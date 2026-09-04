window.ForgeMobile=(()=>{
let keyboardOpen=false,lastFocus=null;
function init(){
 document.documentElement.classList.add("forge-mobile-ready");
 const setViewport=()=>document.documentElement.style.setProperty("--forge-vh",`${window.innerHeight*0.01}px`);
 setViewport();addEventListener("resize",setViewport,{passive:true});
 if(window.visualViewport){
  const sync=()=>{const obscured=Math.max(0,window.innerHeight-window.visualViewport.height-window.visualViewport.offsetTop);keyboardOpen=obscured>120;document.body.classList.toggle("keyboard-open",keyboardOpen);document.documentElement.style.setProperty("--keyboard-inset",`${obscured}px`)};
  visualViewport.addEventListener("resize",sync,{passive:true});visualViewport.addEventListener("scroll",sync,{passive:true});sync();
 }
 document.addEventListener("focusin",e=>{if(e.target.matches("input,textarea,select")){lastFocus=e.target;setTimeout(()=>e.target.scrollIntoView({block:"center",behavior:"smooth"}),120)}});
 document.addEventListener("touchstart",e=>{const b=e.target.closest("button,[role=button],a,input,select");if(b)b.classList.add("touch-active")},{passive:true});
 document.addEventListener("touchend",()=>document.querySelectorAll(".touch-active").forEach(x=>x.classList.remove("touch-active")),{passive:true});
 document.addEventListener("visibilitychange",()=>{if(document.visibilityState==="visible"&&lastFocus&&!document.contains(lastFocus))lastFocus=null});
}
function loading(label="Loading"){return `<div class=mobile-skeleton aria-label="${label}" role=status><i></i><i></i><i></i></div>`}
function standalone(){return matchMedia("(display-mode: standalone)").matches||navigator.standalone===true}
function platform(){const ua=navigator.userAgent||"";return /iPhone|iPad|iPod/.test(ua)?"ios":/Android/.test(ua)?"android":"desktop"}
return {init,loading,standalone,platform,get keyboardOpen(){return keyboardOpen}};
})();
document.readyState==="loading"?document.addEventListener("DOMContentLoaded",ForgeMobile.init,{once:true}):ForgeMobile.init();