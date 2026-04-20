import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), 'VITE_')

  return {
    plugins: [react()],
    server: {
      proxy: {
        '/api/v1/ai-chat': {
        target: 'http://localhost:8002',
        changeOrigin: true,
      },
      '/api': {
          target: env.VITE_API_BASE_URL || 'http://localhost:8080',
          changeOrigin: true,
        },
        '/ws/v1/ai-chat': {
        target: 'ws://localhost:8002',
        ws: true,
        changeOrigin: true,
      },
      '/ws': {
          target: env.VITE_WS_BASE_URL || 'ws://localhost:8080',
          ws: true,
          changeOrigin: true,
        },
      },
    },
  }
})