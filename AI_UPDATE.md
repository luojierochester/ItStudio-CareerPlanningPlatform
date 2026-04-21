# AI 简历实时更新功能说明

## 功能概述

实现了用户通过与 AI 对话实时创建和更新简历的功能。AI 会主动提问引导用户补充简历信息，并自动将对话内容同步到全息简历模型中。

## 主要改动

### 1. AI 提示词优化

#### Agent01.md（已上传简历的用户）

- **简短对话**：每次回复控制在 2-3 句话，一次只问 1 个问题
- **主动引导**：通过提问挖掘用户的经历和亮点
- **话题保护**：严格限制在职业规划相关话题，拒绝无关内容
- **实时更新**：使用 `[UPDATE_RESUME]` 指令格式输出简历更新

#### Agent02.md（未上传简历的用户）

- **循序渐进**：按顺序收集信息（基本信息→教育→技能→项目→目标）
- **简短对话**：每次只问 1 个问题，避免用户压力
- **话题保护**：只讨论职业规划相关内容
- **实时构建**：每收集到信息就立即更新简历

### 2. AI 服务改动 (aIInterface/src/fastapi_server.py)

#### 新增功能

- **降低温度参数**：从 0.7 降至 0.3，提高生成内容的一致性和聚焦度
- **简历更新指令解析**：`parse_resume_update_commands()` 函数解析 AI 输出中的更新指令
- **简历更新应用**：`apply_resume_updates()` 函数调用后端 API 应用更新
- **实时更新**：在 WebSocket 流式输出时自动解析并应用更新

#### 更新指令格式

```json

[UPDATE_RESUME]
{
  "action": "add|update|delete",
  "section": "name|education|skills|projects|targetRole",
  "content": {具体内容}
}
[/UPDATE_RESUME]
```

### 3. 后端改动

#### ResumeController.kt

新增接口：

```kotlin
POST /api/v1/resume/update
```

用于接收 AI 服务发送的简历更新请求。

#### ResumeService.kt

新增方法：

- `updateResume()`：处理简历更新请求
- `applyResumeUpdate()`：应用具体的更新操作（增删改）
- `resumeToText()`：将简历对象转换为文本格式缓存到 Redis

支持的操作：

- **name/targetRole/education**：直接更新
- **skills**：支持 add（追加）、update（替换）、delete（删除）
- **projects**：支持 add（追加项目）、update（替换所有）、delete（删除指定项目）

## 使用流程

### 场景 1：用户已上传简历（Agent01）

1. 用户上传简历后，AI 分析简历内容
2. AI 主动提问挖掘细节：
   - "这个项目中你主要负责什么？"
   - "用了哪些技术栈？"
3. 用户回答后，AI 自动更新简历：

   ```json
   [UPDATE_RESUME]
   {"action": "add", "section": "skills", "content": ["React", "Spring Boot"]}
   [/UPDATE_RESUME]
   ```

4. 前端全息简历模型实时显示更新

### 场景 2：用户未上传简历（Agent02）

1. AI 按顺序引导用户创建简历：
   - "你好！先告诉我你叫什么名字？"
   - "你在哪所学校读书？什么专业？"
   - "你掌握哪些编程语言或技术？"
2. 每收集到信息就立即更新：

   ```json
   [UPDATE_RESUME]
   {"action": "update", "section": "name", "content": "张三"}
   [/UPDATE_RESUME]
   ```

3. 简历逐步完善，实时显示在前端

## 话题保护机制

### 允许讨论的话题

- 教育背景、专业、课程
- 技能、工具、编程语言
- 项目经验、实习经历
- 职业目标、求职意向
- 简历优化、面试准备

### 禁止讨论的话题

- 个人情感、生活琐事
- 娱乐、游戏、八卦
- 政治、宗教、敏感话题
- 与职业规划无关的任何内容

### 处理方式

当用户提出无关话题时，AI 会礼貌回应：
> "让我们聚焦在你的职业发展上。[转回职业话题的问题]"

## 技术细节

### 温度参数调整

- **原值**：0.7（较高创造性，但可能偏离主题）
- **新值**：0.3（更聚焦、更一致、更可控）

### 数据流

```
用户输入 → AI 生成回复（含更新指令）
         ↓
    解析更新指令
         ↓
    调用后端 API (/api/v1/resume/update)
         ↓
    更新 Redis 缓存
         ↓
    前端轮询或 WebSocket 推送
         ↓
    全息简历模型实时更新
```

### Redis 缓存键

- 简历文本：`resume:text:{accountId}`
- 存储格式：纯文本（便于 AI 读取和更新）

## 部署说明

### 1. 更新 AI 服务

```bash
cd aIInterface
# 确保安装了 httpx 依赖
pip install httpx
# 重启服务
python src/fastapi_server.py
```

### 2. 更新后端服务

```bash
cd backend
# 重新编译
./gradlew build
# 重启服务
```

### 3. 环境变量配置

在 AI 服务中添加：

```bash
export BACKEND_API_URL="http://localhost:8080/api"
```

## 测试建议

### 测试用例 1：技能添加

- 用户："我会 Python 和 Java"
- 预期：简历的技能部分增加 Python 和 Java

### 测试用例 2：项目添加

- 用户："我做过一个电商网站项目，用的 Vue 和 Spring Boot"
- 预期：简历的项目部分增加该项目

### 测试用例 3：话题保护

- 用户："你觉得最近的电影好看吗？"
- 预期：AI 拒绝讨论并引导回职业话题

### 测试用例 4：循序渐进（Agent02）

- 验证 AI 是否按顺序提问（姓名→教育→技能→项目）
- 验证每次只问 1 个问题

## 注意事项

1. **数据库表结构**：确保 `user_file` 表已正确创建（包含 `id`、`test_file`、`resume_file` 字段）
2. **Redis 连接**：确保 AI 服务能连接到 Redis
3. **后端 API**：确保后端服务正常运行且 `/api/v1/resume/update` 接口可访问
4. **认证**：AI 服务调用后端 API 时需要传递用户的 JWT token

## 未来优化方向

1. **WebSocket 推送**：后端更新简历后通过 WebSocket 主动推送给前端，无需轮询
2. **版本控制**：记录简历的修改历史，支持撤销操作
3. **AI 建议**：AI 主动发现简历不足并给出优化建议
4. **多轮对话优化**：根据用户回答质量动态调整提问策略
