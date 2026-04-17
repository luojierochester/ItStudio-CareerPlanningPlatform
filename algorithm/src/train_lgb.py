"""
Train LightGBM model given features CSV.
Expected:
- binary mode: columns include label + feature columns
- lambdarank mode: columns include label, query_id + feature columns
"""
import argparse
import pandas as pd
import lightgbm as lgb
from sklearn.model_selection import train_test_split
import joblib
import os

def main(args):
    df = pd.read_csv(args.features_csv)
    exclude_cols = {"label", "group", "query_id"}
    features = [c for c in df.columns if c not in exclude_cols]

    X = df[features]
    y = df["label"]

    os.makedirs(args.out_dir, exist_ok=True)

    if args.objective == "lambdarank":
        if "query_id" not in df.columns:
            raise ValueError("query_id column required for lambdarank objective")

        groups = df["query_id"].unique().tolist()
        train_groups, val_groups = train_test_split(groups, test_size=0.2, random_state=42)

        train_idx = df["query_id"].isin(train_groups)
        val_idx = df["query_id"].isin(val_groups)

        X_train = df.loc[train_idx, features]
        y_train = df.loc[train_idx, "label"]
        X_val = df.loc[val_idx, features]
        y_val = df.loc[val_idx, "label"]

        train_group_sizes = df.loc[train_idx].groupby("query_id").size().tolist()
        val_group_sizes = df.loc[val_idx].groupby("query_id").size().tolist()

        dtrain = lgb.Dataset(X_train, label=y_train, group=train_group_sizes)
        dval = lgb.Dataset(X_val, label=y_val, group=val_group_sizes, reference=dtrain)

        params = {
            "objective": "lambdarank",
            "metric": "ndcg",
            "ndcg_eval_at": [1, 3, 5],
            "learning_rate": 0.05,
            "num_leaves": 31,
            "min_data_in_leaf": 20
        }

        bst = lgb.train(
            params,
            dtrain,
            valid_sets=[dval],
            callbacks=[lgb.early_stopping(50)],
            num_boost_round=1000
        )
    else:
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        dtrain = lgb.Dataset(X_train, label=y_train)
        dval = lgb.Dataset(X_val, label=y_val, reference=dtrain)

        params = {
            "objective": "binary",
            "metric": "auc",
            "learning_rate": 0.05,
            "num_leaves": 31
        }

        bst = lgb.train(
            params,
            dtrain,
            valid_sets=[dval],
            callbacks=[lgb.early_stopping(50)],
            num_boost_round=1000
        )

    joblib.dump(
        {"model": bst, "features": features},
        os.path.join(args.out_dir, "lgb_model.joblib")
    )
    print("Saved LightGBM model to", args.out_dir)

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--features_csv", required=True)
    p.add_argument("--out_dir", required=True)
    p.add_argument("--objective", choices=["binary", "lambdarank"], default="binary")
    args = p.parse_args()
    main(args)