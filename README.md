# ThinkShare 校园交流平台

基于 Flask + PostgreSQL 的全功能校园社区论坛，支持发帖、评论、实时聊天、好友系统、管理后台等。

- 🌐 **线上地址**：[https://thinkshare-yvav.onrender.com](https://thinkshare-yvav.onrender.com)
- 📦 **GitHub**：[Jack1447/ThinkShare](https://github.com/Jack1447/ThinkShare)
- 📖 **部署指南**：[DEPLOY.md](./DEPLOY.md)

---

## ✨ 功能一览

| 模块 | 功能 |
|---|---|
| 🧑‍💻 用户系统 | 注册/登录，头像上传，昵称修改 |
| 📄 论坛 | 分类浏览（日常/新闻/学术/二手），Markdown 发帖，图片拖拽上传 |
| 💬 帖子交互 | 评论/回复（纯文本），点赞，收藏，浏览计数 |
| 🔍 搜索 | 搜索帖子（标题+内容，板块+时间筛选），搜索用户（昵称） |
| 💬 实时聊天 | **WebSocket 实时消息**，短时聊天（10条限制），好友无限聊天，图片发送 |
| 👥 社交 | 关注/取关，好友请求/同意/拒绝，粉丝发帖通知 |
| 🔔 通知 | 评论、回复、好友请求、短时消息等系统通知 |
| 🏠 个人主页 | 帖子/收藏/关注/粉丝/好友/短时联系人/隐私设置 |
| 🛡️ 管理后台 | 网站统计、用户列表、封禁/解封 |
| 🔒 隐私控制 | 帖子、收藏、关注的可见性开关 |

---

## 🏗️ 项目结构

```
campus_forum/
├── forum_pkg/
│   ├── __init__.py       # 应用工厂，Cloudinary/SocketIO 初始化，自动迁移
│   ├── config.py         # 配置分离（开发/生产）
│   ├── models.py         # 数据模型（9 个表）
│   └── routes/           # 路由模块（重构拆分）
│       ├── auth.py       #   登录/注册/登出
│       ├── forum.py      #   论坛/帖子/评论/搜索
│       ├── chat.py       #   WebSocket 聊天/好友
│       ├── user.py       #   个人主页/用户主页/关注/通知
│       └── admin.py      #   管理后台
├── static/
│   ├── css/style.css     # 全局样式
│   └── img/              # 默认头像
├── templates/            # Jinja2 模板（13 个，含 404/500/macros）
├── .env                  # 本地环境变量（不入库）
├── requirements.txt      # 依赖清单
├── run.py                # 开发入口
├── DEPLOY.md             # 详细部署指南
└── README.md
```

---

## 🚀 本地开发

```bash
conda activate se
pip install -r requirements.txt
python run.py
```

访问 `http://127.0.0.1:5000`

> 本地使用 SQLite，首次启动自动建表。需配置 `.env` 中的 `CLOUDINARY_URL` 才支持上传。

---

## 🛠️ 技术栈

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

## 📖 详细文档

完整的部署流程、Cloudinary 配置、管理员设置等请参阅 **[DEPLOY.md](./DEPLOY.md)**。

---

## ⚠️ 注意事项

- Render 免费版 15 分钟无访问自动休眠，唤醒需 30-50 秒
- 免费版无持久磁盘，文件全部走 Cloudinary 云存储
- PostgreSQL 免费版 1GB，Cloudinary 免费版 25GB
