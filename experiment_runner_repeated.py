import os
import shutil
import subprocess
import time
import requests
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CLIENT_DIR = os.path.join(BASE_DIR, "client")
ANALYSIS_DIR = os.path.join(BASE_DIR, "analysis")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
CHARTS_DIR = os.path.join(BASE_DIR, "charts")
EXPERIMENTS_DIR = os.path.join(BASE_DIR, "experiments_repeated")

SERVER_BASE_URL = "http://127.0.0.1:8000"

TOTAL_REQUESTS = 50
RUNS_PER_EXPERIMENT = 3


EXPERIMENTS = [
    {
        "name": "01_baseline_normal",
        "failure_mode": "reset",
        "failure_rate": 0.0,
        "delay_seconds": 0.0,
        "retry": "no_retry",
        "circuit": "false",
        "description": "Normal server without failures, retry, or circuit breaker"
    },
    {
        "name": "02_failure_no_protection_30",
        "failure_mode": "random_error",
        "failure_rate": 0.3,
        "delay_seconds": 0.0,
        "retry": "no_retry",
        "circuit": "false",
        "description": "30% random server error without protection"
    },
    {
        "name": "03_fixed_retry_30",
        "failure_mode": "random_error",
        "failure_rate": 0.3,
        "delay_seconds": 0.0,
        "retry": "fixed_retry",
        "circuit": "false",
        "description": "30% random server error with fixed retry"
    },
    {
        "name": "04_exponential_backoff_30",
        "failure_mode": "random_error",
        "failure_rate": 0.3,
        "delay_seconds": 0.0,
        "retry": "exponential_backoff",
        "circuit": "false",
        "description": "30% random server error with exponential backoff"
    },
    {
        "name": "05_backoff_jitter_30",
        "failure_mode": "random_error",
        "failure_rate": 0.3,
        "delay_seconds": 0.0,
        "retry": "exponential_backoff_jitter",
        "circuit": "false",
        "description": "30% random server error with exponential backoff and jitter"
    },
    {
        "name": "06_circuit_breaker_only_80",
        "failure_mode": "random_error",
        "failure_rate": 0.8,
        "delay_seconds": 0.0,
        "retry": "no_retry",
        "circuit": "true",
        "description": "80% random server error with circuit breaker only"
    },
    {
        "name": "07_retry_and_circuit_breaker_80",
        "failure_mode": "random_error",
        "failure_rate": 0.8,
        "delay_seconds": 0.0,
        "retry": "exponential_backoff_jitter",
        "circuit": "true",
        "description": "80% random server error with retry and circuit breaker"
    },
    {
        "name": "08_random_delay_1_5s",
        "failure_mode": "random_delay",
        "failure_rate": 0.0,
        "delay_seconds": 1.5,
        "retry": "no_retry",
        "circuit": "false",
        "description": "Random delay up to 1.5 seconds without retry or circuit breaker"
    },
    {
        "name": "09_timeout_simulation_3s",
        "failure_mode": "timeout_simulation",
        "failure_rate": 0.0,
        "delay_seconds": 3.0,
        "retry": "no_retry",
        "circuit": "false",
        "description": "Server delay 3 seconds with client timeout 2 seconds"
    }
]


def check_server_running():
    try:
        response = requests.get(f"{SERVER_BASE_URL}/health", timeout=3)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


def reset_server_failure():
    response = requests.post(f"{SERVER_BASE_URL}/config/reset", timeout=5)
    response.raise_for_status()


def configure_server_failure(experiment):
    failure_mode = experiment["failure_mode"]

    if failure_mode == "reset":
        reset_server_failure()
        return

    params = {
        "random_error": False,
        "random_delay": False,
        "timeout_simulation": False,
        "failure_rate": experiment["failure_rate"],
        "delay_seconds": experiment["delay_seconds"]
    }

    if failure_mode == "random_error":
        params["random_error"] = True

    elif failure_mode == "random_delay":
        params["random_delay"] = True

    elif failure_mode == "timeout_simulation":
        params["timeout_simulation"] = True

    else:
        raise ValueError(f"Unknown failure mode: {failure_mode}")

    response = requests.post(
        f"{SERVER_BASE_URL}/config/failure",
        params=params,
        timeout=5
    )
    response.raise_for_status()


def remove_old_outputs():
    results_file = os.path.join(LOGS_DIR, "results.csv")
    summary_file = os.path.join(LOGS_DIR, "summary_results.csv")

    if os.path.exists(results_file):
        os.remove(results_file)

    if os.path.exists(summary_file):
        os.remove(summary_file)

    chart_files = [
        "reliability_ratios.png",
        "latency_analysis.png",
        "retry_analysis.png",
        "request_amplification.png"
    ]

    for chart_file in chart_files:
        path = os.path.join(CHARTS_DIR, chart_file)
        if os.path.exists(path):
            os.remove(path)


def run_client_experiment(experiment):
    command = [
        "python",
        "client.py",
        "--requests",
        str(TOTAL_REQUESTS),
        "--retry",
        experiment["retry"],
        "--circuit",
        experiment["circuit"],
        "--timeout",
        "2"
    ]

    subprocess.run(
        command,
        cwd=CLIENT_DIR,
        check=True
    )


def run_analysis():
    command = [
        "python",
        "analyze_results.py"
    ]

    subprocess.run(
        command,
        cwd=ANALYSIS_DIR,
        check=True
    )


def save_run_outputs(experiment, run_number):
    experiment_name = experiment["name"]

    output_dir = os.path.join(
        EXPERIMENTS_DIR,
        experiment_name,
        f"run_{run_number}"
    )

    os.makedirs(output_dir, exist_ok=True)

    files_to_copy = [
        (os.path.join(LOGS_DIR, "results.csv"), "results.csv"),
        (os.path.join(LOGS_DIR, "summary_results.csv"), "summary_results.csv"),
        (os.path.join(CHARTS_DIR, "reliability_ratios.png"), "reliability_ratios.png"),
        (os.path.join(CHARTS_DIR, "latency_analysis.png"), "latency_analysis.png"),
        (os.path.join(CHARTS_DIR, "retry_analysis.png"), "retry_analysis.png"),
        (os.path.join(CHARTS_DIR, "request_amplification.png"), "request_amplification.png")
    ]

    for source, destination_name in files_to_copy:
        if os.path.exists(source):
            destination = os.path.join(output_dir, destination_name)
            shutil.copy(source, destination)

    description_file = os.path.join(output_dir, "experiment_info.txt")

    with open(description_file, "w") as file:
        file.write(f"Experiment Name: {experiment['name']}\n")
        file.write(f"Description: {experiment['description']}\n")
        file.write(f"Failure Mode: {experiment['failure_mode']}\n")
        file.write(f"Failure Rate: {experiment['failure_rate']}\n")
        file.write(f"Delay Seconds: {experiment['delay_seconds']}\n")
        file.write(f"Retry Strategy: {experiment['retry']}\n")
        file.write(f"Circuit Breaker Enabled: {experiment['circuit']}\n")
        file.write(f"Total Requests: {TOTAL_REQUESTS}\n")
        file.write(f"Run Number: {run_number}\n")
        file.write(f"Run Time: {datetime.now()}\n")


def run_all_experiments():
    os.makedirs(LOGS_DIR, exist_ok=True)
    os.makedirs(CHARTS_DIR, exist_ok=True)
    os.makedirs(EXPERIMENTS_DIR, exist_ok=True)

    if not check_server_running():
        print("ERROR: Server is not running.")
        print("Please start the FastAPI server first:")
        print("cd reliability_dashboard_project/server")
        print("uvicorn main:app --reload")
        return

    print("Server is running.")
    print("Starting repeated automatic experiments...")
    print(f"Runs per experiment: {RUNS_PER_EXPERIMENT}")
    print("========================================")

    for experiment in EXPERIMENTS:
        print(f"Experiment: {experiment['name']}")
        print(f"Description: {experiment['description']}")

        for run_number in range(1, RUNS_PER_EXPERIMENT + 1):
            print(f"Starting run {run_number}/{RUNS_PER_EXPERIMENT}")

            remove_old_outputs()
            configure_server_failure(experiment)

            time.sleep(1)

            run_client_experiment(experiment)
            run_analysis()
            save_run_outputs(experiment, run_number)

            print(f"Finished run {run_number}/{RUNS_PER_EXPERIMENT}")
            print("----------------------------------------")

        print(f"Finished experiment: {experiment['name']}")
        print("========================================")

    reset_server_failure()

    print("All repeated experiments completed.")
    print(f"Results saved in: {EXPERIMENTS_DIR}")


if __name__ == "__main__":
    run_all_experiments()