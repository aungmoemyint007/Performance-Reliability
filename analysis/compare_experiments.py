import os
import pandas as pd
import matplotlib.pyplot as plt

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXPERIMENTS_DIR = os.path.join(BASE_DIR, "experiments")
OUTPUT_DIR = os.path.join(BASE_DIR, "final_results")

FINAL_COMPARISON_FILE = os.path.join(OUTPUT_DIR, "final_comparison.csv")


SHORT_LABELS = {
    "01_baseline_normal": "Baseline",
    "02_failure_no_protection_30": "Failure Only",
    "03_fixed_retry_30": "Fixed Retry",
    "04_exponential_backoff_30": "Backoff",
    "05_backoff_jitter_30": "Jitter",
    "06_circuit_breaker_only_80": "Circuit Only",
    "07_retry_and_circuit_breaker_80": "Retry + Circuit",
    "08_random_delay_1_5s": "Delay",
    "09_timeout_simulation_3s": "Timeout"
}


def extract_info_value(info_text, label):
    for line in info_text.splitlines():
        if line.startswith(label + ":"):
            return line.split(":", 1)[1].strip()
    return ""


def load_experiment_summaries():
    rows = []

    if not os.path.exists(EXPERIMENTS_DIR):
        print("No experiments folder found.")
        print("Please run experiment_runner.py first.")
        return pd.DataFrame()

    experiment_folders = sorted(os.listdir(EXPERIMENTS_DIR))

    for folder_name in experiment_folders:
        folder_path = os.path.join(EXPERIMENTS_DIR, folder_name)

        if not os.path.isdir(folder_path):
            continue

        summary_file = os.path.join(folder_path, "summary_results.csv")
        info_file = os.path.join(folder_path, "experiment_info.txt")

        if not os.path.exists(summary_file):
            print(f"Skipping {folder_name}: summary_results.csv not found.")
            continue

        summary_df = pd.read_csv(summary_file)

        if summary_df.empty:
            print(f"Skipping {folder_name}: summary file is empty.")
            continue

        row = summary_df.iloc[0].to_dict()
        row["experiment_name"] = folder_name
        row["short_label"] = SHORT_LABELS.get(folder_name, folder_name)

        if os.path.exists(info_file):
            with open(info_file, "r") as file:
                info_text = file.read()

            row["description"] = extract_info_value(info_text, "Description")
            row["failure_mode"] = extract_info_value(info_text, "Failure Mode")
            row["failure_rate"] = extract_info_value(info_text, "Failure Rate")
            row["delay_seconds"] = extract_info_value(info_text, "Delay Seconds")
            row["retry_strategy"] = extract_info_value(info_text, "Retry Strategy")
            row["circuit_breaker"] = extract_info_value(info_text, "Circuit Breaker Enabled")

        rows.append(row)

    df = pd.DataFrame(rows)

    if df.empty:
        return df

    first_columns = [
        "experiment_name",
        "short_label",
        "description",
        "failure_mode",
        "failure_rate",
        "delay_seconds",
        "retry_strategy",
        "circuit_breaker"
    ]

    other_columns = [col for col in df.columns if col not in first_columns]
    df = df[first_columns + other_columns]

    return df


def save_final_comparison(df):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    df.to_csv(FINAL_COMPARISON_FILE, index=False)
    print(f"Final comparison saved to: {FINAL_COMPARISON_FILE}")


def print_comparison_table(df):
    display_columns = [
        "short_label",
        "success_ratio",
        "error_ratio",
        "timeout_ratio",
        "circuit_rejection_ratio",
        "average_latency",
        "p95_latency",
        "p99_latency",
        "throughput_rps",
        "total_retries",
        "retry_success_ratio",
        "request_amplification_ratio"
    ]

    available_columns = [col for col in display_columns if col in df.columns]

    print("===== Final Experiment Comparison =====")
    print(df[available_columns].to_string(index=False))


def add_bar_labels(values):
    for i, value in enumerate(values):
        if value == 0:
            continue
        plt.text(i, value, f"{value:.1f}", ha="center", va="bottom", fontsize=8)


def plot_success_ratio(df):
    labels = df["short_label"]
    values = df["success_ratio"] * 100

    plt.figure(figsize=(11, 5))
    plt.bar(labels, values)
    plt.title("Success Ratio by Experiment")
    plt.xlabel("Experiment")
    plt.ylabel("Success Ratio (%)")
    plt.ylim(0, 100)
    plt.xticks(rotation=30, ha="right")

    for i, value in enumerate(values):
        plt.text(i, value + 1, f"{value:.1f}%", ha="center", fontsize=8)

    plt.tight_layout()
    output_file = os.path.join(OUTPUT_DIR, "success_ratio_by_experiment.png")
    plt.savefig(output_file)
    plt.close()


def plot_failure_ratios(df):
    labels = df["short_label"]

    error_values = df["error_ratio"] * 100
    timeout_values = df["timeout_ratio"] * 100
    circuit_values = df["circuit_rejection_ratio"] * 100

    x = range(len(labels))
    width = 0.25

    plt.figure(figsize=(12, 6))
    plt.bar([i - width for i in x], error_values, width=width, label="Error")
    plt.bar(x, timeout_values, width=width, label="Timeout")
    plt.bar([i + width for i in x], circuit_values, width=width, label="Circuit Rejected")

    plt.title("Failure Ratio Comparison")
    plt.xlabel("Experiment")
    plt.ylabel("Ratio (%)")
    plt.xticks(x, labels, rotation=30, ha="right")
    plt.ylim(0, 100)
    plt.legend()

    plt.tight_layout()
    output_file = os.path.join(OUTPUT_DIR, "failure_ratio_comparison.png")
    plt.savefig(output_file)
    plt.close()


def plot_latency_comparison(df):
    labels = df["short_label"]

    avg_latency = df["average_latency"]
    p95_latency = df["p95_latency"]
    p99_latency = df["p99_latency"]

    x = range(len(labels))
    width = 0.25

    plt.figure(figsize=(12, 6))
    plt.bar([i - width for i in x], avg_latency, width=width, label="Average")
    plt.bar(x, p95_latency, width=width, label="p95")
    plt.bar([i + width for i in x], p99_latency, width=width, label="p99")

    plt.title("Latency Comparison by Experiment")
    plt.xlabel("Experiment")
    plt.ylabel("Latency Seconds")
    plt.xticks(x, labels, rotation=30, ha="right")
    plt.legend()

    plt.tight_layout()
    output_file = os.path.join(OUTPUT_DIR, "latency_comparison.png")
    plt.savefig(output_file)
    plt.close()


def plot_request_amplification(df):
    labels = df["short_label"]
    values = df["request_amplification_ratio"]

    plt.figure(figsize=(11, 5))
    plt.bar(labels, values)

    plt.title("Request Amplification Ratio by Experiment")
    plt.xlabel("Experiment")
    plt.ylabel("Request Amplification Ratio")
    plt.xticks(rotation=30, ha="right")

    for i, value in enumerate(values):
        plt.text(i, value + 0.02, f"{value:.2f}", ha="center", fontsize=8)

    plt.tight_layout()
    output_file = os.path.join(OUTPUT_DIR, "request_amplification_by_experiment.png")
    plt.savefig(output_file)
    plt.close()


def plot_retry_analysis(df):
    labels = df["short_label"]
    retry_values = df["total_retries"]
    retry_success_values = df["retry_successes"]

    x = range(len(labels))
    width = 0.35

    plt.figure(figsize=(12, 6))
    plt.bar([i - width / 2 for i in x], retry_values, width=width, label="Total Retries")
    plt.bar([i + width / 2 for i in x], retry_success_values, width=width, label="Retry Successes")

    plt.title("Retry Count and Retry Success Comparison")
    plt.xlabel("Experiment")
    plt.ylabel("Count")
    plt.xticks(x, labels, rotation=30, ha="right")
    plt.legend()

    plt.tight_layout()
    output_file = os.path.join(OUTPUT_DIR, "retry_count_comparison.png")
    plt.savefig(output_file)
    plt.close()


def generate_comparison_charts(df):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    plot_success_ratio(df)
    plot_failure_ratios(df)
    plot_latency_comparison(df)
    plot_request_amplification(df)
    plot_retry_analysis(df)

    print("Comparison charts generated:")
    print("- success_ratio_by_experiment.png")
    print("- failure_ratio_comparison.png")
    print("- latency_comparison.png")
    print("- request_amplification_by_experiment.png")
    print("- retry_count_comparison.png")


def main():
    df = load_experiment_summaries()

    if df.empty:
        print("No experiment summaries found.")
        return

    save_final_comparison(df)
    print_comparison_table(df)
    generate_comparison_charts(df)


if __name__ == "__main__":
    main()