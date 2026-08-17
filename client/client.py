import requests
import time
import csv
import os
import random
import argparse
from datetime import datetime

SERVER_URL = "http://127.0.0.1:8000/api/data"

TOTAL_REQUESTS = 50
TIMEOUT_SECONDS = 2

# Retry settings
RETRY_STRATEGY = "no_retry"
MAX_RETRIES = 3
FIXED_RETRY_DELAY = 0.5
BASE_BACKOFF_DELAY = 0.2
MAX_JITTER = 0.3

# Circuit breaker settings
CIRCUIT_BREAKER_ENABLED = False
FAILURE_THRESHOLD = 5
OPEN_DURATION = 10
HALF_OPEN_MAX_TRIALS = 3
HALF_OPEN_SUCCESS_THRESHOLD = 2

LOG_FILE = "../logs/results.csv"


class CircuitBreaker:
    def __init__(self):
        self.state = "CLOSED"
        self.failure_count = 0
        self.opened_time = None
        self.half_open_trials = 0
        self.half_open_successes = 0

    def allow_request(self):
        if not CIRCUIT_BREAKER_ENABLED:
            return True

        if self.state == "CLOSED":
            return True

        if self.state == "OPEN":
            current_time = time.time()

            if current_time - self.opened_time >= OPEN_DURATION:
                self.state = "HALF_OPEN"
                self.half_open_trials = 0
                self.half_open_successes = 0
                print("Circuit breaker changed to HALF_OPEN")
                return True

            return False

        if self.state == "HALF_OPEN":
            if self.half_open_trials < HALF_OPEN_MAX_TRIALS:
                self.half_open_trials += 1
                return True

            return False

        return True

    def record_success(self):
        if not CIRCUIT_BREAKER_ENABLED:
            return

        if self.state == "CLOSED":
            self.failure_count = 0

        elif self.state == "HALF_OPEN":
            self.half_open_successes += 1

            if self.half_open_successes >= HALF_OPEN_SUCCESS_THRESHOLD:
                self.state = "CLOSED"
                self.failure_count = 0
                self.opened_time = None
                self.half_open_trials = 0
                self.half_open_successes = 0
                print("Circuit breaker changed to CLOSED")

    def record_failure(self):
        if not CIRCUIT_BREAKER_ENABLED:
            return

        if self.state == "CLOSED":
            self.failure_count += 1

            if self.failure_count >= FAILURE_THRESHOLD:
                self.state = "OPEN"
                self.opened_time = time.time()
                print("Circuit breaker changed to OPEN")

        elif self.state == "HALF_OPEN":
            self.state = "OPEN"
            self.opened_time = time.time()
            self.half_open_trials = 0
            self.half_open_successes = 0
            print("Circuit breaker changed back to OPEN")


circuit_breaker = CircuitBreaker()


def prepare_log_file():
    os.makedirs("../logs", exist_ok=True)

    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([
                "request_id",
                "timestamp",
                "start_time",
                "end_time",
                "status_code",
                "latency_seconds",
                "result",
                "error_type",
                "retry_count",
                "retry_strategy",
                "circuit_enabled",
                "circuit_state",
                "circuit_rejected"
            ])


def get_retry_delay(attempt):
    if RETRY_STRATEGY == "fixed_retry":
        return FIXED_RETRY_DELAY

    elif RETRY_STRATEGY == "exponential_backoff":
        return BASE_BACKOFF_DELAY * (2 ** (attempt - 1))

    elif RETRY_STRATEGY == "exponential_backoff_jitter":
        exponential_delay = BASE_BACKOFF_DELAY * (2 ** (attempt - 1))
        jitter = random.uniform(0, MAX_JITTER)
        return exponential_delay + jitter

    else:
        return 0


def make_single_request():
    try:
        response = requests.get(SERVER_URL, timeout=TIMEOUT_SECONDS)

        if response.status_code == 200:
            return response.status_code, "SUCCESS", ""
        else:
            return response.status_code, "FAILURE", f"HTTP_{response.status_code}"

    except requests.exceptions.Timeout:
        return None, "TIMEOUT", "TIMEOUT"

    except requests.exceptions.RequestException as e:
        return None, "FAILURE", str(e)


def send_request_with_retry_and_circuit_breaker(request_id):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    start_time = time.time()

    retry_count = 0
    circuit_rejected = False

    # Check circuit breaker before sending request
    if not circuit_breaker.allow_request():
        end_time = time.time()
        latency = end_time - start_time

        result = "CIRCUIT_REJECTED"
        status_code = None
        error_type = "CIRCUIT_OPEN"
        circuit_rejected = True

        log_result(
            request_id,
            timestamp,
            start_time,
            end_time,
            status_code,
            latency,
            result,
            error_type,
            retry_count,
            circuit_rejected
        )

        print(
            f"Request {request_id}: CIRCUIT_REJECTED | "
            f"Circuit State: {circuit_breaker.state}"
        )
        return

    # Send original request
    status_code, result, error_type = make_single_request()

    if result == "SUCCESS":
        circuit_breaker.record_success()
    else:
        circuit_breaker.record_failure()

    # Retry only if request failed or timed out
    if RETRY_STRATEGY != "no_retry":
        while result != "SUCCESS" and retry_count < MAX_RETRIES:
            retry_count += 1

            delay = get_retry_delay(retry_count)
            print(
                f"Request {request_id}: {result}, "
                f"retry {retry_count} after {round(delay, 2)}s"
            )

            time.sleep(delay)

            # Check circuit breaker before retry
            if not circuit_breaker.allow_request():
                result = "CIRCUIT_REJECTED"
                status_code = None
                error_type = "CIRCUIT_OPEN"
                circuit_rejected = True
                break

            status_code, result, error_type = make_single_request()

            if result == "SUCCESS":
                circuit_breaker.record_success()
            else:
                circuit_breaker.record_failure()

    end_time = time.time()
    latency = end_time - start_time

    log_result(
        request_id,
        timestamp,
        start_time,
        end_time,
        status_code,
        latency,
        result,
        error_type,
        retry_count,
        circuit_rejected
    )

    print(
        f"Request {request_id}: {result} | "
        f"Status: {status_code} | "
        f"Retries: {retry_count} | "
        f"Circuit: {circuit_breaker.state} | "
        f"Latency: {round(latency, 4)}s"
    )


def log_result(
    request_id,
    timestamp,
    start_time,
    end_time,
    status_code,
    latency,
    result,
    error_type,
    retry_count,
    circuit_rejected
):
    with open(LOG_FILE, mode="a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([
            request_id,
            timestamp,
            round(start_time, 4),
            round(end_time, 4),
            status_code,
            round(latency, 4),
            result,
            error_type,
            retry_count,
            RETRY_STRATEGY,
            CIRCUIT_BREAKER_ENABLED,
            circuit_breaker.state,
            circuit_rejected
        ])


def run_test():
    prepare_log_file()

    print("Starting client traffic test...")
    print(f"Total requests: {TOTAL_REQUESTS}")
    print(f"Retry strategy: {RETRY_STRATEGY}")
    print(f"Circuit breaker enabled: {CIRCUIT_BREAKER_ENABLED}")
    print("-----------------------------------")

    for request_id in range(1, TOTAL_REQUESTS + 1):
        send_request_with_retry_and_circuit_breaker(request_id)
        time.sleep(0.1)

    print("-----------------------------------")
    print("Test completed.")
    print(f"Results saved to {LOG_FILE}")


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Client traffic generator for reliability experiment"
    )

    parser.add_argument(
        "--requests",
        type=int,
        default=TOTAL_REQUESTS,
        help="Total number of client requests"
    )

    parser.add_argument(
        "--retry",
        type=str,
        default=RETRY_STRATEGY,
        choices=[
            "no_retry",
            "fixed_retry",
            "exponential_backoff",
            "exponential_backoff_jitter"
        ],
        help="Retry strategy"
    )

    parser.add_argument(
        "--circuit",
        type=str,
        default="false",
        choices=["true", "false"],
        help="Enable or disable circuit breaker"
    )

    parser.add_argument(
        "--timeout",
        type=float,
        default=TIMEOUT_SECONDS,
        help="Client timeout in seconds"
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()

    TOTAL_REQUESTS = args.requests
    RETRY_STRATEGY = args.retry
    TIMEOUT_SECONDS = args.timeout
    CIRCUIT_BREAKER_ENABLED = args.circuit.lower() == "true"

    run_test()