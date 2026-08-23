const CACHE="forge-v14-35-10-core-button-spacing-v1";
const APP_SHELL=[
  "/","/index.html","/styles.css?v=14.35.10","/app.js?v=14.35.10","/manifest.webmanifest?v=14.35.10",
  "/assets/pwa/forge-icon-192-v14343.png","/assets/pwa/forge-icon-512-v14343.png",
  "/assets/pwa/forge-icon-maskable-192-v14343.png","/assets/pwa/forge-icon-maskable-512-v14343.png",
  "/assets/pwa/apple-touch-icon.png"
];

self.addEventListener("install", event => {
  event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(APP_SHELL)));
  self.skipWaiting();
});

self.addEventListener("activate", event => {
  event.waitUntil(
    caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
  );
  self.clients.claim();
});

self.addEventListener("fetch", event => {
  const req=event.request;
  if(req.method!=="GET") return;
  const url=new URL(req.url);

  // API and OAuth data must always come from the server.
  if(url.pathname.startsWith("/me/") ||
     url.pathname.startsWith("/auth/") ||
     url.pathname.startsWith("/health")) return;

  if(req.mode==="navigate"){
    event.respondWith(
      fetch(req).catch(() => caches.match("/index.html"))
    );
    return;
  }

  event.respondWith(
    caches.match(req).then(hit => hit || fetch(req).then(res => {
      if(res.ok && url.origin===self.location.origin){
        const copy=res.clone();
        caches.open(CACHE).then(cache => cache.put(req,copy));
      }
      return res;
    }))
  );
});
