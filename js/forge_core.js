(function(global){
  "use strict";
  const esc=value=>String(value??"").replace(/[&<>"']/g,ch=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[ch]));
  const requestId=()=>global.crypto?.randomUUID?global.crypto.randomUUID():`${Date.now()}-${Math.random()}`;
  global.ForgeCore=Object.freeze({esc,requestId});
})(globalThis);
