# ThinkShare 校园交流平台 — 部署指南

## 项目概述

基于 Flask + PostgreSQL 的校园论坛系统，部署于 Render.com 免费版。

- **线上地址**：`https://thinkshare-yvav.onrender.com`
- **GitHub 仓库**：`https://github.com/Jack1447/ThinkShare`
- **管理员**：Regular_Hexagon（Thanos）

---

## 功能清单

| 功能 | 说明 |
|---|---|
| 注册/登录 | 支持头像上传 |
| 论坛首页 | 分类浏览（日常/新闻/学术/二手），热帖排行，统计数据 |
| 发帖 | SimpleMDE Markdown 编辑器，支持图片拖拽上传 |
| 帖子详情 | Markdown 渲染，评论/回复（纯文本），点赞/收藏 |
| 搜索 | 搜索帖子（标题+内容，支持板块和时间筛选）和用户（昵称） |
| 关注系统 | 关注/取消关注，发布帖子通知粉丝 |
| 聊天 | 短时聊天（10条限制）+ 长时好友聊天（无限），好友聊天支持图片上传 |
| 好友系统 | 好友请求/同意/拒绝 |
| 通知系统 | 评论、回复、好友请求、短时消息等通知 |
| 个人主页 | 头像/昵称修改，帖子/收藏/关注/粉丝/好友/隐私设置 |
| 管理后台 | 网站统计，用户列表，封禁/解封用户 |
| 隐私控制 | 控制帖子、收藏、关注的可见性 |

---

## 技术栈

| 层级 | 技术 |
|---|---|
| 后端框架 | Flask 3.x |
| 数据库 | PostgreSQL（生产环境）/ SQLite（本地开发） |
| ORM | Flask-SQLAlchemy |
| 文件存储 | Cloudinary（云存储，头像、帖子图片、聊天文件） |
| 生产服务器 | Gunicorn |
| 环境变量 | python-dotenv + Render 环境变量 |
| 部署平台 | Render.com |
| 版本控制 | Git + GitHub |

---

## 项目结构

```
campus_forum/
├── forum_pkg/
│   ├── __init__.py      # 应用工厂，数据库初始化，Cloudinary 配置，自动迁移
│   ├── models.py        # 数据模型（9 个表 + 辅助函数）
│   └── routes.py        # 所有路由（~30 个）
├── static/
│   ├── css/style.css    # 全局样式
│   ├── img/default_avatar.svg
│   └── uploads/         # 本地开发时的上传目录（部署后由 Cloudinary 替代）
├── templates/           # Jinja2 模板（12 个，含 search.html）
├── .env                 # 本地环境变量（不提交到 Git）
├── .gitignore           # 排除敏感文件和缓存
├── requirements.txt     # 依赖清单
├── run.py               # 开发环境启动入口
└── DEPLOY.md            # 本文档
```

---

## 本地开发

### 环境准备

```bash
conda activate se
```

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置 .env

在项目根目录创建 `.env` 文件：

```
SECRET_KEY=campus_forum_secret_key_2024
CLOUDINARY_URL=cloudinary://你的API_Key:你的API_Secret@你的Cloud_Name
```

### 启动开发服务器

```bash
python run.py
```

访问 `http://127.0.0.1:5000`

### 本地数据库

本地使用 SQLite，数据库文件 `campus.db` 存放在项目根目录。启动时自动创建表结构。

---

## 文件存储方案（Cloudinary）

### 为什么使用 Cloudinary

- Render 免费版没有持久磁盘，每次重新部署 `static/uploads/` 会被清空
- 用户上传的头像、帖子图片、聊天文件全部存储在 Cloudinary 云端
- 数据库中只存储文件的 URL，访问时直接从 Cloudinary CDN 加载

### 注册 Cloudinary

1. 打开 https://cloudinary.com
2. 点击 **Sign Up for Free**，用 GitHub 或 Google 登录
3. 注册后在 Dashboard 看到三个关键信息：
   - **Cloud Name**（如 `djgz0ifxv`）
   - **API Key**（如 `696845487384931`）
   - **API Secret**

### 使用 Cloudinary 网站

登录后进入 **Dashboard**，可以看到：

| 区域 | 作用 |
|---|---|
| **Media Library** | 浏览和搜索所有已上传的文件（图片、文档等） |
| **Transformations** | 对图片进行裁剪、压缩、加水印等处理 |
| **Settings → Upload** | 设置允许的文件类型、大小限制等 |
| **Settings → Security** | 管理 API 密钥，可轮换密码 |
| **Usage** | 查看存储使用量和流量消耗 |

日常只需偶尔去 Media Library 看看上传的文件，不需要特别操作。

### 代码中的使用方式

```python
# forum_pkg/__init__.py 中定义
import cloudinary
import cloudinary.uploader

cloudinary.config(cloudinary_url=os.environ.get('CLOUDINARY_URL'))

def upload_to_cloudinary(file):
    result = cloudinary.uploader.upload(file)
    return result['secure_url']

# routes.py 中调用
avatar_url = upload_to_cloudinary(file)
user.avatar = avatar_url  # 存的是 https://res.cloudinary.com/... 的 URL
```

---

## 部署流程（Render.com）

### 1. 推送到 GitHub

```bash
git init
git remote add origin https://github.com/Jack1447/ThinkShare.git
git add .
git commit -m "提交信息"
git push -u origin main
```

### 2. 在 Render 创建 Web Service

1. 登录 [Render.com](https://render.com)，使用 GitHub 账号登录
2. 点击 **New +** → **Web Service**
3. 关联仓库 `Jack1447/ThinkShare`
4. 配置参数：

| 配置项 | 值 |
|---|---|
| Name | thinkshare |
| Region | Singapore |
| Branch | main |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `gunicorn run:app` |
| Health Check Path | `/login` |
| Instance Type | Free |

### 3. 创建 PostgreSQL 数据库

1. 点击 **New +** → **PostgreSQL**
2. 配置：

| 配置项 | 值 |
|---|---|
| Name | thinkshare-db |
| Database | thinkshare |
| User | thinkshare |
| Region | Singapore（与 Web Service 同区） |
| Instance Type | Free |

### 4. 添加环境变量

进入 Web Service → **Environment**，添加以下变量：

| Key | Value |
|---|---|
| `DATABASE_URL` | 数据库的 Internal Database URL（从数据库页面复制） |
| `SECRET_KEY` | 任意复杂字符串（如 `thinkshare_secret_key_2024`） |
| `CLOUDINARY_URL` | Cloudinary 的 URL（如 `cloudinary://API_Key:API_Secret@Cloud_Name`） |

点击 **Save Changes**，Render 自动重新部署。

---

## 数据库自动迁移

项目在 `__init__.py` 中实现了自动迁移机制。每次启动时，代码会检查数据库表结构是否包含所需字段，如果缺少就自动添加。因此新增模型字段后**不需要手动删除数据库**，只需 `git push` 部署即可。

---

## 管理员设置

由于 Render 免费版不支持 Shell，通过本地连接远程数据库设置：

```powershell
$env:DATABASE_URL="数据库的External Database URL"; conda activate se; python -c "from forum_pkg import create_app; from forum_pkg.models import User, db; app = create_app(); app.app_context().push(); user = User.query.filter_by(username='用户名').first(); user.is_admin = True; db.session.commit()"
```

---

## 更新代码

修改本地代码后：

```bash
git add .
git commit -m "描述改了什么"
git push
```

Render 会自动检测 GitHub 推送并重新部署。

---

## 暂停与恢复

免费版有 750 小时/月的额度限制。

- **暂停**：进入 Web Service 页面 → 底部 **Suspend Web Service**
- **恢复**：点击 **Resume Web Service**（需等待几十秒冷启动）
- 数据库可以不暂停（免费版数据库不消耗 Web Service 小时数）
- Cloudinary 免费额度 25GB 存储 + 25GB/月流量，无需暂停

---

## .gitignore 说明

以下文件不会被提交到 GitHub：

| 文件 | 原因 |
|---|---|
| `.env` | 包含密钥和凭证 |
| `campus.db` | 本地 SQLite 数据库 |
| `__pycache__/` | Python 缓存 |
| `*.pyc` | 编译文件 |

---

## 注意事项

1. Render 免费版 15 分钟无访问后会自动休眠，下次访问需等待 30-50 秒冷启动
2. 免费版不支持 Shell 和 SSH 登录
3. 免费版不支持持久磁盘，必须使用 Cloudinary（文件）+ PostgreSQL（数据）
4. PostgreSQL 免费版 1GB 存储，90 天试用期
5. Cloudinary 免费版 25GB 存储 + 25GB/月流量
6. 数据库密码或 Cloudinary 密钥如暴露后，应在对应平台轮换密码
