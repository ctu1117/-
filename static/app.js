/* ═══════════════════════════════════════════════════════════
   情绪感知 AI 伴侣 · 前端逻辑
   ═══════════════════════════════════════════════════════════ */

// ── 情绪配置表 ────────────────────────────────────────────────
const EMOTION_MAP = {
  "Happy :)":   { icon: "😊", cls: "e-happy",    label: "开心 Happy" },
  "Angry >_<":  { icon: "😠", cls: "e-angry",    label: "生气 Angry" },
  "Sad  :(":    { icon: "😢", cls: "e-sad",       label: "伤心 Sad"   },
  "Surprise!":  { icon: "😲", cls: "e-surprise",  label: "惊讶!"       },
  "Neutral :|": { icon: "😐", cls: "e-neutral",   label: "平静"        },
  "No Face":    { icon: "🙈", cls: "e-neutral",   label: "未检测到人脸" },
};

// ── 应用状态 ──────────────────────────────────────────────────
let ws               = null;
let currentEmotion   = "Neutral :|";
let currentConfidence = 0.0;
let chatHistory      = [];
let isWaiting        = false;
let typingCounter    = 0;

// ══════════════════════════════════════════════════════════════
// 摄像头 & WebSocket
// ══════════════════════════════════════════════════════════════
async function startCamera() {
  const video  = document.getElementById("video");
  const canvas = document.getElementById("canvas");
  const btn    = document.getElementById("btn-start");
  const placeholder = document.getElementById("camera-placeholder");

  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: "user" },
    });
    video.srcObject = stream;
    video.style.display = "block";
    placeholder.style.display = "none";

    btn.innerHTML = "<span>✅</span> 摄像头已启动";
    btn.disabled = true;

    video.addEventListener("loadeddata", () => {
      canvas.width  = video.videoWidth;
      canvas.height = video.videoHeight;
      connectWebSocket(canvas, video);
    });
  } catch (err) {
    alert("❌ 无法访问摄像头：" + err.message);
  }
}

function connectWebSocket(canvas, video) {
  const wsUrl = `ws://${location.host}/ws/emotion`;
  ws = new WebSocket(wsUrl);
  const ctx         = canvas.getContext("2d");
  const statusDot   = document.getElementById("ws-status");
  const statusLabel = document.getElementById("ws-label");

  ws.onopen = () => {
    statusDot.className = "status-dot connected";
    statusLabel.textContent = "已连接";

    // 每 200ms 截一帧发送给后端
    setInterval(() => {
      if (ws.readyState !== WebSocket.OPEN) return;
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      ws.send(canvas.toDataURL("image/jpeg", 0.6));
    }, 200);
  };

  ws.onmessage = (evt) => {
    const { emotion, confidence } = JSON.parse(evt.data);
    updateEmotion(emotion, confidence);
  };

  ws.onerror = () => {
    statusDot.className = "status-dot error";
    statusLabel.textContent = "连接失败";
  };

  ws.onclose = () => {
    statusDot.className = "status-dot";
    statusLabel.textContent = "已断开";
  };
}

// ── 更新情绪 UI ───────────────────────────────────────────────
function updateEmotion(emotion, confidence) {
  currentEmotion    = emotion;
  currentConfidence = confidence;

  const info   = EMOTION_MAP[emotion] ?? EMOTION_MAP["Neutral :|"];
  const badge  = document.getElementById("emotion-badge");
  const icon   = document.getElementById("emotion-icon");
  const label  = document.getElementById("emotion-label");
  const fill   = document.getElementById("confidence-fill");
  const pct    = document.getElementById("confidence-pct");
  const chip   = document.getElementById("emotion-chip");

  icon.textContent  = info.icon;
  label.textContent = info.label;
  fill.style.width  = `${(confidence * 100).toFixed(0)}%`;
  pct.textContent   = `${(confidence * 100).toFixed(0)}%`;
  chip.textContent  = `${info.icon} ${info.label}`;

  // 更新徽章颜色类
  badge.className = `emotion-badge ${info.cls}`;
}

// ══════════════════════════════════════════════════════════════
// 聊天功能
// ══════════════════════════════════════════════════════════════
async function sendMessage() {
  if (isWaiting) return;
  const input = document.getElementById("chat-input");
  const msg   = input.value.trim();
  if (!msg) return;

  input.value = "";
  appendMessage(msg, "user");
  chatHistory.push({ role: "user", content: msg });

  // 显示打字动画
  const typingId = showTyping();
  setWaiting(true);

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message:    msg,
        emotion:    currentEmotion,
        confidence: currentConfidence,
        history:    chatHistory.slice(-8),
      }),
    });

    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const { reply } = await res.json();

    removeTyping(typingId);
    appendMessage(reply, "ai");
    chatHistory.push({ role: "assistant", content: reply });

  } catch (err) {
    removeTyping(typingId);
    appendMessage("⚠️ 出错了：" + err.message + "。请确认后端服务已启动。", "ai");
  } finally {
    setWaiting(false);
  }
}

function setWaiting(val) {
  isWaiting = val;
  document.getElementById("btn-send").disabled  = val;
  document.getElementById("chat-input").disabled = val;
}

// ── 追加消息气泡 ──────────────────────────────────────────────
function appendMessage(text, role) {
  const container = document.getElementById("chat-messages");
  const div = document.createElement("div");
  div.className = `message ${role === "ai" ? "ai-message" : "user-message"}`;

  // 简单转义避免 XSS
  const safe = text.replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/\n/g, "<br/>");
  div.innerHTML = `<div class="bubble">${safe}</div>`;

  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

// ── 打字动画 ──────────────────────────────────────────────────
function showTyping() {
  const id        = `typing-${typingCounter++}`;
  const container = document.getElementById("chat-messages");
  const div       = document.createElement("div");
  div.className   = "message ai-message";
  div.id          = id;
  div.innerHTML   = `
    <div class="bubble typing-bubble">
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>
    </div>`;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
  return id;
}

function removeTyping(id) {
  document.getElementById(id)?.remove();
}
