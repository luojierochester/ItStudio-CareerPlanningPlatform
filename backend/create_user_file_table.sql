-- 创建 user_file 表
-- 用于存储用户上传的文件 UUID

CREATE TABLE IF NOT EXISTS user_file (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '用户ID，关联 account 表',
    test_file CHAR(36) NULL COMMENT '测试文件UUID',
    resume_file CHAR(36) NULL COMMENT '简历文件UUID'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户文件表';

-- 创建索引以提高查询性能
CREATE INDEX idx_test_file ON user_file(test_file);
CREATE INDEX idx_resume_file ON user_file(resume_file);
