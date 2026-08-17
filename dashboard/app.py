import os
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Use repeated experiment average results
FINAL_RESULTS_DIR = os.path.join(BASE_DIR, "final_results_repeated")
FINAL_COMPARISON_FILE = os.path.join(FINAL_RESULTS_DIR, "final_average_comparison.csv")

st.set_page_config(
    page_title="Reliability Ratio Dashboard",
    page_icon="📊",
    layout="wide"
)


def load_data():
    if not os.path.exists(FINAL_COMPARISON_FILE):
        return None

    df = pd.read_csv(FINAL_COMPARISON_FILE)
    return df


def percent_format(value):
    return f"{value * 100:.2f}%"


def show_metric_cards(df):
    best_success = df.loc[df["success_ratio"].idxmax()]
    lowest_error = df.loc[df["error_ratio"].idxmin()]
    highest_amplification = df.loc[df["request_amplification_ratio"].idxmax()]
    highest_latency = df.loc[df["p99_latency"].idxmax()]

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Best Avg Success Ratio",
        percent_format(best_success["success_ratio"]),
        best_success["short_label"]
    )

    col2.metric(
        "Lowest Avg Error Ratio",
        percent_format(lowest_error["error_ratio"]),
        lowest_error["short_label"]
    )

    col3.metric(
        "Highest Request Amplification",
        f"{highest_amplification['request_amplification_ratio']:.2f}",
        highest_amplification["short_label"]
    )

    col4.metric(
        "Highest p99 Latency",
        f"{highest_latency['p99_latency']:.4f}s",
        highest_latency["short_label"]
    )


def plot_success_ratio(df):
    fig, ax = plt.subplots(figsize=(10, 5))
    values = df["success_ratio"] * 100

    ax.bar(df["short_label"], values)
    ax.set_title("Average Success Ratio by Experiment")
    ax.set_xlabel("Experiment")
    ax.set_ylabel("Success Ratio (%)")
    ax.set_ylim(0, 100)

    for i, value in enumerate(values):
        ax.text(i, value + 1, f"{value:.1f}%", ha="center", fontsize=8)

    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    st.pyplot(fig)


def plot_failure_ratios(df):
    fig, ax = plt.subplots(figsize=(10, 5))

    x = range(len(df))
    width = 0.25

    ax.bar(
        [i - width for i in x],
        df["error_ratio"] * 100,
        width=width,
        label="Error"
    )

    ax.bar(
        x,
        df["timeout_ratio"] * 100,
        width=width,
        label="Timeout"
    )

    ax.bar(
        [i + width for i in x],
        df["circuit_rejection_ratio"] * 100,
        width=width,
        label="Circuit Rejected"
    )

    ax.set_title("Average Failure Ratio Comparison")
    ax.set_xlabel("Experiment")
    ax.set_ylabel("Ratio (%)")
    ax.set_xticks(list(x))
    ax.set_xticklabels(df["short_label"], rotation=30, ha="right")
    ax.set_ylim(0, 100)
    ax.legend()

    plt.tight_layout()
    st.pyplot(fig)


def plot_latency(df):
    fig, ax = plt.subplots(figsize=(10, 5))

    x = range(len(df))
    width = 0.25

    ax.bar(
        [i - width for i in x],
        df["average_latency"],
        width=width,
        label="Average"
    )

    ax.bar(
        x,
        df["p95_latency"],
        width=width,
        label="p95"
    )

    ax.bar(
        [i + width for i in x],
        df["p99_latency"],
        width=width,
        label="p99"
    )

    ax.set_title("Average Latency Comparison")
    ax.set_xlabel("Experiment")
    ax.set_ylabel("Latency Seconds")
    ax.set_xticks(list(x))
    ax.set_xticklabels(df["short_label"], rotation=30, ha="right")
    ax.legend()

    plt.tight_layout()
    st.pyplot(fig)


def plot_request_amplification(df):
    fig, ax = plt.subplots(figsize=(10, 5))

    values = df["request_amplification_ratio"]

    ax.bar(df["short_label"], values)
    ax.set_title("Average Request Amplification Ratio")
    ax.set_xlabel("Experiment")
    ax.set_ylabel("Amplification Ratio")

    for i, value in enumerate(values):
        ax.text(i, value + 0.02, f"{value:.2f}", ha="center", fontsize=8)

    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    st.pyplot(fig)


def plot_retry_analysis(df):
    fig, ax = plt.subplots(figsize=(10, 5))

    x = range(len(df))
    width = 0.35

    ax.bar(
        [i - width / 2 for i in x],
        df["total_retries"],
        width=width,
        label="Total Retries"
    )

    ax.bar(
        [i + width / 2 for i in x],
        df["retry_successes"],
        width=width,
        label="Retry Successes"
    )

    ax.set_title("Average Retry Count and Retry Success")
    ax.set_xlabel("Experiment")
    ax.set_ylabel("Count")
    ax.set_xticks(list(x))
    ax.set_xticklabels(df["short_label"], rotation=30, ha="right")
    ax.legend()

    plt.tight_layout()
    st.pyplot(fig)


def plot_throughput(df):
    fig, ax = plt.subplots(figsize=(10, 5))

    values = df["throughput_rps"]

    ax.bar(df["short_label"], values)
    ax.set_title("Average Throughput by Experiment")
    ax.set_xlabel("Experiment")
    ax.set_ylabel("Requests per Second")

    for i, value in enumerate(values):
        ax.text(i, value + 0.05, f"{value:.2f}", ha="center", fontsize=8)

    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    st.pyplot(fig)


def show_interpretation():
    st.subheader("Interpretation Guide")

    st.write(
        """
        - **Success ratio** shows how often the client receives a successful response.
        - **Error ratio** shows how often the server returns failure responses.
        - **Timeout ratio** shows how often the client waits too long.
        - **Circuit rejection ratio** shows how often the circuit breaker blocks requests.
        - **Request amplification ratio** shows how much extra load retries create.
        - **p95 and p99 latency** show slow-request behavior better than average latency alone.
        - **Throughput** shows how many requests are completed per second.
        """
    )


def show_conclusion_helper(df):
    st.subheader("Automatic Result Notes")

    baseline = df[df["short_label"] == "Baseline"]
    failure_only = df[df["short_label"] == "Failure Only"]
    fixed_retry = df[df["short_label"] == "Fixed Retry"]
    jitter = df[df["short_label"] == "Jitter"]
    circuit_only = df[df["short_label"] == "Circuit Only"]
    retry_circuit = df[df["short_label"] == "Retry + Circuit"]

    if not baseline.empty:
        st.write(
            f"- Baseline achieved an average success ratio of "
            f"**{percent_format(baseline.iloc[0]['success_ratio'])}**."
        )

    if not failure_only.empty:
        st.write(
            f"- Under 30% random failure without protection, success ratio became "
            f"**{percent_format(failure_only.iloc[0]['success_ratio'])}**."
        )

    if not fixed_retry.empty:
        st.write(
            f"- Fixed retry produced request amplification of "
            f"**{fixed_retry.iloc[0]['request_amplification_ratio']:.2f}**, "
            f"showing extra server load from retries."
        )

    if not jitter.empty:
        st.write(
            f"- Exponential backoff with jitter achieved success ratio "
            f"**{percent_format(jitter.iloc[0]['success_ratio'])}** "
            f"with request amplification "
            f"**{jitter.iloc[0]['request_amplification_ratio']:.2f}**."
        )

    if not circuit_only.empty:
        st.write(
            f"- Circuit breaker only rejected "
            f"**{percent_format(circuit_only.iloc[0]['circuit_rejection_ratio'])}** "
            f"of requests during severe failure."
        )

    if not retry_circuit.empty:
        st.write(
            f"- Retry with circuit breaker produced success ratio "
            f"**{percent_format(retry_circuit.iloc[0]['success_ratio'])}** "
            f"and circuit rejection ratio "
            f"**{percent_format(retry_circuit.iloc[0]['circuit_rejection_ratio'])}**."
        )


def main():
    st.title("Reliability Ratio Dashboard")
    st.write(
        "This dashboard shows averaged results from repeated experiments. "
        "Each experiment is repeated three times, and the average values are used "
        "for comparison."
    )

    df = load_data()

    if df is None:
        st.error("final_average_comparison.csv not found.")
        st.write("Please run these commands first:")
        st.code(
            """
cd reliability_dashboard_project
python experiment_runner_repeated.py

cd analysis
python compare_repeated_experiments.py
            """
        )
        return

    show_metric_cards(df)

    st.divider()

    st.subheader("Average Final Comparison Table")

    selected_columns = [
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
        "retry_successes",
        "retry_success_ratio",
        "request_amplification_ratio"
    ]

    available_columns = [col for col in selected_columns if col in df.columns]

    st.dataframe(
        df[available_columns],
        use_container_width=True
    )

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Average Success Ratio")
        plot_success_ratio(df)

    with col2:
        st.subheader("Average Failure Ratios")
        plot_failure_ratios(df)

    st.divider()

    col3, col4 = st.columns(2)

    with col3:
        st.subheader("Average Latency")
        plot_latency(df)

    with col4:
        st.subheader("Average Throughput")
        plot_throughput(df)

    st.divider()

    col5, col6 = st.columns(2)

    with col5:
        st.subheader("Request Amplification")
        plot_request_amplification(df)

    with col6:
        st.subheader("Retry Analysis")
        plot_retry_analysis(df)

    st.divider()

    show_interpretation()

    st.divider()

    show_conclusion_helper(df)


if __name__ == "__main__":
    main()
    