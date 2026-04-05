<template>
  <div class="auth-container">
    <div class="auth-box">
      <h2>注册新账号</h2>
      <form @submit.prevent="handleRegister">
        <div class="form-group">
          <label>用户名</label>
          <input type="text" v-model="username" required placeholder="请输入用户名" />
        </div>
        <div class="form-group">
          <label>密码</label>
          <input type="password" v-model="password" required placeholder="请输入密码" />
        </div>
        <p class="error-msg" v-if="error">{{ error }}</p>
        <button type="submit" class="auth-btn" :disabled="loading">注册</button>
      </form>
      <div class="toggle-link">
        已有账号？ <RouterLink to="/login">返回登录</RouterLink>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';

const username = ref('');
const password = ref('');
const error = ref('');
const loading = ref(false);
const router = useRouter();

const handleRegister = async () => {
  error.value = '';
  loading.value = true;
  try {
    const res = await fetch('/api/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: username.value, password: password.value })
    });
    const data = await res.json();
    if (res.ok) {
      alert("注册成功，请登录！");
      router.push('/login');
    } else {
      error.value = data.detail || '注册失败';
    }
  } catch (err) {
    error.value = '网络错误';
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.auth-container { display: flex; align-items: center; justify-content: center; min-height: calc(100vh - 80px); padding: 2rem; }
.auth-box { background: rgba(30,41,59,0.7); backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.1); border-radius: 16px; padding: 2.5rem; width: 100%; max-width: 400px; box-shadow: 0 8px 32px rgba(0,0,0,0.3); }
h2 { text-align: center; margin-bottom: 2rem; font-size: 1.5rem; background: linear-gradient(135deg, #a8c0ff, #3f2b96); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
.form-group { margin-bottom: 1.5rem; }
label { display: block; margin-bottom: 0.5rem; font-size: 0.9rem; color: #94a3b8; }
input { width: 100%; padding: 0.75rem 1rem; background: rgba(15,23,42,0.6); border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; color: white; transition: border-color 0.3s; }
input:focus { outline: none; border-color: #6366f1; }
.auth-btn { width: 100%; padding: 0.75rem; background: #6366f1; color: white; border: none; border-radius: 8px; font-weight: 600; cursor: pointer; transition: background 0.3s; }
.auth-btn:hover { background: #4f46e5; }
.error-msg { color: #ef4444; font-size: 0.875rem; margin-bottom: 1rem; }
.toggle-link { text-align: center; margin-top: 1.5rem; font-size: 0.9rem; color: #94a3b8; }
.toggle-link a { color: #6366f1; text-decoration: none; }
</style>
