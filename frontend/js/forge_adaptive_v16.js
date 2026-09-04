(()=>{
async function loadAdaptiveDirectives(){
 if(S.adaptiveDirectivesLoading)return;
 S.adaptiveDirectivesLoading=true;
 try{S.adaptiveDirectives=await api("/me/training/adaptive-directives");if(["progress","coach"].includes(S.route))render()}
 catch(e){console.warn("Adaptive directives failed",e)}
 finally{S.adaptiveDirectivesLoading=false}
}
function card(){
 const x=S.adaptiveDirectives;
 if(!x)return `<div class="card adaptive-v16-card"><p class=eyebrow>ADAPTIVE PROGRAMMING 5.0</p><h3>Learning your response…</h3><p class=muted>Forge is comparing performance, recovery, and exercise effectiveness.</p></div>`;
 const rows=(x.directives||[]).slice(0,6);
 return `<div class="card adaptive-v16-card"><div class=row><div><p class=eyebrow>ADAPTIVE PROGRAMMING 5.0</p><h3>${x.actionable_count?`${x.actionable_count} item${x.actionable_count===1?"":"s"} to review`:"Current programming is holding up"}</h3></div><span class=adaptive-mode>${esc(x.recovery_mode||"normal")}</span></div><p class=muted>Forge favors the smallest useful change and preserves what is already working.</p>${rows.length?`<div class=adaptive-directive-list>${rows.map(d=>`<div class="adaptive-directive ${String(d.action).startsWith("preserve")?"preserve":"review"}"><div><b>${esc(d.target||"Training")}</b><small>${esc(d.change||d.action)}</small></div><span>${esc(d.confidence||"learning")}</span></div>`).join("")}</div>`:""}<details class=adaptive-rules><summary>How Forge decides</summary><ul>${(x.rules||[]).map(r=>`<li>${esc(r)}</li>`).join("")}</ul></details></div>`;
}
window.loadAdaptiveDirectives=loadAdaptiveDirectives;
window.adaptiveDirectivesCard=card;
})();