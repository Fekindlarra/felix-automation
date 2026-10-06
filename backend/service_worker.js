/**
 * FASE 14 PASO 13: Service Worker
 * Offline caching and PWA support for Felix Automation Dashboard
 * 
 * Cache Strategy:
 * - Network-first for API calls (always try fresh data)
 * - Cache-first for static assets (CSS, JS, fonts)
 * - Stale-while-revalidate for data endpoints
 */

const CACHE_VERSION = 'v1.0.0-fase14';
const CACHE_STATIC = `${CACHE_VERSION}-static`;
const CACHE_API = `${CACHE_VERSION}-api`;
const CACHE_IMAGES = `${CACHE_VERSION}-images`;

// List of static assets to pre-cache on install
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/admin_dashboard_realtime.html',
  '/dashboard_pipeline_real.html',
  '/client_portal.html',
  '/mobile_dashboard_enhancements.css',
  '/styles.css',
  '/app.js',
  '/manifest.json'
];

/**
 * Install event: Cache static assets
 */
self.addEventListener('install', (event) => {
  console.log('📦 Service Worker installing...');
  
  event.waitUntil(
    caches.open(CACHE_STATIC).then((cache) => {
      console.log('✅ Caching static assets');
      return cache.addAll(STATIC_ASSETS).catch((err) => {
        console.warn('⚠️  Some assets couldn\'t be cached:', err);
        // Don't fail install if some assets are missing
        return Promise.resolve();
      });
    }).then(() => self.skipWaiting()) // Activate immediately
  );
});

/**
 * Activate event: Clean up old caches
 */
self.addEventListener('activate', (event) => {
  console.log('🚀 Service Worker activating...');
  
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((name) => !name.startsWith(CACHE_VERSION))
          .map((name) => {
            console.log(`🗑️  Deleting old cache: ${name}`);
            return caches.delete(name);
          })
      );
    }).then(() => self.clients.claim()) // Claim all clients immediately
  );
});

/**
 * Fetch event: Implement caching strategies
 */
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== 'GET') {
    return event.respondWith(fetch(request));
  }

  // Skip external URLs
  if (url.origin !== self.location.origin) {
    return event.respondWith(fetch(request));
  }

  // API calls: Network-first (try fresh, fallback to cache)
  if (url.pathname.startsWith('/api/')) {
    return event.respondWith(networkFirst(request, CACHE_API));
  }

  // Images: Cache-first (use cached, fetch fresh in background)
  if (request.destination === 'image' || url.pathname.match(/\.(jpg|jpeg|png|gif|svg|webp)$/i)) {
    return event.respondWith(cacheFirst(request, CACHE_IMAGES));
  }

  // Static assets: Cache-first
  if (request.destination === 'style' || request.destination === 'script' || request.destination === 'font') {
    return event.respondWith(cacheFirst(request, CACHE_STATIC));
  }

  // HTML documents: Stale-while-revalidate (serve cached, fetch fresh)
  if (request.destination === 'document' || url.pathname.endsWith('.html')) {
    return event.respondWith(staleWhileRevalidate(request, CACHE_STATIC));
  }

  // Default: Network-first
  return event.respondWith(networkFirst(request, CACHE_API));
});

/**
 * Cache Strategy: Network-first
 * Try network, fallback to cache if offline
 */
async function networkFirst(request, cacheName) {
  const cache = await caches.open(cacheName);
  
  try {
    const response = await fetch(request);
    
    // Cache successful responses
    if (response.ok) {
      cache.put(request, response.clone());
    }
    
    return response;
  } catch (error) {
    // Network failed, try cache
    console.log(`📡 Network failed, trying cache for: ${request.url}`);
    const cached = await cache.match(request);
    
    if (cached) {
      return cached;
    }
    
    // No cache, return offline page
    return new Response('Offline - Data not available', {
      status: 503,
      statusText: 'Service Unavailable',
      headers: new Headers({
        'Content-Type': 'text/plain'
      })
    });
  }
}

/**
 * Cache Strategy: Cache-first
 * Use cached, fetch fresh in background
 */
async function cacheFirst(request, cacheName) {
  const cache = await caches.open(cacheName);
  
  // Try cache first
  const cached = await cache.match(request);
  if (cached) {
    // Fetch fresh in background (don't await)
    fetch(request).then((response) => {
      if (response.ok) {
        cache.put(request, response.clone());
      }
    }).catch(() => {
      // Fetch failed, that's okay - we have cached version
    });
    
    return cached;
  }
  
  // Not in cache, fetch from network
  try {
    const response = await fetch(request);
    
    if (response.ok) {
      cache.put(request, response.clone());
    }
    
    return response;
  } catch (error) {
    return new Response('Offline - Asset not available', {
      status: 503,
      headers: new Headers({ 'Content-Type': 'text/plain' })
    });
  }
}

/**
 * Cache Strategy: Stale-while-revalidate
 * Serve from cache immediately, fetch fresh in background
 */
async function staleWhileRevalidate(request, cacheName) {
  const cache = await caches.open(cacheName);
  
  // Return cached version if available
  const cached = await cache.match(request);
  
  // Fetch fresh in background
  const fetchPromise = fetch(request).then((response) => {
    if (response.ok) {
      cache.put(request, response.clone());
    }
    return response;
  }).catch(() => {
    // Fetch failed, return cached or error
    if (cached) return cached;
    
    return new Response('Offline', {
      status: 503,
      headers: new Headers({ 'Content-Type': 'text/plain' })
    });
  });
  
  // Return cached version or wait for fresh
  return cached || fetchPromise;
}

/**
 * Background sync: Retry pending actions when back online
 */
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-pending-requests') {
    event.waitUntil(syncPendingRequests());
  }
});

async function syncPendingRequests() {
  try {
    const cache = await caches.open(CACHE_API);
    const keys = await cache.keys();
    
    // Find pending requests (marked somehow)
    for (const request of keys) {
      // Only retry POST/PUT requests that failed
      if (request.method !== 'GET') {
        try {
          const response = await fetch(request);
          if (response.ok) {
            // Remove from cache if successful
            await cache.delete(request);
            console.log(`✅ Synced: ${request.url}`);
          }
        } catch (error) {
          console.log(`⚠️  Still offline: ${request.url}`);
        }
      }
    }
  } catch (error) {
    console.error('❌ Sync error:', error);
  }
}

/**
 * Message handler: Communicate with clients
 */
self.addEventListener('message', (event) => {
  const { type, payload } = event.data;
  
  switch (type) {
    case 'SKIP_WAITING':
      self.skipWaiting();
      break;
      
    case 'CLEAR_CACHE':
      caches.delete(payload.cacheName);
      break;
      
    case 'GET_CACHE_SIZE':
      estimateCacheSize().then((size) => {
        event.ports[0].postMessage({ size });
      });
      break;
      
    default:
      console.log('Unknown message:', type);
  }
});

/**
 * Estimate total cache size
 */
async function estimateCacheSize() {
  let totalSize = 0;
  
  try {
    const cacheNames = await caches.keys();
    
    for (const name of cacheNames) {
      const cache = await caches.open(name);
      const keys = await cache.keys();
      
      for (const request of keys) {
        const response = await cache.match(request);
        if (response && response.blob) {
          const blob = await response.blob();
          totalSize += blob.size;
        }
      }
    }
  } catch (error) {
    console.error('Error calculating cache size:', error);
  }
  
  return totalSize;
}

console.log('✅ Service Worker loaded');
