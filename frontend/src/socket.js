import { io } from "socket.io-client"
import { socketio_port } from "../../../../sites/common_site_config.json"

import { getCachedListResource } from "frappe-ui/src/resources/listResource"
import { getCachedResource } from "frappe-ui/src/resources/resources"

export function initSocket() {
  let host = window.location.hostname
  let siteName = window.site_name
  let port = window.location.port ? `:${socketio_port}` : ""
  let protocol = port ? "http" : "https"
  let url = `${protocol}://${host}${port}/${siteName}`
  
  let socket = io(url, {
    withCredentials: true,
    reconnectionAttempts: 5,
  })

  // Handle education-specific resource updates
  socket.on("education:refetch_resource", (data) => {
    if (data.cache_key) {
      let resource =
        getCachedResource(data.cache_key) ||
        getCachedListResource(data.cache_key)

      if (resource) {
        resource.reload()
      }
    }
  })

  // Handle notification updates
  socket.on("education:notification", (data) => {
    // Reload notification resources
    const notificationsResource = getCachedListResource("education:notifications")
    const unreadCountResource = getCachedResource("education:unread_notifications_count")
    
    if (notificationsResource) {
      notificationsResource.reload()
    }
    
    if (unreadCountResource) {
      unreadCountResource.reload()
    }
    
    // Show browser notification if permitted
    if (data.message && Notification && Notification.permission === "granted") {
      // Use system notification if we're not already looking at notifications
      if (!window.location.pathname.includes('/notifications')) {
        const notification = new Notification('Education Portal', {
          body: data.message.replace(/<[^>]*>/g, ''), // Strip HTML
          icon: '/apple-touch-icon.png',
        })
        
        notification.onclick = () => {
          window.focus()
          window.location.href = '/notifications'
        }
      }
    }
  })

  return socket
} 