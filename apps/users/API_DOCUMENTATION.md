# User Authentication API Documentation

## Overview

This document describes the User Authentication and Management API endpoints for the OKR Performance System.

## Base URL

All endpoints are prefixed with `/api/users/`

## Authentication

Most endpoints require JWT authentication. Include the access token in the Authorization header:

```
Authorization: Bearer <access_token>
```

## Endpoints

### 1. User Login

**Endpoint:** `POST /api/users/auth/login/`

**Description:** Authenticate a user and receive JWT tokens

**Authentication:** Not required

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response (200 OK):**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "email": "user@example.com",
    "name": "张三",
    "department": "software",
    "role": "member"
  }
}
```

**Error Responses:**
- `400 Bad Request`: Missing required fields
- `401 Unauthorized`: Invalid credentials

---

### 2. Token Refresh

**Endpoint:** `POST /api/users/auth/token/refresh/`

**Description:** Refresh an expired access token using a refresh token

**Authentication:** Not required

**Request Body:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response (200 OK):**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

---

### 3. Register User (Admin Only)

**Endpoint:** `POST /api/users/auth/register/`

**Description:** Register a new team member (admin only)

**Authentication:** Required (Admin role)

**Request Body:**
```json
{
  "email": "newuser@example.com",
  "name": "新用户",
  "department": "software",
  "role": "member",
  "password": "password123",
  "password_confirm": "password123"
}
```

**Department Options:**
- `hardware` - 硬件部门
- `software` - 软件部门
- `marketing` - 市场部门

**Role Options:**
- `admin` - 管理员
- `member` - 成员

**Response (201 Created):**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "newuser@example.com",
  "name": "新用户",
  "department": "software",
  "role": "member",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

**Error Responses:**
- `400 Bad Request`: Validation errors (password mismatch, invalid department, etc.)
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Not an admin user

---

### 4. List Users

**Endpoint:** `GET /api/users/`

**Description:** Get a list of all team members

**Authentication:** Required

**Query Parameters:**
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 20)

**Response (200 OK):**
```json
{
  "count": 10,
  "next": "http://api.example.com/api/users/?page=2",
  "previous": null,
  "results": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "email": "user@example.com",
      "name": "张三",
      "department": "software",
      "role": "member",
      "is_active": true,
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

---

### 5. Get User Detail

**Endpoint:** `GET /api/users/{user_id}/`

**Description:** Get detailed information about a specific user

**Authentication:** Required

**Response (200 OK):**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "name": "张三",
  "department": "software",
  "role": "member",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "last_login": "2024-01-20T14:25:00Z"
}
```

**Error Responses:**
- `401 Unauthorized`: Not authenticated
- `404 Not Found`: User does not exist

---

### 6. Update User (Admin Only)

**Endpoint:** `PATCH /api/users/{user_id}/`

**Description:** Update user information (admin only)

**Authentication:** Required (Admin role)

**Request Body (all fields optional):**
```json
{
  "name": "更新后的名字",
  "department": "hardware",
  "role": "admin",
  "is_active": false
}
```

**Response (200 OK):**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "name": "更新后的名字",
  "department": "hardware",
  "role": "admin",
  "is_active": false,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-20T15:30:00Z"
}
```

**Error Responses:**
- `400 Bad Request`: Validation errors
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Not an admin user
- `404 Not Found`: User does not exist

---

### 7. Delete User (Admin Only)

**Endpoint:** `DELETE /api/users/{user_id}/`

**Description:** Delete a user (admin only)

**Authentication:** Required (Admin role)

**Response (204 No Content):** Empty response body

**Error Responses:**
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Not an admin user
- `404 Not Found`: User does not exist

---

## Testing

### Test Users

Use the management command to create test users:

```bash
python manage.py create_test_users
```

This creates:
- Admin: `admin@example.com` / `admin123`
- Software: `software@example.com` / `user123`
- Hardware: `hardware@example.com` / `user123`
- Marketing: `marketing@example.com` / `user123`

### Running Tests

```bash
# Run all user tests
python manage.py test apps.users

# Run specific test file
python manage.py test apps.users.tests
python manage.py test apps.users.test_integration
```

## API Documentation

Interactive API documentation is available at:
- Swagger UI: `http://localhost:8000/swagger/`
- ReDoc: `http://localhost:8000/redoc/`

## Error Handling

All error responses follow this format:

```json
{
  "detail": "Error message",
  "code": "error_code"
}
```

Or for validation errors:

```json
{
  "field_name": ["Error message for this field"],
  "another_field": ["Another error message"]
}
```

## Requirements Validation

This implementation satisfies the following requirements:

- **需求 1.1**: 管理员创建新团队成员账户 ✓
- **需求 1.2**: 部门选择（硬件、软件、市场） ✓
- **需求 1.3**: 生成唯一成员ID ✓
- **需求 1.4**: 查看成员列表 ✓
- **需求 1.5**: 修改成员信息 ✓
- **需求 2.1**: 邮箱和密码认证 ✓
- **需求 2.5**: 无效凭证拒绝 ✓
