(()=>{
function enhance(root=document){
 root.querySelectorAll(".card").forEach(el=>el.classList.add("ui-card"));
 root.querySelectorAll(".btn").forEach(el=>el.classList.add("ui-btn"));
 root.querySelectorAll("input,select,textarea").forEach(el=>el.classList.add("ui-control"));
 root.querySelectorAll(".eyebrow").forEach(el=>el.classList.add("ui-eyebrow"));
 root.querySelectorAll(".muted").forEach(el=>el.classList.add("ui-muted"));
 root.querySelectorAll("h1,h2,h3").forEach(el=>el.classList.add("ui-heading"));
}
const observer=new MutationObserver(ms=>{for(const m of ms){for(const n of m.addedNodes){if(n.nodeType===1)enhance(n)}}});
function start(){enhance(document);observer.observe(document.body,{childList:true,subtree:true});document.documentElement.dataset.uiSystem="15.13"}
if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",start,{once:true});else start();
window.ForgeUI={enhance};
})();