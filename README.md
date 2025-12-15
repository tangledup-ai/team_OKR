# 团队OKR任务看板和绩效得分系统

## 项目简介

团队OKR任务看板和绩效得分系统是一个综合性的团队管理平台，用于跟踪任务进度、计算团队和个人绩效得分，并生成月度报告。

## 技术栈

- **后端**: Django 4.2 + Django REST Framework
- **数据库**: PostgreSQL
- **认证**: JWT (djangorestframework-simplejwt)
- **API文档**: Swagger/OpenAPI (drf-yasg)
- **管理界面**: Django Admin + django-admin-interface
- **部署**: Docker + Docker Compose

## 快速开始

### 1. 环境准备

确保已安装以下软件：
- Python 3.11+
- Docker & Docker Compose
- PostgreSQL客户端（可选）

### 2. 克隆项目

```bash
git clone <repository-url>
cd team-okr-performance-system
```

### 3. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，配置数据库连接等信息
```

### 4. 使用Docker启动（推荐）

```bash
# 构建并启动服务
docker-compose up --build

# 在另一个终端执行数据库迁移
docker-compose exec web python manage.py migrate

# 创建超级管理员
docker-compose exec web python manage.py createsuperuser
```

### 5. 本地开发环境

如果不使用Docker，可以按以下步骤设置：

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 执行数据库迁移
python manage.py migrate

# 创建超级管理员
python manage.py createsuperuser

# 启动开发服务器
python manage.py runserver
```

## 访问应用

- **API文档 (Swagger)**: http://localhost:8000/swagger/
- **API文档 (ReDoc)**: http://localhost:8000/redoc/
- **Django Admin**: http://localhost:8000/admin/
- **API根路径**: http://localhost:8000/api/

## 项目结构

```
.
├── config/                 # Django配置
│   ├── settings.py        # 项目设置
│   ├── urls.py            # URL路由
│   ├── wsgi.py            # WSGI配置
│   └── asgi.py            # ASGI配置
├── apps/                   # 应用模块
│   ├── users/             # 用户管理
│   ├── tasks/             # 任务管理
│   ├── reviews/           # 评价系统
│   └── reports/           # 报告生成
├── requirements.txt        # Python依赖
├── Dockerfile             # Docker镜像配置
├── docker-compose.yml     # Docker Compose配置
└── manage.py              # Django管理脚本
```

## 数据库配置

项目使用外部PostgreSQL数据库：

- **主机**: 121.43.104.161:6432
- **数据库**: OKR
- **用户名**: OKR
- **密码**: 123OKR

## 开发指南

### 创建数据库迁移

```bash
python manage.py makemigrations
python manage.py migrate
```

### 运行测试

```bash
python manage.py test
```

### 收集静态文件

```bash
python manage.py collectstatic
```

## API认证

系统使用JWT进行认证。获取令牌的步骤：

1. 登录获取访问令牌：
```bash
POST /api/users/login/
{
    "email": "user@example.com",
    "password": "password"
}
```

2. 使用令牌访问受保护的API：
```bash
Authorization: Bearer <access_token>
```

3. 刷新令牌：
```bash
POST /api/users/token/refresh/
{
    "refresh": "<refresh_token>"
}
```

## 部署

### 生产环境部署

1. 修改 `.env` 文件，设置生产环境配置
2. 设置 `DEBUG=False`
3. 配置 `SECRET_KEY` 为安全的随机字符串
4. 配置 `ALLOWED_HOSTS`
5. 使用 `gunicorn` 作为WSGI服务器

```bash
docker-compose -f docker-compose.prod.yml up -d
```

## 许可证

[待定]

## 联系方式

[待定]
