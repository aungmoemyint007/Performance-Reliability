import os
import pandas as pd
import matplotlib.pyplot as plt

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXPERIMENTS_DIR = os.path.join(BASE_DIR, "experiments_repeated")
OUTPUT_DIR = os.path.join(BASE_DIR, "final_results_repeated")

FINAL_AVERAGE_FILE = os.path.join(OUTPUT_DIR, "final_average_comparison.csv")


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


def load_repeated_summaries():
    rows = []

    if not os.path.exists(EXPERIMENTS_DIR):
        print("No experiments_repeated folder found.")
        print("Please run experiment_runner_repeated.py first.")
        return pd.DataFrame()

    experiment_folders = sorted(os.listdir(EXPERIMENTS_DIR))

    for experiment_name in experiment_folders:
        experiment_path = os.path.join(EXPERIMENTS_DIR, experiment_name)

        if not os.path.isdir(experiment_path):
            continue

        run_rows = []

        for run_folder in sorted(os.listdir(experiment_path)):
            run_path = os.path.join(experiment_path, run_folder)

            if not os.path.isdir(run_path):
                continue

            summary_file = os.path.join(run_path, "summary_results.csv")

            if not os.path.exists(summary_file):
                print(f"Missing summary: {experiment_name}/{run_folder}")
                continue

            summary_df = pd.read_csv(summary_file)

            if summary_df.empty:
                continue

            row = summary_df.iloc[0].to_dict()
            row["experiment_name"] = experiment_name
            row["short_label"] = SHORT_LABELS.get(experiment_name, experiment_name)
            row["run"] = run_folder
            run_rows.append(row)

        if not run_rows:
            continue

        runs_df = pd.DataFrame(run_rows)

        numeric_columns = runs_df.select_dtypes(include="number").columns
        average_row = runs_df[numeric_columns].mean().to_dict()

        average_row["experiment_name"] = experiment_name
        average_row["short_label"] = SHORT_LABELS.get(experiment_name, experiment_name)
        average_row["number_of_runs"] = len(run_rows)

        rows.append(average_row)

    df = pd.DataFrame(rows)

    if df.empty:
        return df

    first_columns = [
        "experiment_name",
        "short_label",
        "number_of_runs"
    ]

    other_columns = [col for col in df.columns if col not in first_columns]
    df = df[first_columns + other_columns]

    return df


def save_average_comparison(df):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    df.to_csv(FINAL_AVERAGE_FILE, index=False)
    print(f"Average comparison saved to: {FINAL_AVERAGE_FILE}")


def print_average_table(df):
    display_columns = [
        "short_label",
        "number_of_runs",
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

    print("===== Average Experiment Comparison =====")
    print(df[available_columns].to_string(index=False))


def plot_success_ratio(df):
    labels = df["short_label"]
    values = df["success_ratio"] * 100

    plt.figure(figsize=(11, 5))
    plt.bar(labels, values)
    plt.title("Average Success Ratio by Experiment")
    plt.xlabel("Experiment")
    plt.ylabel("Success Ratio (%)")
    plt.ylim(0, 100)
    plt.xticks(rotation=30, ha="right")

    for i, value in enumerate(values):
        plt.text(i, value + 1, f"{value:.1f}%", ha="center", fontsize=8)

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "average_success_ratio.png"))
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

    plt.title("Average Failure Ratio Comparison")
    plt.xlabel("Experiment")
    plt.ylabel("Ratio (%)")
    plt.xticks(x, labels, rotation=30, ha="right")
    plt.ylim(0, 100)
    plt.legend()

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "average_failure_ratios.png"))
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

    plt.title("Average Latency Comparison")
    plt.xlabel("Experiment")
    plt.ylabel("Latency Seconds")
    plt.xticks(x, labels, rotation=30, ha="right")
    plt.legend()

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "average_latency_comparison.png"))
    plt.close()


def plot_request_amplification(df):
    labels = df["short_label"]
    values = df["request_amplification_ratio"]

    plt.figure(figsize=(11, 5))
    plt.bar(labels, values)
    plt.title("Average Request Amplification Ratio")
    plt.xlabel("Experiment")
    plt.ylabel("Request Amplification Ratio")
    plt.xticks(rotation=30, ha="right")

    for i, value in enumerate(values):
        plt.text(i, value + 0.02, f"{value:.2f}", ha="center", fontsize=8)

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "average_request_amplification.png"))
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

    plt.title("Average Retry Count and Retry Success")
    plt.xlabel("Experiment")
    plt.ylabel("Count")
    plt.xticks(x, labels, rotation=30, ha="right")
    plt.legend()

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "average_retry_analysis.png"))
    plt.close()


def generate_average_charts(df):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    plot_success_ratio(df)
    plot_failure_ratios(df)
    plot_latency_comparison(df)
    plot_request_amplification(df)
    plot_retry_analysis(df)

    print("Average comparison charts generated:")
    print("- average_success_ratio.png")
    print("- average_failure_ratios.png")
    print("- average_latency_comparison.png")
    print("- average_request_amplification.png")
    print("- average_retry_analysis.png")


def main():
    df = load_repeated_summaries()

    if df.empty:
        print("No repeated experiment summaries found.")
        return

    save_average_comparison(df)
    print_average_table(df)
    generate_average_charts(df)


if __name__ == "__main__":
    main()