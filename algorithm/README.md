1.项目简介

基于Sentence-BERT 文本语义向量 + LightGBM 排序模型的简历 - 职位匹配推荐系统。
输入：用户简历文本
输出：Top-K 最匹配职位列表（含相似度 / 排序分数）

关键词通过features_examples.csv进行管理

2.环境依赖

Python 3.10+
依赖安装：
bash
运行
pip install -r requirements.txt

3.项目结构

├── api.py                      # FastAPI 服务入口  
├── db_models.py                # SQLAlchemy 数据库模型  
├── encode_jobs_db.py           # 岗位编码并写入 SQLite / 构建 FAISS 索引  
├── feature_engineering_db.py  # 特征工程（从 features_examples.csv 读取词典）  
├── inference_pipeline_db.py   # 核心推理引擎 RecommendationEngine  
├── direct_inference.py        # 命令行演示脚本（复用 RecommendationEngine）  
├── train_bi_encoder.py        # 双塔模型训练  
├── train_lgb.py               # LightGBM 精排模型训练  
├── features_examples.csv      # 特征关键词外部词典  
├── requirements.txt  
├── run_demo.sh                # 一键演示脚本  
├── CHANGELOG.md  
└── README.md  

4.特征词典

feature_name,keyword
has_internship,实习
has_internship,intern
has_project,项目
has_project,毕业设计
has_certificate,证书
has_certificate,软考
has_competition,竞赛
has_competition,蓝桥杯
skill,python
skill,java
skill,mysql

| `feature_name` 取值 | 含义 |
|---------------------|------|
| `skill` | 技能关键词 |
| `has_internship` | 实习经历关键词 |
| `has_project` | 项目经历关键词 |
| `has_certificate` | 证书/认证关键词 |
| `has_competition` | 竞赛/创新经历关键词 |
| `has_learning_evidence` | 学习能力关键词 |
| `has_communication_evidence` | 沟通能力关键词 |
| `has_pressure_evidence` | 抗压能力关键词 |

5.数据格式说明


```csv
job_id,title,job_text,job_skill_tokens,min_years
001,Java开发工程师,负责后端系统开发，使用SpringBoot...,"[""java"",""spring"",""mysql""]",0
002,测试工程师,负责功能测试与接口测试...,"[""测试"",""sql"",""接口测试""]",0
```

| 字段 | 说明 |
|------|------|
| `job_id` | 岗位唯一标识 |
| `title` | 岗位标题 |
| `job_text` | 岗位完整文本描述 |
| `job_skill_tokens` | 技能关键词列表（JSON 数组） |


6.启动命令

可能会出现SSL认证问题
$env:HF_ENDPOINT = "https://hf-mirror.com"
如若有模型文件，无需修改

### Step 1：岗位编码入库

python encode_jobs_db.py \
  --jobs_csv data/jobs.csv \
  --model_name_or_path ./model \
  --db_uri sqlite:///jobs.db \
  --faiss_index_path ./models/job_faiss.index

### Step 2（可选）：训练双塔模型

python train_bi_encoder.py \
  --train_csv data/train_pairs.csv \
  --model_name_or_path paraphrase-multilingual-MiniLM-L12-v2 \
  --out_dir ./models/bi_encoder \
  --epochs 2 \
  --batch_size 32

训练数据格式：

resume_text,job_text,label
我熟悉Java...,负责Java后端开发...,1
我熟悉Java...,负责硬件测试...,0


### Step 3（可选）：训练 LightGBM 精排模型

python train_lgb.py \
  --features_csv data/features_for_lgb.csv \
  --out_dir ./models/lgb \
  --objective lambdarank


7. 命令行推理

### 不使用 LightGBM（纯规则打分）

python inference_pipeline_db.py \
  --model_path ./model \
  --db_uri sqlite:///jobs.db \
  --resume_text "我熟悉Python和PyTorch，有推荐系统课程项目经历，曾参加蓝桥杯竞赛" \
  --recall_k 50 \
  --topn 10 \
  --faiss_index_path ./models/job_faiss.index

### 使用 LightGBM 精排

python inference_pipeline_db.py \
  --model_path ./model \
  --db_uri sqlite:///jobs.db \
  --resume_text "我熟悉Python和PyTorch，有推荐系统课程项目经历，曾参加蓝桥杯竞赛" \
  --recall_k 50 \
  --topn 10 \
  --lgb_model ./models/lgb/lgb_model.joblib \
  --faiss_index_path ./models/job_faiss.index


8. API 服务

### 启动服务

python api.py

默认监听：'http://0.0.0.0:8001'


9.输入参数说明

参数	说明	示例
--model_path	句向量模型路径	./models/...-L12-v2
--db_uri	数据库地址	sqlite:///jobs.db
--resume_text	简历 / 用户描述	字符串
--recall_k	返回职位数量	10

10. 输出格式（JSON 结构）
json
[
     {
      "uuid": "02f9600c-554c-481b-8c9b-e6b7437fdd17",
      "job_id": "001",
      "title": "算法工程师",
      "sim": 0.8732,
      "rank_score": 0.9121,
      "skill_match": 3,
      "skill_jaccard": 0.4286,
      "has_internship": 1,
      "has_certificate": 0,
      "has_project": 1,
      "has_competition": 1,
      "has_learning_evidence": 1,
      "has_communication_evidence": 0,
      "has_pressure_evidence": 0,
      "explanation": {
        "matched_skills": ["python", "pytorch", "推荐系统"],
        "missing_skills": ["spark", "hadoop"],
        "reasons": [
          "简历与岗位语义相似度较高",
          "匹配到 3 个岗位技能关键词",
          "简历中包含项目经历",
          "简历中包含竞赛或创新经历"
        ],
        "strengths": [
          "专业技能匹配度较高",
          "具备项目实践基础",
          "简历体现出较强学习能力"
        ],
        "suggestions": [
          "建议优先补充岗位相关技能：spark、hadoop",
          "建议尝试寻找相关实习机会，增强岗位适配度"
        ]
      }
    }
    ...
]
11. 模型说明

Embedding 模型：paraphrase-multilingual-MiniLM-L12-v2
首次运行会自动下载模型(时间可能较长)
功能：将文本转为语义向量
Rank 模型：LightGBM
功能：对召回结果精排，提升匹配准确度

FastAPI 服务化部署
支持命令行推理

12脚本
新增run_demo.bat脚本
