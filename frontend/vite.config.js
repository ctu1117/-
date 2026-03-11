import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [vue()],

  // 构建产物输出到 ../static/（FastAPI 静态文件目录）
  build: {
    outDir: path.resolve(__dirname, '../static'),
    emptyOutDir: true,
  },

  server: {
    port: 5173,
    proxy: {
      // 开发模式下，所有 /api 和 /ws 请求代理到 FastAPI
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
      },
    },
  },
})
