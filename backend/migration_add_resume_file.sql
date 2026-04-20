-- 添加 resume_file 字段到 user_file 表
-- 用于存储用户简历文件的 UUID

ALTER TABLE user_file ADD COLUMN resume_file CHAR(36) NULL COMMENT '简历文件UUID';

-- 创建索引以提高查询性能
CREATE INDEX idx_resume_file ON user_file(resume_file);
