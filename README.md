# AI儿童故事生成与互动系统

基于 **LLM + RAG + LangGraph 多Agent协作** 的AI儿童故事生成与互动系统。采用家庭主账号 + 儿童子账号模式，为儿童提供个性化、安全可控、可互动的故事体验。

## 技术栈

| 层 | 技术 |
|---|---|
| 前端 | Next.js 14+, TypeScript, Tailwind CSS, Zustand |
| 后端 | Python 3.11, FastAPI, SQLAlchemy, Pydantic |
| 数据库 | PostgreSQL, Redis, FAISS (向量检索) |
| AI | LangGraph (Agent编排), LangChain, OpenAI兼容API |
| Embedding | HuggingFace (BAAI/bge-small-zh-v1.5) |
| 部署 | Docker Compose |

## 系统架构

```
展示层: 家长端 Web UI + 儿童端 Web UI (Next.js)
     ↓
业务层: 账号管理 / 儿童档案 / 故事会话 / 成长报告 (FastAPI)
     ↓
AI层:  用户画像Agent → 故事规划Agent → RAG检索Agent → 
       故事生成Agent → 安全审核Agent → 互动控制Agent → 总结Agent
     ↓
数据层: PostgreSQL + Redis + FAISS
```

## 快速启动

### 方式一：本地开发

#### 1. 环境准备

```bash
# 安装 PostgreSQL 和 Redis（macOS）
brew install postgresql@16 redis
brew services start postgresql@16
brew services start redis

# 创建数据库
createdb storyagent
```

#### 2. 后端启动

```bash
cd backend

# 复制并配置环境变量
cp .env.example .env
# 编辑 .env 文件，配置 LLM_BASE_URL 和 LLM_API_KEY

# 安装依赖（使用 conda langgraph 环境）
conda activate langgraph
pip install -r requirements.txt

# 运行数据库迁移
alembic upgrade head

# 启动后端服务
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 3. 前端启动

```bash
cd frontend
npm install
npm run dev
```

访问：
- 前端: http://localhost:3000
- 后端API文档: http://localhost:8000/docs

### 方式二：Docker Compose

```bash
# 复制并配置环境变量
cp .env.example .env
# 编辑 .env

# 一键启动
docker-compose up --build
```

## 环境变量说明

| 变量 | 说明 | 示例 |
|---|---|---|
| `DATABASE_URL` | PostgreSQL 连接字符串 | `postgresql://localhost/storyagent` |
| `REDIS_URL` | Redis 连接字符串 | `redis://localhost:6379/0` |
| `SECRET_KEY` | JWT 签名密钥 | 随机字符串 |
| `LLM_BASE_URL` | LLM API 基础URL | `https://api.example.com/v1` |
| `LLM_API_KEY` | LLM API 密钥 | 你的API Key |
| `LLM_MODEL` | LLM 模型名称 | `qwen-plus` |
| `EMBEDDING_MODEL_NAME` | Embedding 模型 | `BAAI/bge-small-zh-v1.5` |

## 功能说明

### 家长端
- 注册/登录家庭主账号
- 创建/编辑儿童子账号（昵称、年龄、兴趣、阅读水平）
- 安全与偏好设置（屏蔽主题、偏好主题、每日时长限制）
- 查看儿童故事历史
- 查看AI生成的成长报告

### 儿童端
- 选择子账号进入个人故事空间
- 选择主题/主角/场景创建新故事
- 故事互动：每幕故事提供2-3个分支选项
- 故事结束后查看总结和鼓励

### AI能力
- **用户画像Agent**: 根据年龄和兴趣生成儿童画像
- **故事规划Agent**: 生成多幕故事大纲
- **RAG检索Agent**: 从知识库检索相关故事模板和教育主题
- **故事生成Agent**: 基于规划和RAG生成当前场景
- **安全审核Agent**: 双层过滤（规则+LLM），确保内容安全
- **互动控制Agent**: 处理儿童选择，推进剧情
- **总结Agent**: 生成故事总结和成长建议

## 数据库初始化

数据库表通过 Alembic 迁移自动创建：

```bash
cd backend
alembic upgrade head
```

重新生成迁移：

```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
```

## 项目结构

```
storyAgent/
├── backend/
│   ├── app/
│   │   ├── api/           # API路由
│   │   ├── core/          # 配置、安全、依赖注入
│   │   ├── models/        # SQLAlchemy 模型
│   │   ├── schemas/       # Pydantic 数据验证
│   │   ├── services/      # 业务逻辑
│   │   ├── agents/        # LangGraph Agent节点和工作流
│   │   ├── rag/           # RAG知识库管理
│   │   ├── utils/         # 工具类
│   │   ├── db/            # 数据库连接
│   │   └── main.py        # FastAPI入口
│   ├── rag_data/          # RAG种子数据
│   ├── alembic/           # 数据库迁移
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/           # Next.js页面
│   │   ├── services/      # API调用
│   │   ├── store/         # Zustand状态管理
│   │   └── types/         # TypeScript类型
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```
