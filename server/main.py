from fastapi import FastAPI, HTTPException
import time
import random

app = FastAPI()

# Failure injection settings
FAILURE_MODE = {
    "random_error": False,
    "random_delay": False,
    "timeout_simulation": False,
    "failure_rate": 0.0,
    "delay_seconds": 0.0
}


@app.get("/")
def home():
    return {
        "message": "Reliability Analysis API Server is running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "failure_mode": FAILURE_MODE
    }


@app.get("/api/data")
def get_data():
    # 1. Random HTTP 500 error
    if FAILURE_MODE["random_error"]:
        if random.random() < FAILURE_MODE["failure_rate"]:
            raise HTTPException(
                status_code=500,
                detail="Simulated internal server error"
            )

    # 2. Random delay
    if FAILURE_MODE["random_delay"]:
        delay = random.uniform(0, FAILURE_MODE["delay_seconds"])
        time.sleep(delay)

    # 3. Timeout simulation
    if FAILURE_MODE["timeout_simulation"]:
        time.sleep(FAILURE_MODE["delay_seconds"])

    return {
        "status": "success",
        "data": "Sample response from server"
    }


@app.post("/config/failure")
def configure_failure(
    random_error: bool = False,
    random_delay: bool = False,
    timeout_simulation: bool = False,
    failure_rate: float = 0.0,
    delay_seconds: float = 0.0
):
    FAILURE_MODE["random_error"] = random_error
    FAILURE_MODE["random_delay"] = random_delay
    FAILURE_MODE["timeout_simulation"] = timeout_simulation
    FAILURE_MODE["failure_rate"] = failure_rate
    FAILURE_MODE["delay_seconds"] = delay_seconds

    return {
        "message": "Failure mode updated",
        "failure_mode": FAILURE_MODE
    }


@app.post("/config/reset")
def reset_failure():
    FAILURE_MODE["random_error"] = False
    FAILURE_MODE["random_delay"] = False
    FAILURE_MODE["timeout_simulation"] = False
    FAILURE_MODE["failure_rate"] = 0.0
    FAILURE_MODE["delay_seconds"] = 0.0

    return {
        "message": "Failure mode reset",
        "failure_mode": FAILURE_MODE
    }