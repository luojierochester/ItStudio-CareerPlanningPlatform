"""
自动生成 labels.csv（使用真实技能池）
基于简历和岗位数据，使用规则匹配生成训练标签
"""
import os
import pandas as pd
import json
import re
from typing import List, Dict, Set

def load_skill_dict(skill_dict_path: str = "data/skill_dict.json") -> Set[str]:
    """加载技能词典"""
    if not os.path.exists(skill_dict_path):
        print(f"  找不到技能词典：{skill_dict_path}")
        return set()
    
    with open(skill_dict_path, "r", encoding="utf-8") as f:
        skill_data = json.load(f)
    
    skills = set(skill_data.get("skills", []))
    print(f"✅ 加载技能词典：{len(skills)} 个技能")
    return skills

def load_jobs(jobs_csv: str = "data/jobs.csv") -> pd.DataFrame:
    """加载岗位数据"""
    if not os.path.exists(jobs_csv):
        print(f"❌ 找不到文件：{jobs_csv}")
        print("请先运行 prepare_jobs_data.py 生成岗位数据")
        return None
    
    df = pd.read_csv(jobs_csv)
    print(f"✅ 加载 {len(df)} 个岗位")
    return df

def load_resumes(resumes_csv: str = "data/resumes.csv") -> pd.DataFrame:
    """加载简历数据"""
    if not os.path.exists(resumes_csv):
        print(f"❌ 找不到文件：{resumes_csv}")
        print("\n请创建 data/resumes.csv，格式：")
        print("resume_id,resume_text")
        print('resume_001,"我熟悉Python和PyTorch，有推荐系统项目经历"')
        return None
    
    df = pd.read_csv(resumes_csv)
    print(f"✅ 加载 {len(df)} 份简历")
    return df

def extract_skills_from_text(text: str, skill_pool: Set[str]) -> Set[str]:
    """从文本中提取技能关键词（使用真实技能池）"""
    if not isinstance(text, str):
        return set()
    
    text_lower = text.lower()
    found_skills = set()
    
    for skill in skill_pool:
        # 判断是否为中文技能
        is_chinese = bool(re.search(r'[\u4e00-\u9fa5]', skill))
        
        if is_chinese:
            # 中文技能直接匹配
            if skill in text_lower:
                found_skills.add(skill)
        else:
            # 英文技能需要边界匹配（避免误匹配）
            pattern = r'(?<![a-zA-Z0-9])' + re.escape(skill) + r'(?![a-zA-Z0-9])'
            if re.search(pattern, text_lower):
                found_skills.add(skill)
    
    return found_skills

def calculate_match_score(
    resume_text: str, 
    job_row: pd.Series,
    skill_pool: Set[str]
) -> Dict:
    """
    计算简历和岗位的匹配分数
    返回：{score: int, reasons: List[str], skill_overlap: Set[str]}
    """
    score = 0
    reasons = []
    
    resume_lower = resume_text.lower()
    title_lower = str(job_row.get("title", "")).lower()
    job_desc = str(job_row.get("responsibility", "")).lower()
    job_req = str(job_row.get("job_requirement", "")).lower()
    
    # 提取岗位技能
    job_skills_json = job_row.get("job_skill_tokens", "[]")
    try:
        job_skills = set(json.loads(job_skills_json))
    except:
        job_skills = set()
    
    # 提取简历技能
    resume_skills = extract_skills_from_text(resume_text, skill_pool)
    
    # 1. 技能匹配（最重要，权重最高）
    skill_overlap = resume_skills & job_skills
    if skill_overlap:
        # 核心技能加分更多
        core_skills = {"python", "java", "c++", "javascript", "go", "rust"}
        core_overlap = skill_overlap & core_skills
        
        if core_overlap:
            score += len(core_overlap) * 5
            reasons.append(f"核心技能: {', '.join(list(core_overlap)[:3])}")
        
        # 其他技能
        other_overlap = skill_overlap - core_skills
        if other_overlap:
            score += len(other_overlap) * 3
            reasons.append(f"技能匹配: {', '.join(list(other_overlap)[:3])}")
    
    # 2. 岗位类型匹配
    job_type_mapping = {
    "Java开发": (["java", "springboot", "spring", "mybatis"], ["java", "后端", "开发"]),
    "Python开发": (["python", "django", "flask", "fastapi"], ["python", "后端", "开发"]),
    "前端开发": (["vue", "react", "angular", "javascript", "html", "css"], ["前端", "web"]),
    "测试工程师": (["selenium", "jmeter", "pytest", "自动化测试", "性能测试"], ["测试", "qa"]),
    "算法工程师": (["pytorch", "tensorflow", "机器学习", "深度学习"], ["算法", "ai", "机器学习"]),
    "嵌入式开发": (["嵌入式开发", "stm32", "arm", "单片机", "fpga"], ["嵌入式", "单片机"]),
    "运维工程师": (["linux", "docker", "kubernetes", "devops"], ["运维", "devops"]),
    "实施工程师": (["实施", "部署", "技术支持"], ["实施", "交付"]),
    "数据分析": (["sql", "excel高级", "tableau", "powerbi"], ["数据分析", "数据"]),
    "推荐算法": (["推荐系统", "协同过滤", "召回", "精排", "CTR"], ["推荐", "算法"]),
    "机器学习": (["机器学习", "sklearn", "特征工程", "xgboost", "lightgbm"], ["机器学习", "算法"]),
    "深度学习": (["pytorch", "tensorflow", "深度学习", "神经网络", "transformer"], ["深度学习", "算法"]),
    "数据分析": (["数据分析", "pandas", "numpy", "tableau", "sql", "数据挖掘"], ["数据分析", "数据"]),
    "运维": (["linux", "docker", "kubernetes", "ansible", "运维"], ["运维", "devops"]),
    "测试": (["测试", "selenium", "appium", "jmeter", "自动化测试"], ["测试", "qa"]),
}
    
    for job_type, (tech_keywords, title_keywords) in job_type_mapping.items():
        resume_has_tech = any(kw in resume_skills for kw in tech_keywords)
        job_has_tech = any(kw in job_skills for kw in tech_keywords)
        job_has_title = any(kw in title_lower for kw in title_keywords)
        
        if resume_has_tech and (job_has_tech or job_has_title):
            score += 3
            reasons.append(f"岗位类型: {job_type}")
            break
    
    # 3. 学历匹配
    education_levels = {
        "博士": 5,
        "硕士": 4,
        "研究生": 4,
        "本科": 3,
        "大专": 2,
    }
    
    resume_edu = None
    job_edu = None
    
    for edu, level in education_levels.items():
        if edu in resume_lower and resume_edu is None:
            resume_edu = (edu, level)
        if edu in job_desc and job_edu is None:
            job_edu = (edu, level)
    
    if resume_edu and job_edu:
        if resume_edu[1] >= job_edu[1]:
            score += 2
            reasons.append(f"学历匹配: {resume_edu[0]} >= {job_edu[0]}")
        elif resume_edu[1] == job_edu[1] - 1:
            score += 1
            reasons.append(f"学历接近: {resume_edu[0]} ≈ {job_edu[0]}")
    
    # 4. 工作经验匹配
    resume_exp_match = re.search(r"(\d+)\s*年.*?经验", resume_lower)
    job_exp_match = re.search(r"(\d+)\s*年.*?经验", job_desc)
    
    if resume_exp_match and job_exp_match:
        resume_years = int(resume_exp_match.group(1))
        job_years = int(job_exp_match.group(1))
        
        if resume_years >= job_years:
            score += 2
            reasons.append(f"经验匹配: {resume_years}年 >= {job_years}年")
        elif resume_years >= job_years - 1:
            score += 1
            reasons.append(f"经验接近: {resume_years}年 ≈ {job_years}年")
    
    # 5. 应届生/实习生特殊处理
    is_fresh_grad = any(kw in resume_lower for kw in ["应届", "在校", "实习生", "毕业生"])
    job_accepts_fresh = any(kw in job_desc for kw in ["应届", "实习", "无经验", "不限经验"])
    
    if is_fresh_grad and job_accepts_fresh:
        score += 2
        reasons.append("应届生岗位匹配")
    elif is_fresh_grad and not job_accepts_fresh and job_exp_match:
        score -= 2  # 应届生投有经验要求的岗位，减分
    
    # 6. 项目经历
    if "项目" in resume_lower:
        if "项目" in job_desc or "项目经验" in job_desc:
            score += 1
            reasons.append("有项目经历")
    
    # 7. 证书匹配
    cert_keywords = [
        "英语四级", "英语六级", "cet4", "cet6",
        "软考", "计算机等级", "教师资格证", "教资",
        "注册会计师", "cpa", "法考", "执业医师证"
    ]
    
    for cert in cert_keywords:
        if cert in resume_lower and cert in job_desc:
            score += 1
            reasons.append(f"证书: {cert}")
            break
    
    # 8. 竞赛经历
    competition_keywords = ["竞赛", "蓝桥杯", "acm", "数学建模", "挑战杯"]
    if any(kw in resume_lower for kw in competition_keywords):
        if any(kw in job_desc for kw in ["竞赛", "算法", "编程能力"]):
            score += 1
            reasons.append("竞赛经历")
    
    # 9. 地域匹配（如果简历中提到地点）
    cities = ["北京", "上海", "广州", "深圳", "杭州", "成都", "武汉", "西安", "南京", "苏州"]
    job_address = str(job_row.get("address", "")).lower()
    
    for city in cities:
        if city in resume_lower and city in job_address:
            score += 1
            reasons.append(f"地域: {city}")
            break
    
    return {
        "score": score,
        "reasons": reasons,
        "skill_overlap": skill_overlap,
        "skill_overlap_count": len(skill_overlap)
    }

def generate_labels(
    resumes_df: pd.DataFrame,
    jobs_df: pd.DataFrame,
    skill_pool: Set[str],
    positive_per_resume: int = 8,
    negative_per_resume: int = 15,
    score_threshold: int = 6
) -> pd.DataFrame:
    """
    为每份简历生成标签
    
    Args:
        resumes_df: 简历数据
        jobs_df: 岗位数据
        skill_pool: 技能词典
        positive_per_resume: 每份简历的正样本数量
        negative_per_resume: 每份简历的负样本数量
        score_threshold: 正样本的最低分数阈值
    """
    all_labels = []
    
    for idx, resume_row in resumes_df.iterrows():
        resume_id = resume_row["resume_id"]
        resume_text = resume_row["resume_text"]
        
        print(f"\n[{idx+1}/{len(resumes_df)}] 处理简历：{resume_id}")
        
        # 计算所有岗位的匹配分数
        job_scores = []
        for _, job_row in jobs_df.iterrows():
            job_id = job_row["job_id"]
            match_result = calculate_match_score(resume_text, job_row, skill_pool)
            
            job_scores.append({
                "job_id": job_id,
                "job_title": job_row.get("title", ""),
                "score": match_result["score"],
                "reasons": match_result["reasons"],
                "skill_overlap": match_result["skill_overlap"],
                "skill_overlap_count": match_result["skill_overlap_count"]
            })
        
        # 按分数排序
        job_scores.sort(key=lambda x: (x["score"], x["skill_overlap_count"]), reverse=True)
        
        # 选择正样本（高分）
        positive_jobs = [
            js for js in job_scores 
            if js["score"] >= score_threshold
        ][:positive_per_resume]
        
        # 选择负样本（低分，但有一定相关性）
        negative_jobs = [
            js for js in job_scores 
            if 2 <= js["score"] < score_threshold
        ][:negative_per_resume]
        
        # 如果负样本不够，补充一些完全无关的
        if len(negative_jobs) < negative_per_resume:
            zero_score_jobs = [
                js for js in job_scores 
                if js["score"] < 2
            ][:negative_per_resume - len(negative_jobs)]
            negative_jobs.extend(zero_score_jobs)
        
        # 生成标签
        for job in positive_jobs:
            all_labels.append({
                "resume_id": resume_id,
                "job_id": job["job_id"],
                "job_title": job["job_title"],
                "label": 1,
                "score": job["score"],
                "skill_overlap": ", ".join(list(job["skill_overlap"])[:5]),
                "reasons": "; ".join(job["reasons"][:3])
            })
        
        for job in negative_jobs:
            all_labels.append({
                "resume_id": resume_id,
                "job_id": job["job_id"],
                "job_title": job["job_title"],
                "label": 0,
                "score": job["score"],
                "skill_overlap": ", ".join(list(job["skill_overlap"])[:5]) if job["skill_overlap"] else "",
                "reasons": "; ".join(job["reasons"][:3]) if job["reasons"] else "无明显匹配"
            })
        
        print(f"  ✓ 正样本: {len(positive_jobs)}, 负样本: {len(negative_jobs)}")
        if positive_jobs:
            top_job = positive_jobs[0]
            print(f"  ✓ 最佳匹配: {top_job['job_title'][:30]} (分数: {top_job['score']})")
            if top_job['skill_overlap']:
                print(f"    技能: {', '.join(list(top_job['skill_overlap'])[:5])}")
    
    return pd.DataFrame(all_labels)

def main():
    print(" 开始生成 labels.csv...\n")
    
    # 1. 加载数据
    skill_pool = load_skill_dict("data/skill_dict.json")
    jobs_df = load_jobs("data/jobs.csv")
    resumes_df = load_resumes("data/resumes.csv")
    
    if jobs_df is None or resumes_df is None:
        return
    
    if not skill_pool:
        print("⚠️  技能词典为空，将使用基础匹配")
    
    # 2. 生成标签
    print(f"\n 开始匹配...")
    labels_df = generate_labels(
        resumes_df=resumes_df,
        jobs_df=jobs_df,
        skill_pool=skill_pool,
        positive_per_resume=8,   # 每份简历8个正样本
        negative_per_resume=15,  # 每份简历15个负样本
        score_threshold=6        # 分数>=6认为匹配
    )
    
    # 3. 保存结果
    output_file = "data/labels.csv"
    
    # 保存完整版（带分数和原因，用于调试）
    labels_df.to_csv("data/labels_with_scores.csv", index=False, encoding="utf-8-sig")
    
    # 保存简化版（只有3列，用于训练）
    labels_simple = labels_df[["resume_id", "job_id", "label"]].copy()
    labels_simple.to_csv(output_file, index=False, encoding="utf-8-sig")
    
    # 4. 统计信息
    total = len(labels_simple)
    positive = labels_simple["label"].sum()
    negative = total - positive
    
    print(f"\n{'='*60}")
    print(f"✅ 生成完成！")
    print(f"{'='*60}")
    print(f"\n 保存文件：")
    print(f"   - {output_file} (训练用)")
    print(f"   - data/labels_with_scores.csv (调试用)")
    print(f"\n 统计信息：")
    print(f"   总样本数：{total}")
    print(f"   正样本：{positive} ({positive/total:.1%})")
    print(f"   负样本：{negative} ({negative/total:.1%})")
    print(f"   简历数：{len(resumes_df)}")
    print(f"   岗位数：{len(jobs_df)}")
    print(f"   平均每份简历：{total/len(resumes_df):.1f} 个样本")
    
    # 5. 预览正样本
    print(f"\n─── 正样本预览（前5条）───")
    positive_samples = labels_df[labels_df["label"] == 1].head(5)
    for _, row in positive_samples.iterrows():
        print(f"\n简历: {row['resume_id']} → 岗位: {row['job_title'][:40]}")
        print(f"  分数: {row['score']}, 技能: {row['skill_overlap'][:60]}")
        print(f"  原因: {row['reasons'][:80]}")
    
    print(f"\n 提示：")
    print(f"   1. 查看 data/labels_with_scores.csv 了解详细匹配原因")
    print(f"   2. 如果正样本太少，降低 score_threshold (当前: 6)")
    print(f"   3. 如果需要更多样本，增加 positive_per_resume 和 negative_per_resume")
    print(f"\n下一步：运行以下命令生成特征")
    print(f"   python generate_lgb_training_data.py")

if __name__ == "__main__":
    main()