# 情绪感知 AI 聊天系统

> 毕业设计项目 · 基于 MediaPipe 的实时情绪检测 + AI 对话

---

## 项目结构

```
main/
├── emotion/                  # 📦 情绪检测核心模块
│   ├── __init__.py
│   └── detector.py           # get_emotion / create_landmarker / process_frame
│
├── models/                   # 🧠 AI 模型文件
│   └── face_landmarker.task  # MediaPipe 人脸关键点模型（需手动放入）
│
├── static/                   # 🌐 前端页面（待开发）
│   ├── index.html
│   ├── style.css
│   └── app.js
│
├── demo.py                   # 🎥 本地摄像头演示（直接运行测试）
├── server.py                 # 🚀 FastAPI 后端服务
├── requirements.txt          # 📋 依赖清单
└── README.md
```

---

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 放入模型文件

将 `face_landmarker.task` 放入 `models/` 目录。

### 3. 本地摄像头测试

```bash
python demo.py
```

### 4. 启动后端服务（开发中）

```bash
uvicorn server:app --reload
```

---

## 技术栈

| 模块 | 技术 |
|------|------|
| 情绪检测 | MediaPipe Face Landmarker |
| 后端 | FastAPI + WebSocket |
| AI 对话 | DeepSeek API / Kimi API |
| 前端 | 原生 HTML + CSS + JS |
