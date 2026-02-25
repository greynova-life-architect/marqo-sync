import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const frontendPort = parseInt(process.env.FRONTEND_DEV_PORT || '3000', 10)
const apiHost = process.env.API_SERVER_HOST || 'localhost'
const apiPort = parseInt(process.env.API_SERVER_PORT || '8000', 10)
const apiUrl = `http://${apiHost}:${apiPort}`

export default defineConfig({
  plugins: [react()],
  server: {
    port: frontendPort,
    proxy: {
      '/api': {
        target: apiUrl,
        changeOrigin: true
      }
    }
  }
})

