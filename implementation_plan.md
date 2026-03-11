# 情绪感知 AI 伴侣 · 项目升级实施计划

目标：添加 SQLite 数据库持久化、Vue3 前端重构、历史情绪可视化分析功能。

## 架构概览

```
main/
├── database.py          [NEW] SQLAlchemy 引擎 + 初始化
├── models_db.py         [NEW] ORM 数据模型
├── server.py            [MODIFY] 整合数据库 + 新增 API
├── requirements.txt     [MODIFY] 添加 sqlalchemy, aiosqlite
├── frontend/            [NEW] Vue3 + Vite 项目
│   ├── src/
│   │   ├── main.js
│   │   ├── App.vue
│   │   ├── router/index.js
│   │   ├── views/
│   │   │   ├── ChatView.vue      聊天页（现有功能 + 实时图表）
│   │   │   └── HistoryView.vue   历史分析仪表盘
│   │   ├── components/
│   │   │   ├── EmotionPieChart.vue
│   │   │   ├── EmotionLineChart.vue
│   │   │   └── CalendarHeatmap.vue
│   │   └── assets/
│   ├── vite.config.js   代理 /api → FastAPI:8000
│   └── package.json
└── static/              [MODIFY] Vue build 输出目录
```

---

## 第一部分：后端数据库层

### [NEW] database.py
- 使用 SQLAlchemy + aiosqlite（异步驱动）
- 创建 `emotion.db` SQLite 文件
- 提供 `get_db()` 异步依赖注入函数

### [NEW] models_db.py
三张表：

| 表 | 字段 |
|---|---|
| `sessions` | id, started_at, ended_at |
| `emotion_logs` | id, session_id, timestamp, emotion, confidence |
| `chat_messages` | id, session_id, timestamp, role, content, emotion_at_time |

### [MODIFY] server.py
新增/修改的路由：

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/session/start` | 创建新会话，返回 session_id |
| POST | `/api/session/end` | 结束当前会话 |
| GET | `/api/sessions` | 获取所有会话列表 |
| GET | `/api/session/{id}/emotions` | 某次会话的情绪时序（折线图数据） |
| GET | `/api/session/{id}/messages` | 某次会话的聊天记录 |
| GET | `/api/stats` | 全局情绪总占比（饼图百分比） |
| GET | `/api/daily` | 每日情绪数量（热力图数据） |

修改现有路由：
- **`/ws/emotion`**：每次情绪变化写入 `emotion_logs`
- **`/api/chat`**：保存 user 和 ai 消息到 `chat_messages`

---

## 第二部分：Vue3 前端

### 技术栈
- **框架**：Vue 3 + Vite（`create-vite` 模板）
- **路由**：Vue Router 4
- **图表**：Chart.js + vue-chartjs
- **热力图**：vue3-calendar-heatmap（或 D3.js 自绘）
- **样式**：延续现有暗色玻璃拟态风格（原 [style.css](file:///c:/Users/ctu/PycharmProjects/main/static/style.css) 迁移）

### 聊天页 `/` (ChatView.vue)
完整迁移现有功能，并在右侧添加：
- 🥧 **实时情绪饼图**：当前会话的情绪分布（每次情绪更新时累积）
- 📈 **情绪折线图**：最近2分钟的情绪置信度变化

### 历史分析页 `/history` (HistoryView.vue)
- 左侧：会话列表（显示日期/时长/主要情绪）
- 右侧主区域：
  - 总体情绪饼图（所有历史记录）
  - 日历热力图（每日聊天次数/情绪得分）
  - 选中某会话后：显示该会话情绪折线图 + 聊天记录

### Vite 构建配置
- 开发模式：`npm run dev`（`:5173` 端口，代理 `/api` 和 `/ws` 到 `:8000`）
- 生产构建：`npm run build` → 输出到 `../static/`（FastAPI 直接托管）

---

## 验证计划

### 自动化验证（后端 API）
启动 FastAPI 后运行以下 curl 命令验证：
```bash
# 1. 创建会话
curl -X POST http://localhost:8000/api/session/start

# 2. 查询统计
curl http://localhost:8000/api/stats

# 3. 查询会话列表
curl http://localhost:8000/api/sessions
```

### 浏览器验证（前端）
1. `cd frontend && npm run dev` 启动开发服务器
2. 打开 `http://localhost:5173`
3. 启动摄像头 → 验证实时饼图数据累积更新
4. 发送几条消息
5. 切换到 `/history` 页 → 验证饼图、日历热力图显示正确

### 构建验证
```bash
cd frontend && npm run build
uvicorn server:app --reload
# 打开 http://localhost:8000 验证静态页面正常加载
```
