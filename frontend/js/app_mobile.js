/**
 * FASE 14 Track E: Mobile App - PWA & Offline Support
 * Handles service worker registration, PWA install prompt, offline detection
 */

// ============================================================================
// SERVICE WORKER REGISTRATION
// ============================================================================

async function registerServiceWorker() {
  if ('serviceWorker' in navigator) {
    try {
      const registration = await navigator.serviceWorker.register('/service_worker.js', {
        scope: '/',
      });
      console.log('✅ Service Worker registered:', registration);
      
      // Listen for updates
      registration.addEventListener('updatefound', () => {
        const newWorker = registration.installing;
        newWorker.addEventListener('statechange', () => {
          if (newWorker.state === 'activated') {
            console.log('✅ New service worker activated');
            notifyUpdate();
          }
        });
      });
      
      return registration;
    } catch (error) {
      console.error('❌ Service Worker registration failed:', error);
    }
  }
}

// ============================================================================
// PWA INSTALL PROMPT
// ============================================================================

let deferredPrompt;
const installButton = document.getElementById('install-button');

window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  deferredPrompt = e;
  
  if (installButton) {
    installButton.style.display = 'block';
    installButton.addEventListener('click', async () => {
      if (deferredPrompt) {
        deferredPrompt.prompt();
        const { outcome } = await deferredPrompt.userChoice;
        console.log(`User response: ${outcome}`);
        deferredPrompt = null;
        installButton.style.display = 'none';
      }
    });
  }
});

// Hide install button if already installed
window.addEventListener('appinstalled', () => {
  console.log('✅ PWA installed');
  if (installButton) {
    installButton.style.display = 'none';
  }
  deferredPrompt = null;
});

// ============================================================================
// OFFLINE DETECTION
// ============================================================================

const offlineIndicator = document.getElementById('offline-indicator');

function updateOnlineStatus() {
  const isOnline = navigator.onLine;
  
  if (!isOnline && offlineIndicator) {
    offlineIndicator.style.display = 'flex';
    offlineIndicator.textContent = '📡 You are offline. Some features may be limited.';
  } else if (offlineIndicator) {
    offlineIndicator.style.display = 'none';
  }
  
  console.log(`${isOnline ? '🟢' : '🔴'} Connection: ${isOnline ? 'Online' : 'Offline'}`);
}

window.addEventListener('online', updateOnlineStatus);
window.addEventListener('offline', updateOnlineStatus);

// Check initial status
document.addEventListener('DOMContentLoaded', () => {
  updateOnlineStatus();
});

// ============================================================================
// MOBILE OPTIMIZATION
// ============================================================================

// Detect if mobile
function isMobile() {
  return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
}

// Optimize heartbeat for mobile
function optimizeHeartbeat() {
  if (isMobile()) {
    window.HEARTBEAT_INTERVAL = 60000; // 60s on mobile
    console.log('📱 Mobile detected: Using 60s heartbeat');
  } else {
    window.HEARTBEAT_INTERVAL = 30000; // 30s on desktop
    console.log('💻 Desktop detected: Using 30s heartbeat');
  }
}

// Detect network type
async function getConnectionType() {
  if ('connection' in navigator) {
    const connection = navigator.connection;
    console.log(`📡 Network type: ${connection.effectiveType}`);
    return connection.effectiveType; // 4g, 3g, 2g, slow-2g
  }
  return 'unknown';
}

// ============================================================================
// MOBILE GESTURES
// ============================================================================

let touchStartX = 0;
let touchEndX = 0;

document.addEventListener('touchstart', (e) => {
  touchStartX = e.changedTouches[0].screenX;
}, false);

document.addEventListener('touchend', (e) => {
  touchEndX = e.changedTouches[0].screenX;
  handleSwipe();
}, false);

function handleSwipe() {
  const threshold = 50; // Minimum distance for swipe
  const diff = touchStartX - touchEndX;
  
  if (Math.abs(diff) > threshold) {
    if (diff > 0) {
      console.log('👈 Swipe left');
      // Could trigger navigation or panel close
      document.dispatchEvent(new CustomEvent('swipeleft'));
    } else {
      console.log('👉 Swipe right');
      document.dispatchEvent(new CustomEvent('swiperight'));
    }
  }
}

// ============================================================================
// PERFORMANCE MONITORING
// ============================================================================

function logPerformanceMetrics() {
  if ('performance' in window && 'PerformanceObserver' in window) {
    try {
      const observer = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          console.log(`⏱️  ${entry.name}: ${entry.duration.toFixed(2)}ms`);
        }
      });
      
      observer.observe({ entryTypes: ['navigation', 'resource', 'measure'] });
    } catch (e) {
      console.log('Performance observation not supported');
    }
  }
  
  // Log key metrics
  const navigation = performance.getEntriesByType('navigation')[0];
  if (navigation) {
    console.log(`📊 Load Time: ${navigation.loadEventEnd - navigation.loadEventStart}ms`);
    console.log(`📊 DOM Content Loaded: ${navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart}ms`);
  }
}

// ============================================================================
// UPDATE NOTIFICATION
// ============================================================================

function notifyUpdate() {
  const message = document.createElement('div');
  message.className = 'offline-indicator';
  message.innerHTML = `
    <span>🔄 App updated. <a href="#" onclick="location.reload()">Refresh to load new version.</a></span>
  `;
  document.body.appendChild(message);
  
  setTimeout(() => message.remove(), 5000);
}

// ============================================================================
// INITIALIZATION
// ============================================================================

document.addEventListener('DOMContentLoaded', async () => {
  console.log('🚀 Felix Mobile App Initializing...');
  
  // Register service worker
  await registerServiceWorker();
  
  // Setup mobile optimizations
  optimizeHeartbeat();
  await getConnectionType();
  
  // Log performance
  logPerformanceMetrics();
  
  console.log('✅ Mobile app ready');
});

// Export for testing
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    registerServiceWorker,
    updateOnlineStatus,
    isMobile,
    optimizeHeartbeat,
    getConnectionType,
  };
}
