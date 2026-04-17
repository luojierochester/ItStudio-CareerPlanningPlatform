"""
使用 sentence-transformers 训练双塔模型。
输入 CSV 文件（train_pairs.csv）格式：resume_text, job_text, label
默认使用正样本（label==1）进行 MultipleNegativesRankingLoss 训练。
"""
import argparse
import pandas as pd
from sentence_transformers import SentenceTransformer, InputExample, losses
from torch.utils.data import DataLoader

def load_positive_pairs(csv_path, max_samples=None):
    df = pd.read_csv(csv_path)
    pos = df[df["label"] == 1].copy()

    if max_samples:
        pos = pos.sample(n=min(max_samples, len(pos)), random_state=42)

    examples = [
        InputExample(texts=[row["resume_text"], row["job_text"]])
        for _, row in pos.iterrows()
    ]
    return examples

def main(args):
    model = SentenceTransformer(args.model_name_or_path)

    train_examples = load_positive_pairs(args.train_csv, args.max_samples)
    train_dataloader = DataLoader(
        train_examples,
        shuffle=True,
        batch_size=args.batch_size
    )

    train_loss = losses.MultipleNegativesRankingLoss(model)

    model.fit(
        train_objectives=[(train_dataloader, train_loss)],
        epochs=args.epochs,
        output_path=args.out_dir,
        show_progress_bar=True
    )

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--train_csv", required=True, help="CSV with resume_text,job_text,label")
    parser.add_argument("--model_name_or_path", default="paraphrase-multilingual-MiniLM-L12-v2")
    parser.add_argument("--out_dir", required=True)
    parser.add_argument("--epochs", type=int, default=2)
    parser.add_argument("--batch_size", type=int, default=32)
    parser.add_argument("--max_samples", type=int, default=None)
    args = parser.parse_args()
    main(args)