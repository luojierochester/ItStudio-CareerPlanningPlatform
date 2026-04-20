# -*- coding: utf-8 -*-
import joblib
import numpy as np
import pandas as pd

MODEL_PATH = "models/lgb/lgb_model.joblib"

def load_model():
    data = joblib.load(MODEL_PATH)
    return data["model"], data["feature_names"]

def predict_single(features: dict):
    model, feats = load_model()
    x = np.array([features[f] for f in feats]).reshape(1, -1)
    score = model.predict(x)[0]
    return {
        "match_score": round(float(score), 4),
        "recommend": score >= 0.5,
        "label": "推荐" if score >= 0.5 else "不推荐"
    }

def batch_predict(df_features):
    model, feats = load_model()
    X = df_features[feats]
    scores = model.predict(X)
    df_features["match_score"] = scores
    df_features["recommend"] = scores >= 0.5
    return df_features.sort_values("match_score", ascending=False)

if __name__ == "__main__":
    sample = {
        "sim": 0.88,
        "skill_match": 5,
        "skill_jaccard": 0.75,
        "skill_coverage": 0.7,
        "title_kw_score": 0.8,
        "industry_match": 1.0,
        "has_internship": 1,
        "has_certificate": 1,
        "has_project": 1,
        "has_competition": 1,
        "has_learning_evidence": 1,
        "has_communication_evidence": 1,
        "has_pressure_evidence": 1,
        "job_title_len": 18,
        "job_resp_len": 200,
        "job_content_len": 180,
        "job_req_len": 150,
        "job_full_text_len": 550
    }
    print(predict_single(sample))