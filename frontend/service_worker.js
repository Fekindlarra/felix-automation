/**
 * Service Worker for Felix Automation Dashboard
 * - Progressive Web App (PWA) support
 * - Offline capability with caching strategy
 * - Background sync for offline actions
 */

const CACHE_VERSION = 'felix-v1.0.0';
const STATIC_CACHE = `${CACHE_VERSION}-static`;
const DYNAMIC_CACHE = `${CACHE_VERSION}-dynamic`;
const API_CACHE = `${CACHE_VERSION}-api`;

// Files to cache on install
const STATIC_ASSETS = [
    '/frontend/admin_dashboard.html',
    '/frontend/client_portal.html',
    '/frontend/ab_testing_dashboard.html',
    '/frontend/ml_prediction_widgets.html',
    '/frontend/prediction_widgets.js',
    '/frontend/manifest.json',
    'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap'
];

/**
 * Install event - cache static assets
 */
self.addEventListener('install', (event) => {
    console.log('🔧 Service Worker installing...');
    
    event.waitUntil(
        caches.open(STATIC_CACHE)
            .then((cache) => {
                console.log('📦 Caching static assets...');
                return cache.addAll(STATIC_ASSETS);
            })
            .catch((error) => {
                console.error('❌ Cache installation failed:', error);
            })
            .then(() => self.skipWaiting())
    );
});

/**
 * Activate event - clean up old caches
 */
self.addEventListener('activate', (event) => {
    console.log('🚀 Service Worker activating...');
    
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (!cacheName.startsWith(`felix-`)) {
                        return caches.delete(cacheName);
                    }
                    
                    // Keep current version, delete old versions
                    if (cacheName !== STATIC_CACHE && 
                        cacheName !== DYNAMIC_CACHE && 
                        cacheName !== API_CACHE) {
                        console.log('🗑️  Deleting old cache:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        })
            .then(() => self.clients.claim())
    );
});

/**
 * Fetch event - implement caching strategy
 * Network-first for API calls, cache-first for static assets, stale-while-revalidate for dynamics
 */
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);

    // Skip non-GET requests
    if (request.method !== 'GET') {
        return;
    }

    // Skip external resources from other origins (except fonts)
    if (url.origin !== location.origin && !url.hostname.includes('fonts')) {
        return;
    }

    // API calls - network first, fallback to cache
    if (url.pathname.startsWith('/api/') || url.pathname.startsWith('/ws/')) {
        return event.respondWith(networkFirst(request));
    }

    // Static assets (JS, CSS) - cache first, fallback to network
    if (request.destination === 'style' || 
        request.destination === 'script' ||
        url.pathname.endsWith('.ttf') ||
        url.pathname.endsWith('.woff') ||
        url.pathname.endsWith('.woff2')) {
        return event.respondWith(cacheFirst(request));
    }

    // HTML documents - stale while revalidate
    if (request.destination === 'document' || url.pathname.endsWith('.html')) {
        return event.respondWith(staleWhileRevalidate(request));
    }

    // Default - network first with fallback
    event.respondWith(networkFirst(request));
});

/**
 * Cache-first strategy: Try cache first, fallback to network
 * Best for: Static assets that rarely change
 */
async function cacheFirst(request) {
    const cache = await caches.open(STATIC_CACHE);
    const cached = await cache.match(request);

    if (cached) {
        console.log('✅ Cache hit (static):', request.url);
        return cached;
    }

    try {
        const response = await fetch(request);
        if (response.ok) {
            cache.put(request, response.clone());
        }
        return response;
    } catch (error) {
        console.error('❌ Network failed, no cache:', request.url);
        return cacheNotFound();
    }
}

/**
 * Network-first strategy: Try network first, fallback to cache
 * Best for: API calls and dynamic content
 */
async function networkFirst(request) {
    const cache = await caches.open(
        request.url.includes('/api/') ? API_CACHE : DYNAMIC_CACHE
    );

    try {
        const response = await fetch(request);
        
        if (response.ok) {
            cache.put(request, response.clone());
            console.log('✅ Network success:', request.url);
        }
        
        return response;
    } catch (error) {
        console.warn('⚠️  Network failed, trying cache:', request.url);
        const cached = await cache.match(request);
        
        if (cached) {
            console.log('✅ Using cached response:', request.url);
            return cached;
        }

        // Return offline page if available
        if (request.destination === 'document') {
            return cacheNotFound();
        }

        return new Response('Offline - Resource not available', {
            status: 503,
            statusText: 'Service Unavailable'
        });
    }
}

/**
 * Stale-while-revalidate strategy: Return cache immediately, update in background
 * Best for: HTML documents and content that can be slightly stale
 */
async function staleWhileRevalidate(request) {
    const cache = await caches.open(DYNAMIC_CACHE);
    const cached = await cache.match(request);

    // Return cached version immediately
    if (cached) {
        console.log('✅ Serving stale (revalidating):', request.url);
        
        // Update cache in background
        fetch(request).then((response) => {
            if (response.ok) {
                cache.put(request, response.clone());
                console.log('🔄 Cache updated:', request.url);
            }
        }).catch((error) => {
            console.warn('🔄 Background fetch failed:', request.url, error);
        });

        return cached;
    }

    // No cache, fetch from network
    try {
        const response = await fetch(request);
        if (response.ok) {
            cache.put(request, response.clone());
        }
        return response;
    } catch (error) {
        console.error('❌ Network failed, no cache:', request.url);
        return cacheNotFound();
    }
}

/**
 * Return offline fallback page
 */
function cacheNotFound() {
    return new Response(`
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Modo Offline</title>
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    min-height: 100vh;
                    margin: 0;
                    background: linear-gradient(135deg, #667eea 0%, #f093fb 100%);
                    color: white;
                }
                .container {
                    text-align: center;
                    padding: 40px;
                }
                h1 {
                    font-size: 32px;
                    margin: 0 0 16px 0;
                }
                p {
                    font-size: 16px;
                    opacity: 0.9;
                    margin: 0 0 24px 0;
                }
                .status {
                    display: inline-block;
                    padding: 12px 24px;
                    background: rgba(255, 255, 255, 0.2);
                    border-radius: 20px;
                    font-size: 14px;
                }
                @media (prefers-color-scheme: dark) {
                    body {
                        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                    }
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📡 Modo Offline</h1>
                <p>Estás en modo offline. Los datos en caché están disponibles.</p>
                <div class="status">Conectando cuando sea posible...</div>
            </div>
        </body>
        </html>
    `, {
        status: 503,
        statusText: 'Service Unavailable',
        headers: new Headers({
            'Content-Type': 'text/html; charset=utf-8'
        })
    });
}

/**
 * Background sync - for handling offline actions
 */
self.addEventListener('sync', (event) => {
    console.log('🔄 Background sync triggered:', event.tag);

    if (event.tag === 'sync-predictions') {
        event.waitUntil(
            // Retry failed prediction updates
            fetch('/api/predictions/sync', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            }).then(() => {
                console.log('✅ Predictions synced');
            }).catch((error) => {
                console.error('❌ Sync failed:', error);
                throw error; // Retry
            })
        );
    }
});

/**
 * Handle messages from clients
 */
self.addEventListener('message', (event) => {
    const { type, payload } = event.data;

    if (type === 'SKIP_WAITING') {
        console.log('⚡ Skipping waiting, activating new service worker');
        self.skipWaiting();
    }

    if (type === 'CLEAR_CACHE') {
        console.log('🗑️  Clearing cache');
        event.waitUntil(
            caches.keys().then((cacheNames) => {
                return Promise.all(
                    cacheNames.map((cacheName) => caches.delete(cacheName))
                );
            })
        );
    }

    if (type === 'PREFETCH') {
        console.log('📥 Prefetching:', payload);
        event.waitUntil(
            caches.open(DYNAMIC_CACHE).then((cache) => {
                return cache.addAll(payload);
            })
        );
    }
});

console.log('✅ Service Worker loaded and ready');
