import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { VitePWA } from 'vite-plugin-pwa'
import path from 'path'
import fs from 'fs'

// Custom plugin to copy static files
const copyStaticFiles = () => {
  return {
    name: 'copy-static-files',
    writeBundle() {
      // Ensure the static directory exists
      const outputDir = path.resolve(__dirname, 'dist/static')
      if (!fs.existsSync(outputDir)) {
        fs.mkdirSync(outputDir, { recursive: true })
      }
      
      // Copy service worker and notification files
      const sourceDir = path.resolve(__dirname, 'public/static')
      if (fs.existsSync(sourceDir)) {
        const files = fs.readdirSync(sourceDir)
        files.forEach(file => {
          const sourcePath = path.join(sourceDir, file)
          const destPath = path.join(outputDir, file)
          fs.copyFileSync(sourcePath, destPath)
        })
      }
    }
  }
}

export default defineConfig({
  plugins: [
    vue(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.ico', 'robots.txt'],
      manifest: {
        name: 'Education App',
        short_name: 'EduApp',
        description: 'A modern education management application',
        theme_color: '#ffffff',
        background_color: '#ffffff',
        display: 'standalone',
        icons: [
          {
            src: '/icons/pwa-192x192.png',
            sizes: '192x192',
            type: 'image/png'
          },
          {
            src: '/icons/pwa-512x512.png',
            sizes: '512x512',
            type: 'image/png'
          },
          {
            src: '/icons/maskable-512x512.png',
            sizes: '512x512',
            type: 'image/png',
            purpose: 'maskable'
          }
        ],
        start_url: '/',
        scope: '/'
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg,vue}'],
        runtimeCaching: [
          {
            urlPattern: /^https:\/\/fonts\.googleapis\.com\/.*/i,
            handler: 'CacheFirst',
            options: {
              cacheName: 'google-fonts-cache',
              expiration: {
                maxEntries: 10,
                maxAgeSeconds: 60 * 60 * 24 * 365
              },
              cacheableResponse: {
                statuses: [0, 200]
              }
            }
          }
        ]
      }
    }),
    copyStaticFiles()
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    }
  },
  base: '/',
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    rollupOptions: {
      external: [
        'firebase/app',
        'firebase/messaging',
        'firebase/messaging/sw'
      ],
      output: {
        manualChunks(id) {
          if (id.includes('node_modules')) {
            return 'vendor'
          }
        }
      }
    }
  }
}) 