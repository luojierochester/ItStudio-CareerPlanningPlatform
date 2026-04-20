# -*- coding: utf-8 -*-
import os
import pandas as pd
import numpy as np
import joblib
import lightgbm as lgb
from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import roc_auc_score, f1_score
import warnings

warnings.filterwarnings("ignore")

SEED = 42
np.random.seed(SEED)

FEATURE_COLS = [
    "sim", "skill_match", "skill_jaccard", "skill_coverage",
    "title_kw_score", "industry_match",
    "has_internship", "has_certificate", "has_project", "has_competition",
    "has_learning_evidence", "has_communication_evidence", "has_pressure_evidence",
    "job_title_len", "job_resp_len", "job_content_len", "job_req_len", "job_full_text_len"
]

LGB_PARAMS = {
    "objective": "binary",
    "metric": "binary_logloss",
    "boosting_type": "gbdt",
    "learning_rate": 0.05,
    "max_depth": 5,
    "num_leaves": 16,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "verbosity": -1,
    "seed": SEED,
}

def train_model():
    print("=" * 60)
    print("🚀 LightGBM 简历-岗位推荐模型 - 优化训练")
    print("=" * 60)

    data_path = "data/features_for_lgb.csv"
    save_path = "models/lgb/lgb_model.joblib"

    if not os.path.exists(data_path):
        raise FileNotFoundError(f"训练数据不存在：{data_path}")

    df = pd.read_csv(data_path)
    print(f"✅ 加载数据：{len(df)} 条")

    # 检查必要字段
    required_cols = FEATURE_COLS + ["label", "query_id"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"数据缺少必要字段：{missing_cols}")

    # 按 query_id 分组切分，避免同一 query 泄漏到训练集和测试集
    gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=SEED)
    train_idx, test_idx = next(gss.split(df, df["label"], groups=df["query_id"]))

    X_train = df.iloc[train_idx][FEATURE_COLS]
    y_train = df.iloc[train_idx]["label"]
    X_test = df.iloc[test_idx][FEATURE_COLS]
    y_test = df.iloc[test_idx]["label"]

    print(f"训练集大小：{len(X_train)}")
    print(f"测试集大小：{len(X_test)}")

    lgb_train = lgb.Dataset(X_train, y_train, feature_name=FEATURE_COLS)
    lgb_val = lgb.Dataset(X_test, y_test, reference=lgb_train, feature_name=FEATURE_COLS)

    model = lgb.train(
        LGB_PARAMS,
        lgb_train,
        num_boost_round=200,
        valid_sets=[lgb_val],
        callbacks=[lgb.log_evaluation(20)]
    )

    y_pred = model.predict(X_test)
    auc = roc_auc_score(y_test, y_pred)
    f1 = f1_score(y_test, (y_pred > 0.5).astype(int))

    print("\n📊 模型效果")
    print(f"AUC: {auc:.4f}")
    print(f"F1: {f1:.4f}")

    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    # 关键修改：保存键名改为 features
    joblib.dump({
        "model": model,
        "features": FEATURE_COLS
    }, save_path)

    print(f"\n🎉 模型保存成功：{save_path}")
    print(f"📌 保存的特征字段数：{len(FEATURE_COLS)}")
    print(f"📌 特征字段：{FEATURE_COLS}")

if __name__ == "__main__":
    train_model()