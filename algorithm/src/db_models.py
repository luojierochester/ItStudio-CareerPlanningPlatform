"""
数据库模型：使用 SQLite + SQLAlchemy。
所有复杂字段以 JSON 字符串存储（Text）。
主键使用 UUID 字符串（version4）。
"""
import uuid
import json
from sqlalchemy import create_engine, Column, String, Text, Integer
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Job(Base):
    __tablename__ = "jobs"

    uuid = Column(String(36), primary_key=True)
    job_id = Column(String(128), index=True, nullable=True)
    job_text_json = Column(Text, nullable=False)          # 岗位主体信息
    job_skill_tokens_json = Column(Text, nullable=True)   # 技能列表
    min_years = Column(Integer, index=True, nullable=True)
    job_vector_json = Column(Text, nullable=True)         # 向量
    extra_json = Column(Text, nullable=True)              # 扩展信息

def get_engine(db_uri="sqlite:///jobs.db"):
    return create_engine(
        db_uri,
        connect_args={"check_same_thread": False}
    )

def create_tables(engine):
    Base.metadata.create_all(engine)

def make_uuid():
    return str(uuid.uuid4())

def job_row_from_dict(dct):
    """
    统一构造 DB 存储字段
    """
    job_text_payload = {
        "title": dct.get("title", ""),
        "description": dct.get("job_text", ""),
        "skills": dct.get("job_skill_tokens", []),
        "min_years": dct.get("min_years", None),
    }

    return {
        "job_text_json": json.dumps(job_text_payload, ensure_ascii=False),
        "job_skill_tokens_json": json.dumps(dct.get("job_skill_tokens", []), ensure_ascii=False),
        "extra_json": json.dumps(dct.get("extra", {}), ensure_ascii=False)
    }

if __name__ == "__main__":
    engine = get_engine()
    create_tables(engine)
    print("Created tables at jobs.db")