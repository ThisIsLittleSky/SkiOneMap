import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src')
    }
  },
  server: {
    port: 9095,
    proxy: {
      '/api': {
        target: 'http://localhost:8085',
        changeOrigin: true
      },
      '/ws': {
        target: 'ws://localhost:8085',
        ws: true
      },
      '/ai': {
        target: 'http://localhost:8001',
        changeOrigin: true
      },
      '/weather': {
        target: 'http://t.weather.sojson.com',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/weather/, '')
      }
    }
  },
  build: {
    chunkSizeWarningLimit: 600,
    rollupOptions: {
      output: {
        manualChunks: {
          echarts: ['echarts'],
          vue: ['vue', 'vue-router', 'pinia'],
          axios: ['axios'],
        }
      }
    }
  }
})

