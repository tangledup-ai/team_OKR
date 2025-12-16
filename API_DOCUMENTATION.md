# OKR Performance System API Documentation

## 概述

团队OKR任务看板和绩效得分系统是一个综合性的团队管理平台API，用于跟踪任务进度、计算团队和个人绩效得分，并生成月度报告。

## 基础信息

- **Base URL**: `http://localhost:8000/api/`
- **认证方式**: JWT (JSON Web Token)
- **数据格式**: JSON
- **字符编码**: UTF-8

## 认证

### 获取访问令牌

```http
POST /api/users/login/
Content-Type: application/json

{
    "email": "user@example.com",
    "password": "your_password"
}
```

**响应示例**:
```json
{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "email": "user@example.com",
        "name": "张三",
        "department": "software",
        "role": "member"
    }
}
```

### 使用访问令牌

在所有需要认证的API请求中，在请求头中添加：

```http
Authorization: Bearer <your_access_token>
```

## API 模块

### 1. 用户管理 (Users)

#### 用户认证
- `POST /users/login/` - 用户登录
- `POST /users/register/` - 注册新成员（仅管理员）

#### 用户信息管理
- `GET /users/` - 获取团队成员列表
- `GET /users/{id}/` - 获取成员详情
- `PUT /users/{id}/` - 更新成员信息（管理员）
- `PATCH /users/{id}/` - 部分更新成员信息（管理员）
- `GET /users/me/` - 获取当前用户信息
- `GET /users/by-department/{department}/` - 按部门查询成员

#### 工作小时管理
- `GET /users/work-hours/` - 获取工作小时记录
- `POST /users/work-hours/` - 创建工作小时记录（管理员）
- `GET /users/work-hours/monthly-stats/` - 获取月度工作小时统计
- `POST /users/work-hours/batch-create/` - 批量创建工作小时记录

### 2. 任务管理 (Tasks)

#### 任务基础操作
- `GET /tasks/` - 获取任务列表
- `POST /tasks/` - 创建新任务
- `GET /tasks/{id}/` - 获取任务详情
- `PUT /tasks/{id}/` - 更新任务
- `PATCH /tasks/{id}/` - 部分更新任务

#### 任务状态管理
- `PATCH /tasks/{id}/update_status/` - 更新任务状态
- `GET /tasks/by_status/` - 按状态分组获取任务
- `GET /tasks/stats/` - 获取用户任务统计

#### 分值管理
- `POST /tasks/{id}/calculate_score/` - 计算任务分值分配
- `GET /tasks/{id}/score_distribution/` - 获取任务分值分配
- `GET /score-distributions/` - 获取分值分配列表
- `GET /score-allocations/` - 获取用户分值分配明细

### 3. 评价系统 (Reviews)

#### 任务评价
- `POST /reviews/task-review/` - 提交任务评价
- `GET /reviews/task-reviews/{task_id}/` - 获取任务的所有评价
- `GET /reviews/task-summary/{task_id}/` - 获取任务评价汇总

#### 月度评价
- `POST /reviews/monthly-review/` - 提交月度评价
- `GET /reviews/monthly-reviews/` - 获取月度评价列表

#### 个人评价记录
- `GET /reviews/my-reviews/` - 获取当前用户的评价记录
- `GET /reviews/received-reviews/` - 获取当前用户收到的评价

### 4. 报告系统 (Reports)

#### 月度综合评价
- `POST /reports/monthly-evaluations/self-evaluation/` - 提交自我评价
- `POST /reports/monthly-evaluations/peer-evaluation/` - 提交他人评价
- `PATCH /reports/monthly-evaluations/{id}/admin-evaluation/` - 管理员最终评价
- `GET /reports/monthly-evaluations/summary/` - 获取月度评价汇总

#### 管理员功能
- `GET /reports/monthly-evaluations/admin-view-all/` - 管理员查看所有评价
- `POST /reports/monthly-evaluations/batch-admin-evaluation/` - 批量管理员评价
- `GET /reports/monthly-evaluations/admin-history/` - 获取管理员评价历史

## 数据模型

### 用户 (User)
```json
{
    "id": "uuid",
    "email": "string",
    "name": "string",
    "department": "hardware|software|marketing",
    "role": "admin|member",
    "is_active": "boolean",
    "created_at": "datetime",
    "updated_at": "datetime"
}
```

### 任务 (Task)
```json
{
    "id": "uuid",
    "title": "string",
    "description": "string",
    "difficulty_score": "integer (1-10)",
    "revenue_amount": "decimal",
    "status": "todo|in_progress|completed|postponed",
    "owner": "User object",
    "collaborators": ["User objects"],
    "created_by": "User object",
    "created_at": "datetime",
    "started_at": "datetime",
    "completed_at": "datetime",
    "postponed_at": "datetime",
    "postpone_reason": "string"
}
```

### 评价 (Review)
```json
{
    "id": "uuid",
    "type": "task|monthly",
    "task": "uuid",
    "reviewee": "uuid",
    "reviewer": "User object",
    "rating": "integer (1-10)",
    "comment": "string",
    "is_anonymous": "boolean",
    "month": "date",
    "created_at": "datetime"
}
```

## 使用示例

### 创建任务
```http
POST /api/tasks/
Authorization: Bearer <token>
Content-Type: application/json

{
    "title": "开发用户认证模块",
    "description": "实现JWT认证和权限管理",
    "difficulty_score": 8,
    "revenue_amount": "5000.00",
    "owner_id": "123e4567-e89b-12d3-a456-426614174000",
    "collaborator_ids": [
        "456e7890-e89b-12d3-a456-426614174001"
    ]
}
```

### 更新任务状态
```http
PATCH /api/tasks/123e4567-e89b-12d3-a456-426614174000/update_status/
Authorization: Bearer <token>
Content-Type: application/json

{
    "status": "completed"
}
```

### 提交任务评价
```http
POST /api/reviews/task-review/
Authorization: Bearer <token>
Content-Type: application/json

{
    "task": "123e4567-e89b-12d3-a456-426614174000",
    "rating": 9,
    "comment": "任务完成质量很高，代码规范",
    "is_anonymous": false
}
```

### 提交自我评价
```http
POST /api/reports/monthly-evaluations/self-evaluation/
Authorization: Bearer <token>
Content-Type: application/json

{
    "month": "2024-01-01",
    "culture_understanding_score": 8,
    "culture_understanding_text": "深入理解公司文化价值观",
    "culture_understanding_option": "积极践行",
    "team_fit_option": "很好融入",
    "team_fit_text": "与团队协作顺畅",
    "team_fit_ranking": [
        "456e7890-e89b-12d3-a456-426614174001",
        "789e0123-e89b-12d3-a456-426614174002"
    ],
    "monthly_growth_score": 7,
    "monthly_growth_text": "技术能力有所提升",
    "monthly_growth_option": "持续学习",
    "biggest_contribution_score": 9,
    "biggest_contribution_text": "完成了核心认证模块",
    "biggest_contribution_option": "技术突破"
}
```

## 错误处理

API使用标准HTTP状态码：

- `200 OK` - 请求成功
- `201 Created` - 资源创建成功
- `400 Bad Request` - 请求参数错误
- `401 Unauthorized` - 未认证
- `403 Forbidden` - 权限不足
- `404 Not Found` - 资源不存在
- `500 Internal Server Error` - 服务器内部错误

错误响应格式：
```json
{
    "field_name": ["错误信息"],
    "non_field_errors": ["通用错误信息"]
}
```

## 分页

列表API支持分页，默认每页20条记录：

```http
GET /api/tasks/?page=2
```

响应格式：
```json
{
    "count": 100,
    "next": "http://localhost:8000/api/tasks/?page=3",
    "previous": "http://localhost:8000/api/tasks/?page=1",
    "results": [...]
}
```

## 过滤和搜索

支持多种过滤参数：

```http
GET /api/tasks/?status=completed&difficulty_score=8
GET /api/users/work-hours/?month=2024-01&department=software
GET /api/reviews/?type=task&month=2024-01-01
```

## 权限说明

- **管理员 (admin)**: 拥有完整系统权限
  - 注册新成员
  - 录入工作小时
  - 查看所有评价和报告
  - 提交最终评价

- **团队成员 (member)**: 基础权限
  - 查看和管理自己参与的任务
  - 提交任务评价和月度评价
  - 查看自己的报告和统计

## 最佳实践

1. **认证令牌管理**
   - 定期刷新访问令牌
   - 安全存储令牌信息

2. **错误处理**
   - 检查HTTP状态码
   - 处理验证错误信息

3. **数据验证**
   - 客户端进行基础验证
   - 处理服务端验证错误

4. **性能优化**
   - 使用分页避免大量数据传输
   - 合理使用过滤参数

## 联系支持

如有API使用问题，请联系：
- 邮箱: support@okr-system.com
- 文档: https://www.okr-system.com/docs