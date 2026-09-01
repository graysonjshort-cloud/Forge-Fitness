window.ForgeCache=(()=>{
const stamps=new Map();
function fresh(key,ms){const t=stamps.get(key)||0;return Date.now()-t<ms}
function mark(key){stamps.set(key,Date.now())}
function invalidate(...keys){keys.forEach(k=>stamps.delete(k))}
return {fresh,mark,invalidate};
})();