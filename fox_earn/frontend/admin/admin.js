(function(){
"use strict";
const API=window.Fox.api, TG=window.Fox.tg, U=window.Fox.ui;

function showAuthError(m){
  const b=document.getElementById("admin-auth-error"), t=document.getElementById("admin-auth-error-msg"), a=document.getElementById("admin-app");
  if(t) t.textContent=m; if(b) b.hidden=false; if(a) a.hidden=true; U.hideBootLoader();
}
function showAdmin(){ const b=document.getElementById("admin-auth-error"); if(b) b.hidden=true; const a=document.getElementById("admin-app"); if(a) a.hidden=false; }

async function authenticate(){
  if(!TG.isInsideTelegram()){ showAuthError("Open this panel from inside Telegram."); return false; }
  try{
    const res=await API.authenticate(TG.state.initData);
    if(!res || !res.token){ showAuthError("Authentication failed."); return false; }
    if(!res.is_admin){ showAuthError("This account is not an administrator."); return false; }
    API.setToken(res.token); showAdmin(); return true;
  } catch(err){ showAuthError(err.message||"Could not authenticate."); return false; }
}

async function fetchImage(url){
  const r=await fetch(url,{headers:{"Authorization":"Bearer "+API.getToken()},cache:"no-store"});
  if(!r.ok) throw new Error("image "+r.status);
  return URL.createObjectURL(await r.blob());
}

function bindTabs(){
  document.querySelectorAll("#admin-app .tab").forEach(t=>{
    if(t.dataset.bound==="1") return; t.dataset.bound="1";
    t.addEventListener("click",()=>{
      document.querySelectorAll("#admin-app .tab").forEach(x=>x.classList.remove("is-active"));
      t.classList.add("is-active");
      const tab=t.getAttribute("data-atab");
      document.querySelectorAll("#admin-app .tab-panel").forEach(p=>{ p.hidden=p.getAttribute("data-apanel")!==tab; });
    });
  });
}

async function loadOverview(){
  const host=document.getElementById("admin-stats"); if(!host) return;
  try{ const ov=await API.get("/api/admin/overview"); const s=ov.stats||{};
    host.innerHTML="<li><span>Total users</span><b>"+U.formatNumber(s.total_users||0)+"</b></li>"+
      "<li><span>Coins in circulation</span><b>"+U.formatNumber(s.total_coins||0)+"</b></li>"+
      "<li><span>Pending activations</span><b>"+U.formatNumber(s.pending_wallet_activations||0)+"</b></li>"+
      "<li><span>Pending withdrawals</span><b>"+U.formatNumber(s.pending_withdrawals||0)+"</b></li>";
  } catch(err){ host.innerHTML="<li><span>Error</span><b>"+U.escapeHtml(err.message)+"</b></li>"; }
}

async function loadActivations(){
  const host=document.getElementById("admin-wa"); if(!host) return;
  const st=(document.getElementById("admin-wa-status")||{}).value || "pending";
  try{
    const res=await API.get("/api/admin/wallet-activations?status="+encodeURIComponent(st)+"&limit=50");
    const rows=res.activations||[];
    if(!rows.length){ host.innerHTML='<li class="empty-state">No requests.</li>'; return; }
    host.innerHTML=rows.map(a=>{
      const shot=a.has_screenshot?'<div class="upload-preview" data-shot="'+a.id+'" style="margin-top:10px"><p class="card-hint" style="padding:12px">Loading…</p></div>':'';
      return '<li style="flex-direction:column;align-items:stretch"><div class="row-between"><span class="li-main">'+
        '<span class="li-name">'+U.escapeHtml((a.method||"").toUpperCase())+" · "+U.formatUSD(a.fee_cents||0)+'</span>'+
        '<span class="li-sub">'+U.escapeHtml(a.display_name||"User")+" · "+U.escapeHtml(U.formatDateTime(a.created_at))+'</span>'+
        '</span><span class="pill pill-amber">'+U.escapeHtml(a.status)+'</span></div>'+shot+
        '<div class="row-between mt-8"><button class="btn btn-primary btn-compact" data-wa-act="approve" data-wa-id="'+a.id+'">Approve</button>'+
        '<button class="btn btn-ghost btn-compact" data-wa-act="reject" data-wa-id="'+a.id+'">Reject</button></div></li>';
    }).join("");
    host.querySelectorAll("[data-wa-act]").forEach(b=>b.addEventListener("click",()=>waAction(b.getAttribute("data-wa-id"),b.getAttribute("data-wa-act"),b)));
    for(const a of rows){
      if(!a.has_screenshot) continue;
      const w=host.querySelector('[data-shot="'+a.id+'"]'); if(!w) continue;
      try{ const url=await fetchImage("/api/wallet/activate/"+a.id+"/screenshot"); w.innerHTML='<img src="'+url+'" alt="proof"/>'; }
      catch(e){ w.innerHTML='<p class="card-hint" style="padding:12px;color:#fecaca">Could not load.</p>'; }
    }
  } catch(err){ host.innerHTML='<li class="empty-state">'+U.escapeHtml(err.message||"Could not load.")+"</li>"; }
}

async function waAction(id, action, btn){
  let note="";
  if(action==="reject"){ note=window.prompt("Rejection reason:",""); if(note===null) return; }
  else { if(!window.confirm("Approve and activate wallet?")) return; }
  U.setLoading(btn,true,"…");
  try{ await API.post("/api/admin/wallet-activations/"+encodeURIComponent(id)+"/action",{action,note}); U.toast("Done.","success"); await loadActivations(); }
  catch(err){ U.toast(err.message||"Failed.","error"); }
  finally { U.setLoading(btn,false); }
}

async function loadWithdrawals(){
  const host=document.getElementById("admin-withdrawals"); if(!host) return;
  try{ const res=await API.get("/api/admin/withdrawals?status=pending&limit=50"); const rows=res.withdrawals||[];
    if(!rows.length){ host.innerHTML='<li class="empty-state">None pending.</li>'; return; }
    host.innerHTML=rows.map(w=>'<li style="flex-direction:column;align-items:stretch"><div class="row-between">'+
      '<span class="li-main"><span class="li-name">'+U.formatUSD(w.amount_cents)+" · "+U.escapeHtml(w.method)+'</span>'+
      '<span class="li-sub">'+U.escapeHtml(w.display_name||"User")+" · "+U.escapeHtml(U.formatDateTime(w.created_at))+'</span>'+
      '<span class="li-sub">Dest: '+U.escapeHtml(w.destination||"—")+'</span></span>'+
      '<span class="pill pill-amber">pending</span></div>'+
      '<div class="row-between mt-8"><button class="btn btn-primary btn-compact" data-wd-act="approve" data-wd-id="'+w.id+'">Approve</button>'+
      '<button class="btn btn-ghost btn-compact" data-wd-act="reject" data-wd-id="'+w.id+'">Reject</button>'+
      '<button class="btn btn-primary btn-compact" data-wd-act="paid" data-wd-id="'+w.id+'">Paid</button></div></li>').join("");
    host.querySelectorAll("[data-wd-act]").forEach(b=>b.addEventListener("click",()=>wdAction(b.getAttribute("data-wd-id"),b.getAttribute("data-wd-act"),b)));
  } catch(err){ host.innerHTML='<li class="empty-state">'+U.escapeHtml(err.message||"Failed.")+"</li>"; }
}

async function wdAction(id, action, btn){
  if(!window.confirm("Confirm: "+action+"?")) return;
  U.setLoading(btn,true,"…");
  try{ await API.post("/api/admin/withdrawals/"+encodeURIComponent(id)+"/action",{action,note:""}); U.toast("Done.","success"); await loadWithdrawals(); }
  catch(err){ U.toast(err.message||"Failed.","error"); }
  finally { U.setLoading(btn,false); }
}

async function loadSettings(){
  try{
    const res=await API.get("/api/admin/settings"); const items=res.settings||[];
    const map={}; items.forEach(s=>map[s.key]=s.value);
    const tmr=document.getElementById("admin-timer-target"); if(tmr && map.withdrawal_target_local) tmr.value=map.withdrawal_target_local;
    const tme=document.getElementById("admin-timer-enabled"); if(tme) tme.checked=map.withdrawal_timer_enabled==="1";
    const wa=document.getElementById("admin-wa-enabled"); if(wa) wa.value=map.wallet_activation_enabled==="1"?"1":"0";
    const wf=document.getElementById("admin-wa-fee"); if(wf) wf.value=(parseInt(map.wallet_activation_fee_cents||"0",10)/100).toFixed(2);
    const rmin=document.getElementById("admin-ref-min"); if(rmin) rmin.value=map.referral_min_valid||"3";
    const rrew=document.getElementById("admin-ref-reward"); if(rrew) rrew.value=(parseInt(map.referral_reward_cents||"1000",10)/100).toFixed(2);
    const sh=document.getElementById("admin-settings");
    if(sh) sh.innerHTML=items.map(s=>"<li><span>"+U.escapeHtml(s.key)+"</span><b>"+U.escapeHtml(String(s.value).slice(0,80))+"</b></li>").join("");
  } catch(err){}
  try{ const res=await API.get("/api/admin/audit?limit=50"); const rows=res.logs||[];
    const h=document.getElementById("admin-audit");
    if(h) h.innerHTML=rows.length?rows.map(l=>'<li><span class="li-main"><span class="li-name">'+U.escapeHtml(l.action)+'</span><span class="li-sub">'+U.escapeHtml(l.actor||"system")+" · "+U.escapeHtml(U.formatDateTime(l.created_at))+'</span></span></li>').join(""):'<li class="empty-state">No entries.</li>';
  } catch(err){}
}

function bindButtons(){
  const t=document.getElementById("admin-timer-save");
  if(t) t.addEventListener("click", async ()=>{
    const dt=document.getElementById("admin-timer-target").value; const en=document.getElementById("admin-timer-enabled").checked;
    try{ await API.post("/api/admin/withdrawal-timer",{target_local:dt, enabled:en}); U.toast("Saved.","success"); loadSettings(); }
    catch(e){ U.toast(e.message||"Failed.","error"); }
  });
  const wa=document.getElementById("admin-wa-save");
  if(wa) wa.addEventListener("click", async ()=>{
    const en=document.getElementById("admin-wa-enabled").value; const fee=parseFloat(document.getElementById("admin-wa-fee").value||"0");
    try{ await API.post("/api/admin/settings",{updates:{wallet_activation_enabled:en, wallet_activation_fee_cents:String(Math.round(fee*100))}}); U.toast("Saved.","success"); loadSettings(); }
    catch(e){ U.toast(e.message||"Failed.","error"); }
  });
  const r=document.getElementById("admin-ref-save");
  if(r) r.addEventListener("click", async ()=>{
    const minv=document.getElementById("admin-ref-min").value; const reward=parseFloat(document.getElementById("admin-ref-reward").value||"0");
    try{ await API.post("/api/admin/settings",{updates:{referral_min_valid:String(minv), referral_reward_cents:String(Math.round(reward*100))}}); U.toast("Saved.","success"); loadSettings(); }
    catch(e){ U.toast(e.message||"Failed.","error"); }
  });
  const sr=document.getElementById("admin-settings-reload"); if(sr) sr.addEventListener("click",()=>loadSettings());
  const sel=document.getElementById("admin-wa-status"); if(sel) sel.addEventListener("change",()=>loadActivations());
}

async function boot(){
  U.init(); TG.init();
  if(!await authenticate()) return;
  bindTabs(); bindButtons();
  await Promise.all([loadOverview(), loadActivations(), loadWithdrawals(), loadSettings()]);
  U.hideBootLoader();
}
if(document.readyState==="loading") document.addEventListener("DOMContentLoaded",boot);
else boot();
})();
