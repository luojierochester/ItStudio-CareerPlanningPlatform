"""
岗位数据准备脚本（增强版）
将岗位数据.xls转换为训练LightGBM所需的格式
使用更全面的技能关键词库
"""
import os
import sys
import pandas as pd
import re
import json
import numpy as np
from typing import List, Dict, Optional

# ==================== 完整技能关键词映射表 ====================
SKILL_MAP = {
    #==================== 编程语言 / 基础开发 ====================
    "python": "python", "java": "java", "c++": "c++", "c#": "c#",
    "golang": "go", "go语言": "go", "rust": "rust", "scala": "scala",
    "kotlin": "kotlin", "swift": "swift", "php": "php",
    "javascript": "javascript", "js": "javascript",
    "typescript": "typescript", "ts": "typescript",
    "html": "html", "css": "css", "html5": "html5", "css3": "css3",
    "shell": "shell", "bash": "shell", "powershell": "shell",
    "matlab": "matlab", "r语言": "r", "r": "r", "lua": "lua",
    "汇编": "汇编语言", "perl": "perl",
    # ==================== 前端 ====================
    "vue": "vue", "react": "react", "angular": "angular",
    "jquery": "jquery", "uni-app": "uni-app", "uniapp": "uni-app",
    "小程序": "微信小程序", "flutter": "flutter", "webpack": "webpack",
    "vite": "vite", "element": "element-ui", "antd": "antd",
    "nuxt": "nuxt", "next": "nextjs", "tailwind": "tailwindcss",
    "svelte": "svelte", "quasar": "quasar",
    # ==================== 后端 ====================
    "spring": "spring", "springboot": "springboot",
    "spring boot": "springboot", "mybatis": "mybatis",
    "django": "django", "flask": "flask", "fastapi": "fastapi",
    "node.js": "nodejs", "nodejs": "nodejs", "express": "express",
    "gin": "gin", "beego": "beego", "nestjs": "nestjs",
    "tomcat": "tomcat", "jboss": "jboss",
    # ==================== 数据库 / 中间件 ====================
    "mysql": "mysql", "postgresql": "postgresql", "postgres": "postgresql",
    "oracle": "oracle", "sql server": "sqlserver", "sqlserver": "sqlserver",
    "sqlite": "sqlite", "mongodb": "mongodb", "redis": "redis",
    "elasticsearch": "elasticsearch", "es": "elasticsearch",
    "hbase": "hbase", "cassandra": "cassandra",
    "达梦": "达梦数据库", "人大金仓": "人大金仓",
    "国产数据库": "国产数据库", "sql": "sql",
    "存储过程": "存储过程", "索引优化": "索引优化",
    "rabbitmq": "rabbitmq", "rocketmq": "rocketmq",
    # ==================== 大数据 / 数据分析 ====================
    "hadoop": "hadoop", "spark": "spark", "kafka": "kafka",
    "hive": "hive", "flink": "flink", "hdfs": "hdfs",
    "zookeeper": "zookeeper", "flume": "flume", "sqoop": "sqoop",
    "pandas": "pandas", "numpy": "numpy", "matplotlib": "matplotlib",
    "tableau": "tableau", "power bi": "powerbi", "powerbi": "powerbi",
    "superset": "superset", "datax": "datax",
    # ==================== 云原生 / 运维 / DevOps ====================
    "docker": "docker", "kubernetes": "kubernetes", "k8s": "kubernetes",
    "linux": "linux", "centos": "linux", "ubuntu": "linux",
    "git": "git", "svn": "svn", "jenkins": "jenkins",
    "nginx": "nginx", "ansible": "ansible", "prometheus": "prometheus",
    "grafana": "grafana", "harbor": "harbor",
    "ci/cd": "ci/cd", "devops": "devops",
    # ==================== AI / 大模型 / 机器学习 ====================
    "tensorflow": "tensorflow", "pytorch": "pytorch",
    "scikit-learn": "sklearn", "sklearn": "sklearn",
    "opencv": "opencv", "深度学习": "深度学习",
    "机器学习": "机器学习", "人工智能": "人工智能", "ai": "人工智能",
    "自然语言处理": "nlp", "nlp": "nlp",
    "计算机视觉": "cv", "cv": "cv", "推荐系统": "推荐系统",
    "大模型": "大模型", "llm": "大模型", "langchain": "langchain",
    "rag": "rag", "aigc": "aigc",
    # ==================== 测试 ====================
    "selenium": "selenium", "appium": "appium", "jmeter": "jmeter",
    "postman": "postman", "pytest": "pytest", "junit": "junit",
    "接口测试": "接口测试", "自动化测试": "自动化测试",
    "性能测试": "性能测试", "黑盒测试": "黑盒测试",
    "白盒测试": "白盒测试", "回归测试": "回归测试",
    "禅道": "禅道", "jira": "jira",
    # ==================== 嵌入式 / 物联网 / 电子电气 ====================
    "嵌入式": "嵌入式开发", "单片机": "单片机", "stm32": "stm32",
    "fpga": "fpga", "verilog": "verilog", "vhdl": "vhdl",
    "arm": "arm", "rtos": "rtos", "freertos": "freertos",
    "autosar": "autosar", "can总线": "can", "can": "can",
    "modbus": "modbus", "opc": "opc", "plc": "plc",
    "物联网": "iot", "iot": "iot", "5g": "5g", "lora": "lora",
    "nb-iot": "nb-iot", "蓝牙": "蓝牙", "zigbee": "zigbee",
    "电源设计": "电源设计", "pcb": "pcb设计", "ad": "altium designer",
    "altium designer": "altium designer", "cadence": "cadence",
    # ==================== 机械/ 机电 ====================
    "solidworks": "solidworks", "ug": "ug", "catia": "catia",
    "proe": "proe", "creo": "creo", "ansys": "ansys",
    "abaqus": "abaqus", "hypermesh": "hypermesh",
    "cad": "cad", "caxa": "caxa", "数控编程": "数控编程",
    "加工中心": "加工中心", "夹具设计": "夹具设计",
    "液压传动": "液压传动", "气动控制": "气动控制",
    # ==================== 土木 / 建筑 / 测绘 ====================
    "bim": "bim", "revit": "revit", "civil3d": "civil3d",
    "tekla": "tekla", "pkpm": "pkpm", "盈建科": "盈建科",
    "arcgis": "arcgis", "cass": "cass", "gis": "gis",
    "测量": "工程测量", "造价": "工程造价",
    "广联达": "广联达", "品茗": "品茗", "混凝土": "混凝土",
    "钢结构": "钢结构", "装配式": "装配式建筑",
    # ==================== 化工 / 环境 ====================
    "hplc": "高效液相色谱", "gc-ms": "气相色谱质谱",
    "pcr": "pcr检测", "细胞培养": "细胞培养",
    "发酵工艺": "发酵工艺", "精馏": "精馏",
    "环评": "环境评价", "污水治理": "污水处理",
    "voc": "voc治理", "origin": "origin绘图",
    "chemdraw": "chemdraw", "autocad plant": "工厂设计",
    # ==================== 医学 / 药学 / 生物 ====================
    "ngs": "高通量测序", "高通量测序": "ngs",
    "流式细胞仪": "流式细胞仪", "病理切片": "病理切片",
    "药理实验": "药理实验", "gcp": "gcp", "gmp": "gmp",
    "医学影像": "医学影像", "ct": "ct操作", "mr": "核磁",
    "护士资格证": "护士证", "执业医师": "执业医师证",
    # ==================== 会计 / 财务 / 金融 ====================
    "用友": "用友", "金蝶": "金蝶", "sap": "sap",
    "excel": "excel高级", "vlookup": "vlookup",
    "数据透视表": "数据透视表", "会计电算化": "会计电算化",
    "初级会计": "初级会计证", "中级会计": "中级会计证",
    "cpa": "注册会计师", "税务师": "税务师",
    "审计": "审计", "报税": "纳税申报",
    "资产评估": "资产评估", "银行从业": "银行从业",
    "证券从业": "证券从业", "基金从业": "基金从业",
    "风控": "风险控制", "信贷": "信贷业务",
    # ==================== 人力资源 / 行政 ====================
    "人力资源": "人力资源管理", "招聘": "招聘",
    "薪酬绩效": "薪酬绩效", "社保公积金": "社保操作",
    "劳动法": "劳动法", "劳动合同": "劳动合同",
    "e-hr": "ehr系统", "北森": "北森系统",
    # ==================== 设计类 ====================
    "ps": "photoshop", "photoshop": "photoshop",
    "illustrator": "illustrator", "id": "indesign",
    "cdr": "coreldraw", "sketch": "sketch", "figma": "figma",
    "3dmax": "3dmax", "maya": "maya", "blender": "blender",
    "c4d": "c4d", "su": "sketchup", "sketchup": "草图大师",
    "室内设计": "室内设计", "平面设计": "平面设计",
    # ==================== 英语 / 语言能力 ====================
    "英语四级": "cet4", "cet4": "英语四级",
    "英语六级": "cet6", "cet6": "英语六级",
    "专四": "专四", "专八": "专八",
    "雅思": "雅思", "托福": "托福",
    "英语口语": "英语口语", "英语翻译": "英语翻译",
    # ==================== 教师 / 教育类 ====================
    "教师资格证": "教资", "教资": "教师资格证",
    "普通话": "普通话证书", "教育学": "教育学",
    "教育心理学": "教育心理学", "课程设计": "课程设计",
    "课堂管理": "课堂管理", "课件制作": "课件制作",
    # ==================== 法律 / 公考 ====================
    "法律职业资格证": "法考a证", "法考": "法律资格证",
    "公文写作": "公文写作", "申论": "申论",
    "行测": "行测", "公务员": "公务员能力",
    # ==================== 物流 / 电商 ====================
    "仓储管理": "仓储", "物流系统": "物流系统",
    "供应链": "供应链管理", "快递运营": "快递运营",
    "电商运营": "电商运营", "淘宝运营": "淘宝运营",
    "抖音运营": "抖音运营", "新媒体运营": "新媒体运营",
    # ==================== 通用能力 ====================
    "office": "office", "word": "word", "ppt": "ppt",
    "visio": "visio", "project": "project",
    "沟通能力": "沟通", "团队协作": "团队协作",
    "抗压能力": "抗压", "时间管理": "时间管理",
    "报告撰写": "报告撰写", "资料整理": "资料整理",
}

# ==================== 段落提取规则 ====================
SECTION_RULES = {
    "工作内容": [
        r"工作内容[：:]\s*([\s\S]*?)(?=\n\s*(?:岗位要求|任职要求|入职要求|岗位职责|工作时间|薪资待遇|$))",
        r"工作职责[：:]\s*([\s\S]*?)(?=\n\s*(?:岗位要求|任职要求|入职要求|工作时间|薪资待遇|$))",
        r"主要工作[：:]\s*([\s\S]*?)(?=\n\s*(?:岗位要求|任职要求|入职要求|工作时间|$))",
    ],
    "岗位要求": [
        r"(?:岗位要求|任职要求|入职要求)[：:]\s*([\s\S]*?)(?=\n\s*(?:工作内容|工作时间|薪资待遇|福利|$))",
        r"岗位职责[：:]\s*([\s\S]*?)(?=\n\s*(?:工作内容|工作时间|薪资待遇|$))",
    ],
    "工作时间": [
        r"(?:工作时间|上班时间|班次安排)[：:]\s*([^\n]{2,80})",
    ],
}

# ==================== 工具函数 ====================
def clean_html(text: str) -> str:
    """清理HTML标签"""
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    return text.strip()

def clean_field(val) -> str:
    """清理字段内容"""
    if pd.isna(val):
        return ""
    text = clean_html(str(val))
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def extract_section(full_text: str, rules: list) -> str:
    """按规则列表依次尝试提取段落"""
    for pattern in rules:
        m = re.search(pattern, full_text, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return ""

def extract_skills(text: str) -> list:
    """从文本中提取技能关键词"""
    if not text:
        return []
    text_lower = text.lower()
    found = {}
    
    for keyword, standard in SKILL_MAP.items():
        is_cn = bool(re.search(r'[\u4e00-\u9fa5]', keyword))
        if is_cn:
            # 中文关键词直接匹配
            if keyword in text_lower:
                found[standard] = True
        else:
            # 英文关键词需要边界匹配
            pat = r'(?<![a-zA-Z0-9])' + re.escape(keyword) + r'(?![a-zA-Z0-9])'
            if re.search(pat, text_lower):
                found[standard] = True
    
    return list(found.keys())

def extract_min_years(text: str) -> int:
    """提取最低工作年限"""
    if not text:
        return 0
    if re.search(r"应届|无经验|不限|在校生|实习生|应届毕业生", text):
        return 0
    m = re.search(r"(\d+)\s*年(?:以上|及以上)?(?:工作|开发|相关|实际)?经验", text)
    if m:
        return min(int(m.group(1)), 10)
    return 0

def clean_salary(salary: str) -> str:
    """清洗薪资格式"""
    if not isinstance(salary, str):
        return "面议"
    
    salary = salary.replace("元", "").replace("·", "").replace(" ", "").strip()
    if "面议" in salary or "议" in salary:
        return "面议"
    if "天" in salary:
        return f"{salary}元/天"
    if "月" in salary:
        return f"{salary}元/月"
    if "年" in salary:
        return f"{salary}元/年"
    
    if "-" in salary and not any(c in salary for c in ["·", "天", "月", "年"]):
        return f"{salary}元/月"
    
    return f"{salary}元"

# ==================== 主函数 ====================
def main():
    print("🔍 开始准备岗位数据...")
    
    # 1. 读取Excel文件
    excel_file = "岗位数据.xls"
    if not os.path.exists(excel_file):
        print(f"❌ 找不到文件：{excel_file}")
        return
    
    try:
        df = pd.read_excel(excel_file, dtype=str)
        print(f"✅ 成功读取 {len(df)} 个岗位数据")
        print(f"   原始列：{list(df.columns)}")
    except Exception as e:
        print(f"❌ 读取Excel文件失败：{e}")
        return
    
    # 2. 处理数据
    rows = []
    skill_empty = 0
    
    for idx, row in df.iterrows():
        # 基础字段
        job_id = clean_field(row.get("岗位编码", "")) or f"JOB_{idx:05d}"
        title = clean_field(row.get("岗位名称", "")) or "未知岗位"
        company = clean_field(row.get("公司名称", ""))
        address = clean_field(row.get("地址", ""))
        salary = clean_salary(clean_field(row.get("薪资范围", "")))
        industry = clean_field(row.get("所属行业", ""))
        detail = clean_field(row.get("岗位详情", ""))
        
        if not detail or len(detail) < 5:
            continue
        
        # 从岗位详情中提取细分段落
        work_content = extract_section(detail, SECTION_RULES["工作内容"])
        job_req = extract_section(detail, SECTION_RULES["岗位要求"])
        work_time = extract_section(detail, SECTION_RULES["工作时间"])
        
        # 技能提取（全文）
        skills = extract_skills(detail)
        if not skills:
            skill_empty += 1
        
        # 提取最低工作年限
        min_years = extract_min_years(detail)
        
        rows.append({
            "job_id": job_id,
            "title": title,
            "company": company,
            "address": address,
            "salary": salary,
            "industry": industry,
            "responsibility": detail,
            "work_content": work_content,
            "job_requirement": job_req,
            "work_time": work_time,
            "job_skill_tokens": json.dumps(skills, ensure_ascii=False),
            "min_years": min_years,
        })
    
    # 3. 生成 DataFrame
    COLUMNS = [
        "job_id", "title", "company", "address", "salary", "industry",
        "responsibility", "work_content", "job_requirement", "work_time",
        "job_skill_tokens", "min_years",
    ]
    
    out_df = pd.DataFrame(rows, columns=COLUMNS)
    
    # 4. 保存 jobs.csv
    os.makedirs("data", exist_ok=True)
    out_df.to_csv("data/jobs.csv", index=False, encoding="utf-8-sig")
    
    total = len(out_df)
    print(f"\n✅ 已保存：data/jobs.csv，共 {total} 条")
    print(f"   技能提取成功：{total - skill_empty} 条 ({(total-skill_empty)/total:.1%})")
    print(f"   技能为空：{skill_empty} 条 ({skill_empty/total:.1%})")
    
    # 5. 生成技能词典
    all_skills = []
    for skills_json in out_df["job_skill_tokens"]:
        skills = json.loads(skills_json)
        all_skills.extend(skills)
    
    skill_counts = pd.Series(all_skills).value_counts()
    skill_dict = {
        "skills": skill_counts.index.tolist(),
        "counts": skill_counts.values.tolist()
    }
    
    with open("data/skill_dict.json", "w", encoding="utf-8") as f:
        json.dump(skill_dict, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 生成 skill_dict.json：{len(skill_counts)} 个技能")
    
    # 6. 统计信息
    print("\n📊 技能出现频次 TOP 20：")
    for skill, count in zip(skill_counts.index[:20], skill_counts.values[:20]):
        print(f"  {skill}: {count}")
    
    # 7. 预览前3条
    print("\n─── 前3条完整预览 ───")
    for _, r in out_df.head(3).iterrows():
        print(f"\n{'─'*60}")
        print(f"job_id          : {r['job_id']}")
        print(f"title           : {r['title']}")
        print(f"company         : {r['company']}")
        print(f"salary          : {r['salary']}")
        print(f"industry        : {r['industry']}")
        print(f"work_content    : {str(r['work_content'])[:80] or '(未提取到)'}...")
        print(f"job_requirement : {str(r['job_requirement'])[:80] or '(未提取到)'}...")
        print(f"work_time       : {r['work_time'] or '(未提取到)'}")
        print(f"job_skill_tokens: {r['job_skill_tokens']}")
        print(f"min_years       : {r['min_years']}")
    
    print("\n✅ 岗位数据准备完成！")
    print("📁 生成文件：")
    print("  - data/jobs.csv          （用于数据库）")
    print("  - data/skill_dict.json   （技能词典）")

if __name__ == "__main__":
    main()