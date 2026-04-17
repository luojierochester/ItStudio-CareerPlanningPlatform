"""
大学生版端到端推理：
1. 使用 DB 存储岗位
2. 优先 FAISS 召回，无索引时回退内存余弦检索
3. 使用大学生特征进行精排
4. 输出更适合职业规划场景的解释结果
"""

import argparse
import json
import os
import numpy as np
import joblib

from sqlalchemy.orm import sessionmaker
from db_models import get_engine, Job
from sentence_transformers import SentenceTransformer
from feature_engineering_db import (
    build_features_from_db,
    extract_skills_from_resume_text
)
from sklearn.metrics.pairwise import cosine_similarity

class RecommendationEngine:
    def __init__(self, model_path, db_uri, lgb_model_path=None, faiss_index_path=None):
        self.model_path = model_path
        self.db_uri = db_uri
        self.lgb_model_path = lgb_model_path
        self.faiss_index_path = faiss_index_path

        self.model = None
        self.rows = []
        self.job_vectors = None
        self.row_map = {}
        self.uuid_to_index = {}
        self.lgb_model = None
        self.feature_list = None
        self.faiss_index = None

    def load(self):
        self._load_model()
        self._load_jobs()
        self._load_lgb_model()
        self._load_faiss_index()

    def _load_model(self):
        self.model = SentenceTransformer(self.model_path)

    def _load_jobs(self):
        engine = get_engine(self.db_uri)
        Session = sessionmaker(bind=engine)
        session = Session()
        self.rows = session.query(Job).all()
        session.close()

        if not self.rows:
            raise ValueError("No jobs found in DB.")

        vecs = []
        dim = self.model.get_sentence_embedding_dimension()

        for idx, r in enumerate(self.rows):
            if r.job_vector_json:
                vec = np.array(json.loads(r.job_vector_json), dtype=np.float32)
            else:
                vec = np.zeros((dim,), dtype=np.float32)

            vecs.append(vec)
            self.row_map[r.uuid] = r
            self.uuid_to_index[r.uuid] = idx

        self.job_vectors = np.vstack(vecs).astype(np.float32)

    def _load_lgb_model(self):
        if self.lgb_model_path and os.path.exists(self.lgb_model_path):
            obj = joblib.load(self.lgb_model_path)
            self.lgb_model = obj["model"]
            self.feature_list = obj["features"]

    def _load_faiss_index(self):
        if self.faiss_index_path and os.path.exists(self.faiss_index_path):
            import faiss
            self.faiss_index = faiss.read_index(self.faiss_index_path)

    def recall(self, resume_vec, topk=100):
        """
        优先使用 FAISS；否则回退到内存 cosine 检索
        """
        resume_vec = resume_vec.astype(np.float32).reshape(1, -1)

        if self.faiss_index is not None:
            scores, indices = self.faiss_index.search(resume_vec, topk)
            idxs = indices[0]
            sims = scores[0]
            valid = [(i, s) for i, s in zip(idxs, sims) if i >= 0]
            if not valid:
                return np.array([], dtype=int), np.array([], dtype=float)
            idxs = np.array([x[0] for x in valid], dtype=int)
            sims = np.array([x[1] for x in valid], dtype=float)
            return idxs, sims

        sims = cosine_similarity(resume_vec, self.job_vectors)[0]
        idx = np.argsort(-sims)[:topk]
        return idx, sims[idx]

    def rerank(self, resume_text, resume_vec, candidate_rows, candidate_vecs, candidate_sims=None):
        feats_df = build_features_from_db(
            resume_text=resume_text,
            resume_vec=resume_vec,
            candidates_meta_rows=candidate_rows,
            candidate_vecs=candidate_vecs,
            candidate_sims=candidate_sims
        )

        if self.lgb_model is not None and self.feature_list is not None:
            # 保证特征列存在
            for col in self.feature_list:
                if col not in feats_df.columns:
                    feats_df[col] = 0
            X = feats_df[self.feature_list].fillna(0)
            feats_df["rank_score"] = self.lgb_model.predict(X)
            feats_df = feats_df.sort_values("rank_score", ascending=False)
        else:
            # 无 LGB 时采用更适合大学生场景的简单打分
            feats_df["rank_score"] = (
                feats_df["sim"] * 0.55 +
                feats_df["skill_jaccard"] * 0.20 +
                (feats_df["skill_match"] > 0).astype(float) * 0.10 +
                feats_df.get("has_project", 0) * 0.05 +
                feats_df.get("has_internship", 0) * 0.05 +
                feats_df.get("has_certificate", 0) * 0.03 +
                feats_df.get("has_competition", 0) * 0.02
            )
            feats_df = feats_df.sort_values("rank_score", ascending=False)

        return feats_df

    def _build_explanation(self, resume_text, row_meta, feat_row):
        """
        更适合大学生职业规划场景的解释结果
        """
        resume_skills = extract_skills_from_resume_text(resume_text)
        job_skills = json.loads(row_meta.job_skill_tokens_json) if row_meta.job_skill_tokens_json else []
        job_skill_set = set(str(s).lower() for s in job_skills)
        matched_skills = list(resume_skills & job_skill_set)[:5]
        missing_skills = list(job_skill_set - resume_skills)[:5]

        reasons = []
        strengths = []
        suggestions = []

        sim = float(feat_row.get("sim", 0))
        skill_match = int(feat_row.get("skill_match", 0))
        has_project = int(feat_row.get("has_project", 0))
        has_internship = int(feat_row.get("has_internship", 0))
        has_certificate = int(feat_row.get("has_certificate", 0))
        has_competition = int(feat_row.get("has_competition", 0))
        has_learning = int(feat_row.get("has_learning_evidence", 0))
        has_communication = int(feat_row.get("has_communication_evidence", 0))
        has_pressure = int(feat_row.get("has_pressure_evidence", 0))

        # 推荐原因
        if sim > 0.6:
            reasons.append("简历与岗位语义相似度较高")
        elif sim > 0.45:
            reasons.append("简历与岗位具备一定语义相关性")

        if skill_match > 0:
            reasons.append(f"匹配到 {skill_match} 个岗位技能关键词")

        if has_project == 1:
            reasons.append("简历中包含项目经历")
        if has_internship == 1:
            reasons.append("简历中包含实习经历")
        if has_certificate == 1:
            reasons.append("简历中包含证书/认证信息")
        if has_competition == 1:
            reasons.append("简历中包含竞赛或创新经历")

        # 优势
        if skill_match >= 3:
            strengths.append("专业技能匹配度较高")
        elif skill_match >= 1:
            strengths.append("具备部分岗位所需技能基础")

        if has_project == 1:
            strengths.append("具备项目实践基础")
        if has_internship == 1:
            strengths.append("具备一定实习实践经历")
        if has_learning == 1:
            strengths.append("简历体现出较强学习能力")
        if has_communication == 1:
            strengths.append("简历体现出沟通协作能力")
        if has_pressure == 1:
            strengths.append("简历体现出一定抗压能力")

        # 建议
        if missing_skills:
            suggestions.append(f"建议优先补充岗位相关技能：{'、'.join(missing_skills[:3])}")
        if has_project == 0:
            suggestions.append("建议补充课程项目、比赛项目或个人作品")
        if has_internship == 0:
            suggestions.append("建议尝试寻找相关实习机会，增强岗位适配度")
        if has_certificate == 0:
            suggestions.append("可根据目标岗位补充相关证书或技能认证")

        return {
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "reasons": reasons,
            "strengths": strengths,
            "suggestions": suggestions
        }

    def recommend(self, resume_text, recall_k=100, topn=20):
        resume_vec = self.model.encode([resume_text], normalize_embeddings=True)[0].astype(np.float32)

        idxs, sims = self.recall(resume_vec, topk=recall_k)
        if len(idxs) == 0:
            return []

        candidate_rows = [self.rows[i] for i in idxs]
        candidate_vecs = self.job_vectors[idxs]

        feats_df = self.rerank(
            resume_text=resume_text,
            resume_vec=resume_vec,
            candidate_rows=candidate_rows,
            candidate_vecs=candidate_vecs,
            candidate_sims=sims
        )

        out_rows = []
        for _, r in feats_df.head(topn).iterrows():
            job_uuid = r["job_uuid"]
            row_meta = self.row_map[job_uuid]
            job_text_obj = json.loads(row_meta.job_text_json)

            explanation = self._build_explanation(resume_text, row_meta, r)

            out_rows.append({
                "uuid": row_meta.uuid,
                "job_id": row_meta.job_id,
                "title": job_text_obj.get("title", ""),
                "job_text": job_text_obj.get("description", ""),
                "sim": float(r.get("sim", 0)),
                "rank_score": float(r.get("rank_score", 0)),
                "skill_match": int(r.get("skill_match", 0)),
                "skill_jaccard": float(r.get("skill_jaccard", 0)),

                # 大学生特征输出
                "has_internship": int(r.get("has_internship", 0)),
                "has_certificate": int(r.get("has_certificate", 0)),
                "has_project": int(r.get("has_project", 0)),
                "has_competition": int(r.get("has_competition", 0)),
                "has_learning_evidence": int(r.get("has_learning_evidence", 0)),
                "has_communication_evidence": int(r.get("has_communication_evidence", 0)),
                "has_pressure_evidence": int(r.get("has_pressure_evidence", 0)),

                # 保留兼容字段
                "explanation": explanation
            })

        return out_rows

def main(args):
    engine = RecommendationEngine(
        model_path=args.model_path,
        db_uri=args.db_uri,
        lgb_model_path=args.lgb_model,
        faiss_index_path=args.faiss_index_path
    )
    engine.load()

    result = engine.recommend(
        resume_text=args.resume_text,
        recall_k=args.recall_k,
        topn=args.topn
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--model_path", required=True)
    p.add_argument("--db_uri", default="sqlite:///jobs.db")
    p.add_argument("--resume_text", required=True)
    p.add_argument("--recall_k", type=int, default=100)
    p.add_argument("--topn", type=int, default=20)
    p.add_argument("--lgb_model", default=None)
    p.add_argument("--faiss_index_path", default="./models/job_faiss.index")
    args = p.parse_args()
    main(args)