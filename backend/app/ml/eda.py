"""Generate labelled exploratory charts for synthetic OPD development data only."""
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from app.ml.generate_demo_data import DATA_FILE, write_dataset

OUTPUT_DIR = Path(__file__).parent / "eda"
NOTICE = "Synthetic development data only — not real hospital data"


def build_eda() -> list[Path]:
    if not DATA_FILE.exists():
        write_dataset()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    frame = pd.read_csv(DATA_FILE)
    sns.set_theme(style="whitegrid", palette="deep")
    outputs: list[Path] = []

    fig, axes = plt.subplots(1, 2, figsize=(13, 4.5))
    sns.histplot(frame, x="waiting_time_minutes", bins=36, ax=axes[0], color="#0F8F83")
    axes[0].set_title("Synthetic waiting-time distribution")
    axes[0].set_xlabel("Waiting time (minutes)")
    sns.histplot(frame, x="consultation_duration", bins=28, ax=axes[1], color="#15334A")
    axes[1].set_title("Synthetic consultation-duration distribution")
    axes[1].set_xlabel("Consultation duration (minutes)")
    fig.suptitle(NOTICE, fontsize=10)
    path = OUTPUT_DIR / "distributions.png"
    fig.tight_layout(); fig.savefig(path, dpi=160); plt.close(fig); outputs.append(path)

    sampled = frame.sample(min(800, len(frame)), random_state=42)
    fig, axes = plt.subplots(1, 3, figsize=(17, 4.5))
    sns.regplot(data=sampled, x="patients_ahead", y="waiting_time_minutes", scatter_kws={"alpha": 0.25, "s": 15}, line_kws={"color": "#15334A"}, ax=axes[0])
    axes[0].set_title("Patients ahead vs. waiting time")
    sns.boxplot(data=frame, x="department_code", y="waiting_time_minutes", hue="department_code", legend=False, ax=axes[1])
    axes[1].set_title("Waiting-time variation by department")
    sns.regplot(data=sampled, x="queue_length", y="waiting_time_minutes", scatter_kws={"alpha": 0.22, "s": 15}, line_kws={"color": "#0F8F83"}, ax=axes[2])
    axes[2].set_title("Queue length vs. waiting time")
    fig.suptitle(NOTICE, fontsize=10)
    path = OUTPUT_DIR / "queue_relationships.png"
    fig.tight_layout(); fig.savefig(path, dpi=160); plt.close(fig); outputs.append(path)

    doctor_workload = frame.groupby("doctor_label", as_index=False).agg(records=("waiting_time_minutes", "size"), average_wait_minutes=("waiting_time_minutes", "mean"))
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.5))
    sns.barplot(data=doctor_workload, x="doctor_label", y="records", color="#0F8F83", ax=axes[0])
    axes[0].set_title("Synthetic doctor workload")
    axes[0].tick_params(axis="x", rotation=25)
    sns.regplot(data=sampled, x="consultation_duration", y="waiting_time_minutes", scatter_kws={"alpha": 0.22, "s": 15}, line_kws={"color": "#15334A"}, ax=axes[1])
    axes[1].set_title("Consultation duration vs. waiting time")
    fig.suptitle(NOTICE, fontsize=10)
    path = OUTPUT_DIR / "workload_and_duration_relationships.png"
    fig.tight_layout(); fig.savefig(path, dpi=160); plt.close(fig); outputs.append(path)

    hourly = frame.groupby("hour", as_index=False).size().rename(columns={"size": "patients"})
    fig, ax = plt.subplots(figsize=(8, 4.5))
    sns.lineplot(data=hourly, x="hour", y="patients", marker="o", color="#0F8F83", ax=ax)
    ax.set_title("Synthetic patient arrivals by hour")
    ax.set_xlabel("Hour of day"); ax.set_ylabel("Synthetic records")
    fig.suptitle(NOTICE, fontsize=10)
    path = OUTPUT_DIR / "hourly_load.png"
    fig.tight_layout(); fig.savefig(path, dpi=160); plt.close(fig); outputs.append(path)
    return outputs


if __name__ == "__main__":
    for output in build_eda():
        print(output)
