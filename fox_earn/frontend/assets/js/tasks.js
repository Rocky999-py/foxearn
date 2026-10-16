(function(){
"use strict";
const U=window.Fox.ui, API=window.Fox.api;

function renderPreview(){
  const host=document.getElementById("tasks-list"); if(!host) return;
  host.innerHTML='<div class="card"><p class="empty-state">No tasks available right now.</p></div>';
}

async function load(){
  const host=document.getElementById("tasks-list"); if(!host) return;
  if(!window.Fox.state.authenticated){ renderPreview(); return; }
  host.innerHTML='<div class="skeleton-card"></div>';
  try{
    const res=await API.get("/api/tasks"); const tasks=res.tasks||[];
    if(!tasks.length){ host.innerHTML='<div class="card"><p class="empty-state">No tasks available right now.</p></div>'; return; }
  } catch(err){ host.innerHTML='<div class="card"><p class="empty-state">'+U.escapeHtml(err.message||"Could not load tasks.")+"</p></div>"; }
}

window.Fox=window.Fox||{}; window.Fox.screenHooks=window.Fox.screenHooks||{};
window.Fox.screenHooks.tasks=()=>load();
window.Fox.tasks={ load };
})();
