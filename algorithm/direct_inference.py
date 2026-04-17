from sentence_transformers import SentenceTransformer, util
import pandas as pd
import json

def main():

    MODEL_PATH = "paraphrase-multilingual-MiniLM-L12-v2"
    JOBS_CSV_PATH = "data/jobs.csv"  
    RESUME_TEXT = "我有两年 PyTorch 项目经验，熟悉深度学习"  
    RECALL_K = 10  

    print("正在加载模型...")
    model = SentenceTransformer(MODEL_PATH)
    print("模型加载完成！")

    
    print(f"正在读取岗位数据: {JOBS_CSV_PATH}")
    jobs_df = pd.read_csv(JOBS_CSV_PATH)
    print(f"成功读取 {len(jobs_df)} 条岗位数据！")

    
    resume_embedding = model.encode(RESUME_TEXT, convert_to_tensor=True)
    
    results = []
    for idx, row in jobs_df.iterrows():
        job_id = row["job_id"]
        job_title = row["title"]
        job_desc = row["description"]
        job_full_text = f"{job_title}\n{job_desc}" 
        
        job_embedding = model.encode(job_full_text, convert_to_tensor=True)
        
        sim_score = util.cos_sim(resume_embedding, job_embedding).item()
        

        results.append({
            "uuid": f"job_{job_id}",  
            "job_text": job_full_text[:300] + "..." if len(job_full_text) > 300 else job_full_text,
            "sim": round(sim_score, 6),
            "lgb_score": None  
        })

    results_sorted = sorted(results, key=lambda x: x["sim"], reverse=True)[:RECALL_K]

    print("\n=== 简历岗位推荐结果 ===")
    print(json.dumps(results_sorted, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()