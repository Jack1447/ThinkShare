# ThinkShare 校园交流平台

基于 Flask + React 的全功能校园社区论坛，支持发帖、评论、实时聊天、好友系统、管理后台等。

- 🌐 **线上地址**：[https://thinkshare-yvav.onrender.com](https://thinkshare-yvav.onrender.com)
- 📦 **GitHub**：[Jack1447/ThinkShare](https://github.com/Jack1447/ThinkShare)

> ℹ️ 本分支 (`react-frontend`) 使用 **React + Tailwind CSS + JWT** 前后端分离架构。旧的 Jinja2 模板版本在 [`main`](https://github.com/Jack1447/ThinkShare/tree/main) 分支。

---

## ✨ 功能一览

| 模块 | 功能 |
|---|---|
| 🧑‍💻 用户系统 | 注册/登录（JWT），头像上传，昵称修改 |
| 📄 论坛 | 分类浏览（日常/新闻/学术/二手），Markdown 发帖，图片上传 |
| 💬 帖子交互 | 评论/回复（树形嵌套），点赞，收藏，浏览计数 |
| 🔍 搜索 | 搜索帖子（标题+内容，板块+时间筛选），搜索用户（昵称） |
| 💬 实时聊天 | WebSocket 实时消息，短时聊天（10条限制），好友无限聊天 |
| 👥 社交 | 关注/取关，好友请求/同意/拒绝，粉丝发帖通知 |
| 🔔 通知 | 评论、回复、好友请求、短时消息等系统通知 |
| 🏠 个人主页 | 帖子/收藏/关注/粉丝/好友/短时联系人/隐私设置 |
| 🛡️ 管理后台 | 网站统计、用户列表、封禁/解封 |
| 🔒 隐私控制 | 帖子、收藏、关注的可见性开关 |

---

## 🏗️ 项目结构

```
campus_forum/
├── forum_pkg/               # Flask 后端
│   ├── __init__.py          # 应用工厂，JWT/CORS/Cloudinary/SocketIO 初始化
│   ├── config.py            # 配置分离（开发/生产）
│   ├── models.py            # 数据模型（9 个表）
│   └── routes/
│       ├── __init__.py      # 路由注册入口
│       └── api/             # REST API（JSON 响应）
│           ├── auth.py      #   JWT 登录/注册/获取当前用户
│           ├── forum.py     #   论坛/帖子CRUD/评论/点赞/收藏/搜索/上传
│           ├── user.py      #   个人主页/用户主页/关注/好友/通知/隐私
│           ├── chat.py      #   聊天/发送消息
│           └── admin.py     #   管理后台/封禁/解封
├── frontend/                # React 前端
│   ├── src/
│   │   ├── components/      # 通用组件（Navbar, PostCard, Toast...）
│   │   ├── contexts/        # AuthContext（JWT 状态管理）
│   │   ├── pages/           # 12 个页面
│   │   ├── services/        # Axios API 服务层
│   │   ├── App.jsx          # 路由配置
│   │   └── index.css        # Tailwind CSS + 自定义样式
│   ├── tailwind.config.js
│   └── vite.config.js       # 开发代理配置
├── static/
│   └── img/default_avatar.svg
├── requirements.txt
├── run.py                   # Flask 开发入口
└── README.md
```

---

## 🛠️ 技术栈

| 层级 | 技术 |
|---|---|
| 前端框架 | React 18 + Vite |
| 前端样式 | Tailwind CSS v3 |
| 前端路由 | React Router v6 |
| HTTP 请求 | Axios |
| 后端框架 | Flask 3.x + REST JSON API |
| 认证 | Flask-JWT-Extended（JWT Token） |
| 实时通信 | Flask-SocketIO + WebSocket |
| 数据库 | PostgreSQL（生产）/ SQLite（开发） |
| ORM | Flask-SQLAlchemy |
| 文件存储 | Cloudinary 云存储 |
| 生产服务器 | Gunicorn |
| 部署平台 | Render.com |

---

## 🚀 本地开发

需要两个终端：

```bash
# 终端1：启动 Flask 后端（5000端口）
conda activate se
pip install -r requirements.txt
python run.py

# 终端2：启动 React 前端（5173端口，自动代理 API 到 5000）
cd frontend
npm install
npm run dev
```

访问 `http://localhost:5173`

### 配置 .env

在项目根目录创建 `.env` 文件：

```
SECRET_KEY=campus_forum_secret_key_2024
CLOUDINARY_URL=cloudinary://你的API_Key:你的API_Secret@你的Cloud_Name
```

---

## ☁️ Cloudinary 文件存储

所有用户上传（头像、帖子图片、聊天文件）存储在 Cloudinary 云端，数据库只存 URL。

1. 打开 [Cloudinary](https://cloudinary.com) → **Sign Up for Free**
2. Dashboard 获取：**Cloud Name**、**API Key**、**API Secret**
3. 拼成：`cloudinary://API_Key:API_Secret@Cloud_Name`，写入 `.env`

---

## 🌐 部署到 Render.com

### 1. 推送到 GitHub

```bash
git push origin react-frontend
```

### 2. 创建 Web Service

1. [Render.com](https://render.com) → **New +** → **Web Service**
2. 关联 `Jack1447/ThinkShare`

配置：

| 配置项 | 值 |
|---|---|
| Branch | `react-frontend` |
| Build Command | `pip install -r requirements.txt && cd frontend && npm install && npm run build && cd ..` |
| Start Command | `gunicorn run:app --worker-class gthread --threads 4 -w 1` |
| Health Check Path | `/api/auth/login` |

### 3. 创建 PostgreSQL + 环境变量

与 main 分支相同：创建 PostgreSQL 数据库，配置 `DATABASE_URL`、`SECRET_KEY`、`CLOUDINARY_URL` 环境变量。

### ⚠️ React 静态文件

生产环境下 `__init__.py` 会自动检测 `frontend/dist/` 目录，将 React 打包文件作为静态资源提供服务。所有 `/api/` 请求走 Flask API，其他请求返回 React 的 `index.html`。

---

## 🔄 分支说明

| 分支 | 架构 | 前端 |
|---|---|---|
| [`main`](https://github.com/Jack1447/ThinkShare/tree/main) | Flask + Jinja2 模板 | 服务端渲染 |
| `react-frontend`（当前） | Flask REST API + React SPA | 客户端渲染 |
