(function(global){
  "use strict";
  const FORGE_REQUEST_TIMEOUT_MS=15000;
  async function request(base,getToken,state,path,opt={}){
    const headers={"Content-Type":"application/json",...(opt.headers||{})};
    const token=getToken?.()||"";
    if(token)headers.Authorization=`Bearer ${token}`;
    let response;
    const controller=new AbortController();
    const timer=setTimeout(()=>controller.abort(),FORGE_REQUEST_TIMEOUT_MS);
    try{
      response=await fetch(base+path,{...opt,headers,signal:controller.signal});
    }catch(err){
      if(err?.name==="AbortError")throw Error("Forge request timed out. Check your connection and try again.");
      state.online=navigator.onLine;
      if(!state.online)throw Error("You're offline. Forge will reconnect when your internet returns.");
      throw Error("Forge couldn't reach the server. Try again in a moment.");
    }finally{
      clearTimeout(timer);
    }
    let data={};
    try{data=await response.json()}catch{}
    if(!response.ok){
      if(response.status===401&&token)throw Error("Your session expired. Please sign in again.");
      const detail=data.detail;
      if(Array.isArray(detail)){
        const msg=detail.map(x=>{
          if(typeof x==="string")return x;
          const where=Array.isArray(x?.loc)?x.loc.filter(v=>v!=="body").join(" → "):"";
          return `${where?where+": ":""}${x?.msg||"Invalid request"}`;
        }).join(" • ");
        throw Error(msg||`Request failed (${response.status})`);
      }
      if(detail&&typeof detail==="object")throw Error(detail.message||detail.msg||JSON.stringify(detail));
      throw Error(detail||`Request failed (${response.status})`);
    }
    return data;
  }
  global.ForgeApi=Object.freeze({request});
})(globalThis);
