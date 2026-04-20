"""
从已有简历样本生成 LightGBM 训练数据
需要准备：
  1. resumes.csv：包含 resume_id, resume_text 列
  2. labels.csv：包含 resume_id, job_id, label（1=匹配，0=不匹配）
"""
import os
import sys

# 添加 src 目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

import argparse
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import sessionmaker
from db_models import get_engine, Job
from feature_engineering_db import build_features_from_db
import json

def main(args):
    # 加载模型和数据库
    model = SentenceTransformer(args.model_path)
    engine = get_engine(args.db_uri)
    Session = sessionmaker(bind=engine)
    session = Session()
    all_jobs = session.query(Job).all()
    session.close()

    # 构建 job_id -> Job 映射
    job_map = {j.job_id: j for j in all_jobs if j.job_id}
    
    # 加载简历和标签
    resumes_df = pd.read_csv(args.resumes_csv)
    labels_df = pd.read_csv(args.labels_csv)

    # 合并
    data = labels_df.merge(resumes_df, on="resume_id", how="left")
    
    all_features = []
    
    for resume_id, group in data.groupby("resume_id"):
        resume_text = group.iloc[0]["resume_text"]
        
        # 编码简历
        resume_vec = model.encode([resume_text], normalize_embeddings=True)[0]
        
        # 获取该简历对应的所有候选岗位
        candidate_jobs = []
        candidate_vecs = []
        candidate_labels = []
        
        for _, row in group.iterrows():
            job_id = row["job_id"]
            label = int(row["label"])
            
            if job_id not in job_map:
                continue
                
            job_obj = job_map[job_id]
            job_vec = np.array(json.loads(job_obj.job_vector_json), dtype=np.float32)
            
            candidate_jobs.append(job_obj)
            candidate_vecs.append(job_vec)
            candidate_labels.append(label)
        
        if not candidate_jobs:
            continue
        
        # 提取特征
        feats_df = build_features_from_db(
            resume_text=resume_text,
            resume_vec=resume_vec,
            candidates_meta_rows=candidate_jobs,
            candidate_vecs=np.vstack(candidate_vecs)
        )
        
        # 添加 query_id 和 label
        feats_df["query_id"] = resume_id
        feats_df["label"] = candidate_labels
        
        all_features.append(feats_df)
    
    # 合并所有特征
    final_df = pd.concat(all_features, ignore_index=True)
    
    # 移除不需要的列
    final_df = final_df.drop(columns=["job_uuid"], errors="ignore")
    
    # 保存
    final_df.to_csv(args.output_csv, index=False)
    print(f"✅ 生成训练数据：{args.output_csv}")
    print(f"   总样本数：{len(final_df)}")
    print(f"   正样本数：{final_df['label'].sum()}")
    print(f"   负样本数：{len(final_df) - final_df['label'].sum()}")
    print(f"   特征列：{[c for c in final_df.columns if c not in ['query_id', 'label']]}")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--resumes_csv", default="data/resumes.csv", help="简历数据，包含 resume_id, resume_text")
    p.add_argument("--labels_csv", default="data/labels.csv", help="标签数据，包含 resume_id, job_id, label")
    p.add_argument("--model_path", default="./model")
    p.add_argument("--db_uri", default="sqlite:///jobs.db")
    p.add_argument("--output_csv", default="data/features_for_lgb.csv")
    args = p.parse_args()
    main(args)