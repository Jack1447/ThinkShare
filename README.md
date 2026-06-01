<img src="static/img/logo.png" alt="logo" style="zoom:150%;" />


基于 Flask + PostgreSQL 的全功能校园社区论坛，支持发帖、评论、实时聊天、好友系统、管理后台等。

- 🌐 **线上地址**：[https://thinkshare-yvav.onrender.com](https://thinkshare-yvav.onrender.com)
- 📦 **GitHub**：[Jack1447/ThinkShare](https://github.com/Jack1447/ThinkShare)

---

## 一、功能一览

| 模块 | 功能 |
|---|---|
| 用户系统 | 注册/登录（输入验证），头像上传，昵称修改 |
| 论坛 | 分类浏览（日常/新闻/学术/二手），Markdown 发帖，图片拖拽上传，分页（每页 25 条） |
| 帖子交互 | 评论/回复（嵌套），点赞，收藏，浏览计数 |
| 帖子置顶 | 管理员可将帖子置顶，置顶帖始终排在最前 |
| 搜索 | 搜索帖子（标题+内容，板块+时间筛选），搜索用户（昵称） |
| 实时聊天 | WebSocket 实时消息，短时聊天（10条限制），好友无限聊天，图片发送 |
| 社交 | 关注/取关，好友请求/同意/拒绝，粉丝发帖通知 |
| 通知 | 评论、回复、好友请求、举报结果等系统通知 |
| 举报 | 用户举报违规帖子/评论（违规内容/人身攻击/广告骚扰），管理员在后台审核处理，通知举报双方 |
| 个人主页 | 帖子/收藏/关注/粉丝/好友/短时联系人/隐私设置 |
| 管理后台 | 网站统计、用户列表（封禁/解封）、帖子管理（表格展示/删除）、举报管理（处理/忽略） |
| 隐私控制 | 帖子、收藏、关注的可见性开关 + 短时聊天/好友请求权限 |
| 性能 | 分页、数据库索引、N+1 查询优化（joinedload 预加载） |

---

## 二、项目结构

```
campus_forum/
├── forum_pkg/
│   ├── __init__.py       # 应用工厂，Cloudinary/SocketIO 初始化，自动迁移
│   ├── config.py         # 配置分离（开发/生产）
│   ├── models.py         # 数据模型（10 个表）
│   └── routes/           # 路由模块（重构拆分）
│       ├── auth.py       #   登录/注册/登出
│       ├── forum.py      #   论坛/帖子/评论/搜索
│       ├── chat.py       #   WebSocket 聊天/好友
│       ├── user.py       #   个人主页/用户主页/关注/通知
│       └── admin.py      #   管理后台
├── static/
│   ├── css/style.css     # 全局样式
│   └── img/              # 默认头像
├── templates/            # Jinja2 模板
├── .env                  # 本地环境变量（不入库）
├── requirements.txt      # 依赖清单
├── run.py                # 开发入口
└── README.md
```

---

## 三、技术栈

| 层级 | 技术 |
|---|---|
| 后端框架 | Flask 3.x |
| 实时通信 | Flask-SocketIO + WebSocket |
| 数据库 | PostgreSQL（生产）/ SQLite（开发） |
| ORM | Flask-SQLAlchemy |
| 文件存储 | Cloudinary 云存储 |
| 生产服务器 | Gunicorn（gthread 多线程） |
| 部署平台 | Render.com |
| 版本控制 | Git + GitHub |

---

## 四、本地开发

```bash
conda activate se
pip install -r requirements.txt
python run.py
```

访问 `http://127.0.0.1:5000`

### 配置 .env

在项目根目录创建 `.env` 文件：

```
SECRET_KEY=campus_forum_secret_key_2024
CLOUDINARY_URL=cloudinary://你的API_Key:你的API_Secret@你的Cloud_Name
```

---

## 五、Cloudinary 文件存储

### 为什么需要 Cloudinary

Render 免费版没有持久磁盘，每次部署 `static/uploads/` 会被清空。所有用户上传（头像、帖子图片、聊天文件）存储在 Cloudinary 云端，数据库只存 URL。

### 注册

1. 打开 [Cloudinary](https://cloudinary.com) → **Sign Up for Free**，用 GitHub 或 Google 登录
2. 注册后在 Dashboard 获取三个凭证：**Cloud Name**、**API Key**、**API Secret**
3. 拼成一行：`cloudinary://API_Key:API_Secret@Cloud_Name`，写入 `.env` 的 `CLOUDINARY_URL`

### 日常使用

登录 Cloudinary → **Media Library** 可浏览所有已上传的文件。**Usage** 页面查看存储和流量使用（免费额度 25GB）。

---

## 六、部署到 Render.com

### 1. 推送到 GitHub

```bash
git init
git remote add origin https://github.com/Jack1447/ThinkShare.git
git add .
git commit -m "初始提交"
git push -u origin main
```

### 2. 创建 Web Service

1. 登录 [Render.com](https://render.com)，用 GitHub 登录
2. **New +** → **Web Service**，关联 `Jack1447/ThinkShare`
3. 配置：

| 配置项 | 值 |
|---|---|
| Name | thinkshare |
| Region | Singapore |
| Branch | main |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `gunicorn run:app --worker-class gthread --threads 4 -w 1` |
| Health Check Path | `/login` |
| Instance Type | Free |

### 3. 创建 PostgreSQL 数据库

1. **New +** → **PostgreSQL**

| 配置项 | 值 |
|---|---|
| Name | thinkshare-db |
| Database | thinkshare |
| User | thinkshare |
| Region | Singapore |
| Instance Type | Free |

### 4. 配置环境变量

在 Web Service → **Environment** 添加：

| Key | Value |
|---|---|
| `DATABASE_URL` | 数据库的 Internal Database URL |
| `SECRET_KEY` | 任意复杂字符串 |
| `CLOUDINARY_URL` | Cloudinary 的完整 URL |

点 **Save Changes**，Render 自动重新部署。

### 5. 设置管理员

由于免费版不支持 Shell，通过本地连接远程数据库：

```powershell
$env:DATABASE_URL="数据库的External Database URL"; conda activate se; python -c "from forum_pkg import create_app; from forum_pkg.models import User, db; app = create_app(); app.app_context().push(); user = User.query.filter_by(username='你的用户名').first(); user.is_admin = True; db.session.commit()"
```

---

## 七、更新代码

```bash
git add .
git commit -m "描述改动"
git push
```

Render 自动检测 GitHub 推送并重新部署（Auto-Deploy）。

---

## 八、暂停与恢复

免费版有 750 小时/月额度。

| 操作 | 方法 |
|---|---|
| 暂停 | Web Service → **Suspend Web Service** |
| 恢复 | **Resume Web Service**（需等待几十秒冷启动） |

数据库和 Cloudinary 无需暂停，不消耗 Web Service 小时数。

---

## 九、数据库自动迁移

`__init__.py` 中实现了自动迁移：每次启动检查表结构，缺少的列自动添加。新增模型字段后**不需要手动删数据库**。

---

## 十、注意事项

1. Render 免费版 15 分钟无访问自动休眠，唤醒需 30-50 秒
2. 免费版无持久磁盘，文件全部走 Cloudinary 云存储
3. PostgreSQL 免费版 1GB 存储，90 天试用期
4. Cloudinary 免费版 25GB 存储 + 25GB/月流量
5. 密钥如暴露后，在对应平台轮换密码
