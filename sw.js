const CACHE="forge-v14-36-9-articulated-demo-v2-v1";
const APP_SHELL=[
  "/","/index.html","/styles.css?v=14.36.3","/app.js?v=14.36.3","/manifest.webmanifest?v=14.36.3",
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
    caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE && k !== DEMO_CACHE).map(k => caches.delete(k))))
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


const DEMO_CACHE="forge-exercise-demos-v1";
const DEMO_CACHE_LIMIT=40;

async function trimDemoCache(){
  const cache=await caches.open(DEMO_CACHE);
  const keys=await cache.keys();
  while(keys.length>DEMO_CACHE_LIMIT){
    const oldest=keys.shift();
    await cache.delete(oldest);
  }
}
async function cacheDemoUrls(urls=[]){
  const cache=await caches.open(DEMO_CACHE);
  let cached=0,failed=0;
  for(const url of [...new Set(urls)].slice(0,DEMO_CACHE_LIMIT)){
    try{
      const request=new Request(url,{credentials:"same-origin"});
      const existing=await cache.match(request);
      if(existing){cached++;continue}
      const response=await fetch(request);
      if(response.ok){await cache.put(request,response.clone());cached++}else failed++;
    }catch{failed++}
  }
  await trimDemoCache();
  return {cached,failed,cache:DEMO_CACHE};
}
self.addEventListener("message",event=>{
  const reply=data=>{try{event.ports?.[0]?.postMessage(data)}catch{}};
  if(event.data?.type==="CACHE_DEMO_ASSETS"){
    event.waitUntil(cacheDemoUrls(event.data.urls||[]).then(reply));
  }
  if(event.data?.type==="DEMO_CACHE_STATUS"){
    event.waitUntil(caches.open(DEMO_CACHE).then(async cache=>{
      const keys=await cache.keys();reply({cached:keys.length,limit:DEMO_CACHE_LIMIT,cache:DEMO_CACHE});
    }));
  }
});

self.addEventListener("fetch",event=>{
  const req=event.request;
  if(req.method!=="GET")return;
  const url=new URL(req.url);
  const isDemoMedia=/\/(assets\/)?exercise[_-]?demos\//i.test(url.pathname) ||
                    /\.(mp4|webm|gif|avif|webp)$/i.test(url.pathname);
  if(!isDemoMedia)return;
  event.respondWith((async()=>{
    const cache=await caches.open(DEMO_CACHE);
    const hit=await cache.match(req);
    if(hit)return hit;
    try{
      const response=await fetch(req);
      if(response.ok){await cache.put(req,response.clone());await trimDemoCache()}
      return response;
    }catch{
      return new Response("",{status:503,statusText:"Demo unavailable offline"});
    }
  })());
});
