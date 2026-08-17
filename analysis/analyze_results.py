import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

LOG_FILE = "../logs/results.csv"
SUMMARY_FILE = "../logs/summary_results.csv"
CHART_DIR = "../charts"


def calculate_summary(df):
    total_requests = len(df)

    successful_requests = len(df[df["result"] == "SUCCESS"])
    failed_requests = len(df[df["result"] == "FAILURE"])
    timeout_requests = len(df[df["result"] == "TIMEOUT"])

    if "CIRCUIT_REJECTED" in df["result"].values:
        circuit_rejected_requests = len(df[df["result"] == "CIRCUIT_REJECTED"])
    else:
        circuit_rejected_requests = 0

    success_ratio = successful_requests / total_requests if total_requests > 0 else 0
    error_ratio = failed_requests / total_requests if total_requests > 0 else 0
    timeout_ratio = timeout_requests / total_requests if total_requests > 0 else 0

    circuit_rejection_ratio = (
        circuit_rejected_requests / total_requests
        if total_requests > 0
        else 0
    )

    average_latency = df["latency_seconds"].mean()
    p95_latency = np.percentile(df["latency_seconds"], 95)
    p99_latency = np.percentile(df["latency_seconds"], 99)

    total_time = df["end_time"].max() - df["start_time"].min()
    throughput = total_requests / total_time if total_time > 0 else 0

    total_retries = df["retry_count"].sum() if "retry_count" in df.columns else 0

    original_client_requests = total_requests
    actual_server_requests = total_requests + total_retries

    request_amplification_ratio = (
        actual_server_requests / original_client_requests
        if original_client_requests > 0
        else 0
    )

    retry_successes = 0
    retry_success_ratio = 0

    if "retry_count" in df.columns:
        retry_successes = len(
            df[(df["retry_count"] > 0) & (df["result"] == "SUCCESS")]
        )

        retry_success_ratio = (
            retry_successes / total_retries
            if total_retries > 0
            else 0
        )

    summary = {
        "total_requests": total_requests,
        "successful_requests": successful_requests,
        "failed_requests": failed_requests,
        "timeout_requests": timeout_requests,
        "circuit_rejected_requests": circuit_rejected_requests,

        "success_ratio": round(success_ratio, 4),
        "error_ratio": round(error_ratio, 4),
        "timeout_ratio": round(timeout_ratio, 4),
        "circuit_rejection_ratio": round(circuit_rejection_ratio, 4),

        "average_latency": round(average_latency, 4),
        "p95_latency": round(p95_latency, 4),
        "p99_latency": round(p99_latency, 4),
        "throughput_rps": round(throughput, 4),

        "total_retries": int(total_retries),
        "retry_successes": int(retry_successes),
        "retry_success_ratio": round(retry_success_ratio, 4),
        "request_amplification_ratio": round(request_amplification_ratio, 4)
    }

    return summary


def save_summary(summary):
    summary_df = pd.DataFrame([summary])
    summary_df.to_csv(SUMMARY_FILE, index=False)


def print_summary(summary):
    print("===== Reliability and Performance Summary =====")
    print(f"Total Requests: {summary['total_requests']}")
    print(f"Successful Requests: {summary['successful_requests']}")
    print(f"Failed Requests: {summary['failed_requests']}")
    print(f"Timeout Requests: {summary['timeout_requests']}")
    print(f"Circuit Rejected Requests: {summary['circuit_rejected_requests']}")

    print("----------------------------------------------")
    print(f"Success Ratio: {summary['success_ratio'] * 100:.2f}%")
    print(f"Error Ratio: {summary['error_ratio'] * 100:.2f}%")
    print(f"Timeout Ratio: {summary['timeout_ratio'] * 100:.2f}%")
    print(f"Circuit Rejection Ratio: {summary['circuit_rejection_ratio'] * 100:.2f}%")

    print("----------------------------------------------")
    print(f"Average Latency: {summary['average_latency']:.4f} seconds")
    print(f"p95 Latency: {summary['p95_latency']:.4f} seconds")
    print(f"p99 Latency: {summary['p99_latency']:.4f} seconds")
    print(f"Throughput: {summary['throughput_rps']:.2f} requests/second")

    print("----------------------------------------------")
    print(f"Total Retries: {summary['total_retries']}")
    print(f"Retry Successes: {summary['retry_successes']}")
    print(f"Retry Success Ratio: {summary['retry_success_ratio'] * 100:.2f}%")
    print(f"Request Amplification Ratio: {summary['request_amplification_ratio']:.2f}")


def plot_ratio_chart(summary):
    labels = [
        "Success",
        "Error",
        "Timeout",
        "Circuit Rejected"
    ]

    values = [
        summary["success_ratio"] * 100,
        summary["error_ratio"] * 100,
        summary["timeout_ratio"] * 100,
        summary["circuit_rejection_ratio"] * 100
    ]

    plt.figure(figsize=(9, 5))
    plt.bar(labels, values)
    plt.title("Reliability Ratio Comparison")
    plt.xlabel("Result Type")
    plt.ylabel("Ratio (%)")
    plt.ylim(0, 100)

    for i, value in enumerate(values):
        plt.text(i, value + 1, f"{value:.1f}%", ha="center")

    plt.tight_layout()
    plt.savefig(f"{CHART_DIR}/reliability_ratios.png")
    plt.close()


def plot_latency_chart(summary):
    labels = [
        "Average",
        "p95",
        "p99"
    ]

    values = [
        summary["average_latency"],
        summary["p95_latency"],
        summary["p99_latency"]
    ]

    plt.figure(figsize=(8, 5))
    plt.bar(labels, values)
    plt.title("Latency Analysis")
    plt.xlabel("Latency Metric")
    plt.ylabel("Seconds")

    for i, value in enumerate(values):
        plt.text(i, value + 0.01, f"{value:.4f}s", ha="center")

    plt.tight_layout()
    plt.savefig(f"{CHART_DIR}/latency_analysis.png")
    plt.close()


def plot_retry_chart(summary):
    labels = [
        "Total Retries",
        "Retry Successes"
    ]

    values = [
        summary["total_retries"],
        summary["retry_successes"]
    ]

    plt.figure(figsize=(8, 5))
    plt.bar(labels, values)
    plt.title("Retry Analysis")
    plt.xlabel("Retry Metric")
    plt.ylabel("Count")

    for i, value in enumerate(values):
        plt.text(i, value + 0.5, str(value), ha="center")

    plt.tight_layout()
    plt.savefig(f"{CHART_DIR}/retry_analysis.png")
    plt.close()


def plot_request_amplification_chart(summary):
    labels = [
        "Normal Load",
        "Actual Load"
    ]

    normal_load = 1.0
    actual_load = summary["request_amplification_ratio"]

    values = [
        normal_load,
        actual_load
    ]

    plt.figure(figsize=(8, 5))
    plt.bar(labels, values)
    plt.title("Request Amplification Ratio")
    plt.xlabel("Load Type")
    plt.ylabel("Ratio")

    for i, value in enumerate(values):
        plt.text(i, value + 0.02, f"{value:.2f}", ha="center")

    plt.tight_layout()
    plt.savefig(f"{CHART_DIR}/request_amplification.png")
    plt.close()


def analyze_results():
    os.makedirs(CHART_DIR, exist_ok=True)

    if not os.path.exists(LOG_FILE):
        print("No results.csv file found.")
        print("Please run client.py first.")
        return

    df = pd.read_csv(LOG_FILE)

    if df.empty:
        print("results.csv is empty.")
        return

    required_columns = [
        "request_id",
        "start_time",
        "end_time",
        "latency_seconds",
        "result"
    ]

    for column in required_columns:
        if column not in df.columns:
            print(f"Missing required column: {column}")
            print("Please check your results.csv file.")
            return

    summary = calculate_summary(df)

    save_summary(summary)
    print_summary(summary)

    plot_ratio_chart(summary)
    plot_latency_chart(summary)
    plot_retry_chart(summary)
    plot_request_amplification_chart(summary)

    print("----------------------------------------------")
    print(f"Summary saved to: {SUMMARY_FILE}")
    print(f"Charts saved to: {CHART_DIR}")
    print("Generated charts:")
    print("- reliability_ratios.png")
    print("- latency_analysis.png")
    print("- retry_analysis.png")
    print("- request_amplification.png")


if __name__ == "__main__":
    analyze_results()