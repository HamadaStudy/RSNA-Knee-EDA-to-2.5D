import marimo

__generated_with = "0.23.16"
app = marimo.App(width="medium")


@app.cell
def _():
    import pandas as pd
    from pathlib import Path
    import matplotlib.pyplot as plt

    ROOT = Path('/Users/thamada/dev/practice/kaggle/RSNA-Knee-EDA-to-2.5D/')
    OUTPUT_DIR = ROOT / "data/artifacts/00_analysis/count_label_exist"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(ROOT / 'data/mini_dataset/train.csv')

    LABELS = [
        "ACL",
        "MCL",
        "Medial Meniscus",
        "Lateral Meniscus",
        "Medial OA",
        "Lateral OA",
        "PF OA",
        "Effusion",
        "Effusion",
        "Synovitis",
        "Baker's",
        "Contusion",
        "Fracture",
    ]
    return LABELS, OUTPUT_DIR, df, plt


@app.cell
def _(LABELS, OUTPUT_DIR, df, plt):
    # ラベルのないデータを除外する
    df_has_label = df[df['ACL'].notnull()]

    # 各ラベルのカウント
    label_counts = df_has_label[LABELS].sum(axis=0)

    # プロット
    plt.figure(figsize=(12, 5))
    plt.bar(LABELS, label_counts)

    plt.xlabel("Label")
    plt.ylabel("Count")
    plt.title("Label Distribution")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()

    plt.savefig(OUTPUT_DIR / "label_distribution.png")
    return (df_has_label,)


@app.cell
def _(OUTPUT_DIR, df_has_label):
    df_has_label.to_csv(OUTPUT_DIR / "train_label_exist.csv", index=False)
    return


if __name__ == "__main__":
    app.run()
