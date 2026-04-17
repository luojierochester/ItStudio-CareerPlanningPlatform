"""
大学生场景特征工程（外部特征词典版）：
- 从 features_examples.csv 加载特征关键词
- 弱化/移除工作年限约束
- 强化技能、项目、实习、证书、竞赛、软素质等特征
"""

import os
import json
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# 默认词典路径，可通过环境变量覆盖
DEFAULT_FEATURE_CSV = os.getenv("FEATURE_CSV_PATH", "./data/features_examples.csv")

# 全局缓存，避免重复加载
_FEATURE_KEYWORDS_CACHE = None

def load_feature_keywords(csv_path=None):

    global _FEATURE_KEYWORDS_CACHE

    if _FEATURE_KEYWORDS_CACHE is not None:
        return _FEATURE_KEYWORDS_CACHE

    path = csv_path or DEFAULT_FEATURE_CSV

    if not os.path.exists(path):
        raise FileNotFoundError(
            f"特征关键词文件不存在：{path}\n"
            f"请确保 features_examples.csv 存在，或通过环境变量 FEATURE_CSV_PATH 指定路径。"
        )

    df = pd.read_csv(path, encoding="utf-8")
    df.columns = [c.strip() for c in df.columns]

    if "feature_name" not in df.columns or "keyword" not in df.columns:
        raise ValueError(
            "features_examples.csv 必须包含 'feature_name' 和 'keyword' 两列。"
        )

    result = {}
    for _, row in df.iterrows():
        fname = str(row["feature_name"]).strip()
        kw = str(row["keyword"]).strip()
        if fname not in result:
            result[fname] = []
        result[fname].append(kw)

    _FEATURE_KEYWORDS_CACHE = result
    return result

def reload_feature_keywords(csv_path=None):
    global _FEATURE_KEYWORDS_CACHE
    _FEATURE_KEYWORDS_CACHE = None
    return load_feature_keywords(csv_path)

def _contains_any(text, keywords):
    txt = str(text).lower()
    return int(any(k.lower() in txt for k in keywords))

def extract_skills_from_resume_text(resume_text, feature_keywords=None):
    if feature_keywords is None:
        feature_keywords = load_feature_keywords()

    skill_lexicon = feature_keywords.get("skill", [])
    text = str(resume_text).lower()

    skills = set()
    for kw in skill_lexicon:
        if kw.lower() in text:
            skills.add(kw.lower())

    return skills

def count_skill_matches(resume_skills, job_skill_tokens):
    job_skills = set(str(s).lower() for s in job_skill_tokens)
    return len(resume_skills.intersection(job_skills))

def calc_skill_jaccard(resume_skills, job_skill_tokens):
    job_skills = set(str(s).lower() for s in job_skill_tokens)
    union = resume_skills | job_skills
    if not union:
        return 0.0
    return len(resume_skills & job_skills) / len(union)

def build_features_from_db(
    resume_text,
    resume_vec,
    candidates_meta_rows,
    candidate_vecs,
    candidate_sims=None,
    feature_csv_path=None
):
    resume_text = str(resume_text)

    # 加载特征词典
    feature_keywords = load_feature_keywords(feature_csv_path)

    # 提取简历画像特征
    resume_skills = extract_skills_from_resume_text(resume_text, feature_keywords)

    has_internship = _contains_any(resume_text, feature_keywords.get("has_internship", []))
    has_certificate = _contains_any(resume_text, feature_keywords.get("has_certificate", []))
    has_project = _contains_any(resume_text, feature_keywords.get("has_project", []))
    has_competition = _contains_any(resume_text, feature_keywords.get("has_competition", []))
    has_learning_evidence = _contains_any(resume_text, feature_keywords.get("has_learning_evidence", []))
    has_communication_evidence = _contains_any(resume_text, feature_keywords.get("has_communication_evidence", []))
    has_pressure_evidence = _contains_any(resume_text, feature_keywords.get("has_pressure_evidence", []))

    feats = []
    for i, row in enumerate(candidates_meta_rows):
        job_text_obj = json.loads(row.job_text_json)
        job_skill_tokens = (
            json.loads(row.job_skill_tokens_json)
            if row.job_skill_tokens_json
            else []
        )

        # 相似度
        if candidate_sims is not None:
            sim = float(candidate_sims[i])
        else:
            jvec = candidate_vecs[i:i + 1]
            sim = float(cosine_similarity(resume_vec.reshape(1, -1), jvec)[0, 0])

        skill_match = count_skill_matches(resume_skills, job_skill_tokens)
        skill_jaccard = calc_skill_jaccard(resume_skills, job_skill_tokens)

        feats.append({
            "job_uuid": row.uuid,

            # 语义相似度
            "sim": sim,

            # 技能特征
            "skill_match": skill_match,
            "skill_jaccard": skill_jaccard,

            # 大学生关键背景特征
            "has_internship": has_internship,
            "has_certificate": has_certificate,
            "has_project": has_project,
            "has_competition": has_competition,

            # 软能力线索
            "has_learning_evidence": has_learning_evidence,
            "has_communication_evidence": has_communication_evidence,
            "has_pressure_evidence": has_pressure_evidence,

            # 岗位文本统计
            "job_title_len": len(job_text_obj.get("title", "")),
            "job_desc_len": len(job_text_obj.get("description", "")),
        })

    return pd.DataFrame(feats)