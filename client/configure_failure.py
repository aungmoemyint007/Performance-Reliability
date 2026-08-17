import requests

BASE_URL = "http://127.0.0.1:8000"


def reset_failure():
    response = requests.post(f"{BASE_URL}/config/reset")
    print(response.json())


def set_random_error(failure_rate):
    response = requests.post(
        f"{BASE_URL}/config/failure",
        params={
            "random_error": True,
            "failure_rate": failure_rate
        }
    )
    print(response.json())


def set_random_delay(delay_seconds):
    response = requests.post(
        f"{BASE_URL}/config/failure",
        params={
            "random_delay": True,
            "delay_seconds": delay_seconds
        }
    )
    print(response.json())


def set_timeout_simulation(delay_seconds):
    response = requests.post(
        f"{BASE_URL}/config/failure",
        params={
            "timeout_simulation": True,
            "delay_seconds": delay_seconds
        }
    )
    print(response.json())


if __name__ == "__main__":
    print("Choose failure mode:")
    print("1. Reset failure mode")
    print("2. Random HTTP 500 error")
    print("3. Random delay")
    print("4. Timeout simulation")

    choice = input("Enter choice: ")

    if choice == "1":
        reset_failure()

    elif choice == "2":
        rate = float(input("Enter failure rate, example 0.3 for 30%: "))
        set_random_error(rate)

    elif choice == "3":
        delay = float(input("Enter maximum random delay in seconds: "))
        set_random_delay(delay)

    elif choice == "4":
        delay = float(input("Enter timeout delay in seconds: "))
        set_timeout_simulation(delay)

    else:
        print("Invalid choice")