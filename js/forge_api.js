(function(global){
  "use strict";
  async function request(base,getToken,state,path,opt={}){
    const headers={"Content-Type":"application/json",...(opt.headers||{})};
    const token=getToken?.()||"";
    if(token)headers.Authorization=`Bearer ${token}`;
    let response;
    try{
      response=await fetch(base+path,{...opt,headers});
    }catch(err){
      state.online=navigator.onLine;
      if(!state.online)throw Error("You're offline. Forge will reconnect when your internet returns.");
      throw Error("Forge couldn't reach the server. Try again in a moment.");
    }
    let data={};
    try{data=await response.json()}catch{}
    if(!response.ok){
      if(response.status===401&&token)throw Error("Your session expired. Please sign in again.");
      throw Error(data.detail||`Request failed (${response.status})`);
    }
    return data;
  }
  global.ForgeApi=Object.freeze({request});
})(globalThis);
