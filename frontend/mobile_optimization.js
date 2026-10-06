/**
 * Mobile Optimization Module for FASE 14
 * Handles: Service Worker registration, PWA features, mobile-specific behaviors
 */

class MobileOptimizer {
  constructor() {
    this.serviceWorkerReady = false;
    this.isOnline = navigator.onLine;
    this.isMobile = this.detectMobile();
    this.heartbeatInterval = this.isMobile ? 60000 : 30000; // Mobile: 60s, Desktop: 30s

    this.init();
  }

  /**
   * Initialize mobile optimization
   */
  async init() {
    console.log('[Mobile] Initializing optimization (Mobile:', this.isMobile + ')');

    // Register service worker
    await this.registerServiceWorker();

    // Listen for online/offline events
    this.setupConnectionMonitoring();

    // Optimize WebSocket heartbeat for mobile
    this.optimizeWebSocketHeartbeat();

    // Setup touch-friendly UI enhancements
    this.setupTouchOptimizations();

    // Setup PWA install prompt
    this.setupInstallPrompt();

    // Optimize viewport for notches and safe areas
    this.optimizeViewport();
  }

  /**
   * Detect if device is mobile
   */
  detectMobile() {
    const userAgent = navigator.userAgent;
    return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(userAgent);
  }

  /**
   * Register service worker for offline support
   */
  async registerServiceWorker() {
    if (!('serviceWorker' in navigator)) {
      console.warn('[Mobile] Service Worker not supported');
      return;
    }

    try {
      const registration = await navigator.serviceWorker.register('/backend/service_worker.js', {
        scope: '/',
        updateViaCache: 'none'
      });

      this.serviceWorkerReady = true;
      console.log('[Mobile] Service Worker registered:', registration.scope);

      // Handle updates
      registration.addEventListener('updatefound', () => {
        const newWorker = registration.installing;
        newWorker.addEventListener('statechange', () => {
          if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
            this.notifyUpdate();
          }
        });
      });

      // Handle controller change
      navigator.serviceWorker.addEventListener('controllerchange', () => {
        console.log('[Mobile] Service Worker controller changed');
      });

    } catch (error) {
      console.error('[Mobile] Service Worker registration failed:', error);
    }
  }

  /**
   * Setup online/offline monitoring
   */
  setupConnectionMonitoring() {
    window.addEventListener('online', () => {
      this.isOnline = true;
      this.showNotification('Connection restored', 'success');
      this.triggerSync();
    });

    window.addEventListener('offline', () => {
      this.isOnline = false;
      this.showNotification('Connection lost - using cached data', 'warning');
    });
  }

  /**
   * Optimize WebSocket heartbeat based on device and connection type
   */
  optimizeWebSocketHeartbeat() {
    if (typeof window.websocketHeartbeat !== 'undefined') {
      // Adjust heartbeat interval based on network type
      const connection = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
      let interval = this.heartbeatInterval;

      if (connection) {
        if (connection.effectiveType === '4g') {
          interval = this.isMobile ? 45000 : 30000; // 4G: reduce interval
        } else if (connection.effectiveType === '3g') {
          interval = 90000; // 3G: increase interval to save battery
        } else if (connection.effectiveType === '2g') {
          interval = 120000; // 2G: significant increase
        }
      }

      window.websocketHeartbeat = interval;
      console.log('[Mobile] WebSocket heartbeat set to:', interval + 'ms');
    }
  }

  /**
   * Setup touch-friendly UI enhancements
   */
  setupTouchOptimizations() {
    // Increase touch target sizes on mobile
    if (this.isMobile) {
      const style = document.createElement('style');
      style.textContent = `
        /* Touch target minimum size: 44x44px */
        button, a.button, .btn, [role="button"],
        .connection-status, .filter-badge, .tab-button {
          min-height: 44px;
          min-width: 44px;
          padding: 12px 16px !important;
        }

        /* Avoid hover on touch devices */
        @media (hover: none) {
          button:hover, a:hover, .card:hover {
            background-color: inherit;
            transform: none;
          }
        }

        /* Increase touch feedback */
        @media (hover: none) {
          button, a.button, .btn {
            -webkit-tap-highlight-color: rgba(74, 144, 226, 0.2);
            transition: background-color 0.2s ease;
          }

          button:active, a:active, .btn:active {
            background-color: rgba(74, 144, 226, 0.15);
          }
        }

        /* Mobile-friendly spacing */
        @media (max-width: 768px) {
          .card {
            margin-bottom: 12px;
            border-radius: 12px;
          }

          .grid {
            gap: 12px;
          }

          .modal {
            margin: 0;
            border-radius: 12px 12px 0 0;
            max-height: 90vh;
          }
        }

        /* Optimize chart rendering on mobile */
        @media (max-width: 768px) {
          canvas {
            max-height: 250px !important;
          }

          .chart-container {
            height: auto;
            max-height: 300px;
          }
        }

        /* Safe area support */
        body {
          padding-bottom: env(safe-area-inset-bottom, 0px);
        }

        /* Landscape mode adjustments */
        @media (max-height: 500px) and (orientation: landscape) {
          .header {
            padding: 8px 16px;
          }

          .header h1 {
            font-size: 16px;
          }

          main {
            gap: 8px;
          }
        }
      `;
      document.head.appendChild(style);
      console.log('[Mobile] Touch optimizations applied');
    }
  }

  /**
   * Setup PWA install prompt handling
   */
  setupInstallPrompt() {
    let deferredPrompt;

    window.addEventListener('beforeinstallprompt', (e) => {
      e.preventDefault();
      deferredPrompt = e;
      this.showInstallPrompt(deferredPrompt);
    });

    window.addEventListener('appinstalled', () => {
      console.log('[Mobile] App installed');
      deferredPrompt = null;
      this.showNotification('App installed successfully!', 'success');
    });
  }

  /**
   * Show PWA install prompt
   */
  showInstallPrompt(prompt) {
    // Create install button if it doesn't exist
    const installBtn = document.getElementById('install-app-btn');
    if (installBtn) {
      installBtn.style.display = 'flex';
      installBtn.addEventListener('click', async () => {
        if (prompt) {
          prompt.prompt();
          const { outcome } = await prompt.userChoice;
          console.log('[Mobile] Install prompt outcome:', outcome);
        }
      });
    }
  }

  /**
   * Optimize viewport for notches and safe areas
   */
  optimizeViewport() {
    // The viewport meta is typically already set in HTML, but ensure it's correct
    let viewport = document.querySelector('meta[name="viewport"]');
    if (!viewport) {
      viewport = document.createElement('meta');
      viewport.name = 'viewport';
      document.head.appendChild(viewport);
    }

    viewport.setAttribute('content',
      'width=device-width, initial-scale=1, maximum-scale=5, viewport-fit=cover, user-scalable=yes'
    );
  }

  /**
   * Trigger background sync when coming online
   */
  async triggerSync() {
    if ('serviceWorker' in navigator && 'SyncManager' in window) {
      try {
        const registration = await navigator.serviceWorker.ready;
        await registration.sync.register('sync-predictions');
        await registration.sync.register('sync-analytics');
        console.log('[Mobile] Background sync triggered');
      } catch (error) {
        console.error('[Mobile] Sync registration failed:', error);
      }
    }
  }

  /**
   * Show notification to user
   */
  showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `mobile-notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
      position: fixed;
      bottom: env(safe-area-inset-bottom, 20px);
      left: 16px;
      right: 16px;
      padding: 16px;
      background: ${type === 'success' ? '#4CAF50' : type === 'warning' ? '#FF9800' : '#2196F3'};
      color: white;
      border-radius: 8px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.2);
      font-size: 14px;
      z-index: 10000;
      animation: slideUp 0.3s ease;
    `;

    document.body.appendChild(notification);

    setTimeout(() => {
      notification.style.animation = 'slideDown 0.3s ease';
      setTimeout(() => notification.remove(), 300);
    }, 3000);
  }

  /**
   * Notify user about available update
   */
  notifyUpdate() {
    const notification = document.createElement('div');
    notification.className = 'update-notification';
    notification.innerHTML = `
      <div style="padding: 16px;">
        <p style="margin: 0 0 12px 0; font-weight: 500;">Update available</p>
        <button id="update-now-btn" style="padding: 8px 16px; background: #4A90E2; color: white; border: none; border-radius: 4px; cursor: pointer;">
          Update Now
        </button>
      </div>
    `;
    notification.style.cssText = `
      position: fixed;
      bottom: env(safe-area-inset-bottom, 20px);
      left: 16px;
      right: 16px;
      background: white;
      border-radius: 8px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.2);
      z-index: 10000;
    `;

    document.body.appendChild(notification);

    document.getElementById('update-now-btn').addEventListener('click', () => {
      window.location.reload();
    });
  }

  /**
   * Get network information
   */
  getNetworkInfo() {
    const connection = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
    return {
      online: navigator.onLine,
      effectiveType: connection?.effectiveType || 'unknown',
      downlink: connection?.downlink || undefined,
      rtt: connection?.rtt || undefined,
      saveData: navigator.connection?.saveData || false
    };
  }

  /**
   * Optimize images for mobile
   */
  optimizeImages() {
    const images = document.querySelectorAll('img');
    images.forEach(img => {
      if (!img.loading) {
        img.loading = 'lazy';
      }
      if (!img.decoding) {
        img.decoding = 'async';
      }
    });
  }

  /**
   * Get device memory (if available)
   */
  getDeviceCapabilities() {
    return {
      cores: navigator.hardwareConcurrency || 1,
      memory: navigator.deviceMemory || undefined,
      mobile: this.isMobile,
      network: this.getNetworkInfo()
    };
  }
}

// Auto-initialize on page load
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    window.mobileOptimizer = new MobileOptimizer();
  });
} else {
  window.mobileOptimizer = new MobileOptimizer();
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
  module.exports = MobileOptimizer;
}
