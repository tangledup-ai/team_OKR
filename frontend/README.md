# OKR 任务看板前端

团队OKR任务看板和绩效得分系统的React前端应用。

## 功能特性

- 🔐 用户登录认证
- 📋 任务看板（四列布局：未完成、进行中、完成、推迟）
- 🖱️ 拖拽功能（React DnD）
- 📝 任务创建和编辑
- 👥 团队成员管理
- 💰 任务难度分值和变现金额
- 📊 任务状态管理

## 技术栈

- React 18
- React Router DOM
- React DnD (拖拽功能)
- Tailwind CSS
- Axios (API调用)
- Heroicons (图标)

## 开发环境启动

### 使用 Docker (推荐)

```bash
# 在项目根目录运行
docker-compose up frontend
```

### 本地开发

```bash
cd frontend
npm install
npm start
```

应用将在 http://localhost:3000 启动

## 项目结构

```
frontend/
├── public/
│   └── index.html
├── src/
│   ├── components/          # 可复用组件
│   │   ├── Header.js
│   │   ├── TaskCard.js
│   │   ├── TaskColumn.js
│   │   ├── TaskModal.js
│   │   ├── CreateTaskModal.js
│   │   └── PostponeReasonModal.js
│   ├── contexts/           # React Context
│   │   └── AuthContext.js
│   ├── pages/              # 页面组件
│   │   ├── LoginPage.js
│   │   └── TaskBoard.js
│   ├── services/           # API服务
│   │   ├── api.js
│   │   └── taskService.js
│   ├── App.js
│   ├── index.js
│   └── index.css
├── package.json
└── Dockerfile
```

## API 集成

前端通过 Axios 与 Django REST API 集成：

- 认证：JWT Token
- 任务管理：CRUD 操作
- 用户管理：获取团队成员信息
- 自动 Token 刷新

## 环境变量

- `REACT_APP_API_URL`: 后端API地址 (默认: http://localhost:8000)

## 构建生产版本

```bash
npm run build
```

构建文件将生成在 `build/` 目录中。