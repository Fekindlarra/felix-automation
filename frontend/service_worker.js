/**
 * Service Worker - Offline Capability & PWA Support
 * FASE 14: Mobile Dashboard Optimization
 *
 * Estrategia:
 * - Network-first para APIs (intentar red, fallback a cache)
 * - Cache-first para assets estáticos (JS, CSS, fonts)
 * - Stale-while-revalidate para datos no-críticos
 */

const CACHE_VERSION = 'felix-v1.0.0';
const ASSET_CACHE = `${CACHE_VERSION}-assets`;
const API_CACHE = `${CACHE_VERSION}-api`;
const IMAGE_CACHE = `${CACHE_VERSION}-images`;

// Assets estáticos (nunca cambian)
const STATIC_ASSETS = [
    '/frontend/admin_dashboard.html',
    '/frontend/client_portal.html',
    '/frontend/prediction_widgets.js',
    'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap',
    'https://cdnjs.cloudflare.com/ajax/libs/chart.js/3.9.1/chart.min.js',
    'https://code.jquery.com/jquery-3.6.0.min.js'
];

// Instalar Service Worker
self.addEventListener('install', (event) => {
    console.log('🔧 Service Worker instalando...');

    event.waitUntil(
        caches.open(ASSET_CACHE)
            .then((cache) => {
                console.log('📦 Cacheando assets estáticos...');
                // No fallar si algo no está disponible
                return Promise.allSettled(
                    STATIC_ASSETS.map(url => {
                        return cache.add(url).catch(() => {
                            console.warn(`⚠️  No se pudo cachear: ${url}`);
                        });
                    })
                );
            })
            .then(() => {
                console.log('✅ Service Worker instalado');
                return self.skipWaiting(); // Activar inmediatamente
            })
            .catch((err) => console.error('❌ Error durante install:', err))
    );
});

// Activar Service Worker
self.addEventListener('activate', (event) => {
    console.log('🚀 Service Worker activando...');

    event.waitUntil(
        caches.keys()
            .then((cacheNames) => {
                // Limpiar caches viejas
                return Promise.all(
                    cacheNames
                        .filter((name) => name.startsWith('felix-') && name !== CACHE_VERSION)
                        .map((name) => {
                            console.log(`🗑️  Eliminando cache vieja: ${name}`);
                            return caches.delete(name);
                        })
                );
            })
            .then(() => {
                console.log('✅ Service Worker activado');
                return self.clients.claim();
            })
    );
});

// Fetch - Estrategia de caché
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);

    // Ignorar solicitudes no-HTTP
    if (!url.protocol.startsWith('http')) {
        return;
    }

    // 1. NETWORK-FIRST para APIs (/api/*)
    if (url.pathname.startsWith('/api/')) {
        event.respondWith(
            fetch(request)
                .then((response) => {
                    // Cache response if successful
                    if (response.ok) {
                        const cache = caches.open(API_CACHE);
                        cache.then((c) => c.put(request, response.clone()));
                    }
                    return response;
                })
                .catch(() => {
                    // Fallback a cache si no hay conexión
                    return caches.match(request)
                        .then((cached) => cached || createOfflineResponse());
                })
        );
        return;
    }

    // 2. CACHE-FIRST para assets estáticos (JS, CSS, fonts)
    if (isStaticAsset(request.url)) {
        event.respondWith(
            caches.match(request)
                .then((cached) => {
                    if (cached) return cached;

                    // Si no está en cache, intentar red
                    return fetch(request)
                        .then((response) => {
                            if (!response.ok) throw new Error('Network response not ok');

                            // Cache la respuesta
                            const cache = caches.open(ASSET_CACHE);
                            cache.then((c) => c.put(request, response.clone()));

                            return response;
                        })
                        .catch(() => {
                            // No está en cache y no hay red
                            return createOfflineResponse();
                        });
                })
        );
        return;
    }

    // 3. STALE-WHILE-REVALIDATE para imágenes
    if (isImage(request.url)) {
        event.respondWith(
            caches.match(request)
                .then((cached) => {
                    const fetchPromise = fetch(request)
                        .then((response) => {
                            if (response.ok) {
                                caches.open(IMAGE_CACHE).then((c) => {
                                    c.put(request, response.clone());
                                });
                            }
                            return response;
                        })
                        .catch(() => null);

                    return cached || fetchPromise || createOfflineImage();
                })
        );
        return;
    }

    // 4. DEFAULT: Network-first con fallback a cache
    event.respondWith(
        fetch(request)
            .then((response) => response)
            .catch(() => {
                return caches.match(request)
                    .then((cached) => cached || createOfflineResponse());
            })
    );
});

/**
 * Funciones auxiliares
 */

function isStaticAsset(url) {
    const staticPatterns = [
        /\.js$/,
        /\.css$/,
        /\.woff2?$/,
        /fonts\.googleapis/,
        /cdnjs\.cloudflare/
    ];
    return staticPatterns.some((pattern) => pattern.test(url));
}

function isImage(url) {
    return /\.(png|jpg|jpeg|gif|webp|svg)$/i.test(url);
}

function createOfflineResponse() {
    return new Response(
        `<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Offline - Felix Automation</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            text-align: center;
            max-width: 400px;
        }
        h1 { font-size: 36px; margin-bottom: 16px; }
        p { font-size: 16px; opacity: 0.9; margin-bottom: 24px; line-height: 1.6; }
        .status {
            background: rgba(255,255,255,0.1);
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 24px;
            font-size: 14px;
        }
        button {
            background: white;
            color: #667eea;
            border: none;
            padding: 12px 32px;
            border-radius: 6px;
            font-weight: 600;
            cursor: pointer;
            font-size: 16px;
        }
        button:hover {
            opacity: 0.9;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📡 Sin conexión</h1>
        <p>No estamos conectados a Internet. Algunos datos pueden estar disponibles en caché.</p>
        <div class="status">
            <p>Intenta conectarte a una red WiFi o datos móviles.</p>
        </div>
        <button onclick="location.reload()">Reintentar Conexión</button>
    </div>
</body>
</html>`,
        {
            status: 503,
            statusText: 'Service Unavailable',
            headers: { 'Content-Type': 'text/html; charset=utf-8' }
        }
    );
}

function createOfflineImage() {
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
        <rect fill="#f0f0f0" width="100" height="100"/>
        <text x="50" y="50" text-anchor="middle" dy=".3em" fill="#999" font-size="12">No disponible</text>
    </svg>`;

    return new Response(svg, {
        headers: { 'Content-Type': 'image/svg+xml' }
    });
}

/**
 * Background Sync - Intentar resincronizar cuando vuelva conexión
 */
self.addEventListener('sync', (event) => {
    if (event.tag === 'sync-emails') {
        event.waitUntil(syncPendingEmails());
    }
});

async function syncPendingEmails() {
    try {
        const cache = await caches.open(API_CACHE);
        const requests = await cache.keys();

        // Filtrar solicitudes de email que no se enviaron
        const emailRequests = requests.filter((req) =>
            req.url.includes('/api/emails') && req.method === 'POST'
        );

        for (const req of emailRequests) {
            try {
                const response = await fetch(req);
                if (response.ok) {
                    await cache.delete(req);
                }
            } catch (error) {
                console.warn('❌ No se pudo sincronizar:', req.url);
            }
        }

        console.log('✅ Resincronización completada');
    } catch (error) {
        console.error('❌ Error en sincronización:', error);
    }
}

/**
 * Message Handler - Comunicación con cliente
 */
self.addEventListener('message', (event) => {
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }

    if (event.data && event.data.type === 'CLEAR_CACHE') {
        caches.keys().then((names) => {
            names.forEach((name) => caches.delete(name));
        });
    }
});

console.log('✅ Service Worker registrado - Offline mode activo');
