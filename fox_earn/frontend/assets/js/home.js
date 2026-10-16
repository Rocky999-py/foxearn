(function(){
"use strict";
const CFG=window.FOX_CONFIG, U=window.Fox.ui, API=window.Fox.api, TG=window.Fox.tg;
const tap={ pending:0, inFlight:false, flushTimer:null, button:null, floaters:null };

function setText(id,v){ const n=document.getElementById(id); if(n) n.textContent=v; }

function renderAvatar(boxId,fbId,u){
  const box=document.getElementById(boxId); if(!box) return;
  const photo = u.photo_url || TG.getPhotoUrl();
  const name = u.display_name || TG.getDisplayName() || "•";
  if(photo) box.innerHTML='<img src="'+U.escapeHtml(photo)+'" alt="" referrerpolicy="no-referrer"/>';
  else box.innerHTML='<span id="'+fbId+'">'+U.escapeHtml((name).trim().charAt(0).toUpperCase())+"</span>";
}

function renderSummary(data){
  const u=data.user||{}, s=data.stats||{};
  setText("home-name", u.display_name||"—");
  setText("home-username", u.username?"@"+u.username:"—");
  setText("home-coins", U.formatNumber(s.balance||0));
  setText("home-dollars", U.formatUSD(s.dollar_balance_cents||0));
  setText("home-total-earned", U.formatNumber(s.total_earned||0)+" coins");
  renderAvatar("home-avatar","home-avatar-fallback",u);
}

function renderPreview(){
  setText("home-name","—");
  setText("home-username","Open inside Telegram to sign in");
  setText("home-coins","0");
  setText("home-dollars","$0.00");
  setText("home-total-earned","0 coins");
  const box=document.getElementById("home-avatar");
  if(box) box.innerHTML='<span id="home-avatar-fallback">•</span>';
}

function spawnFloater(e,text){
  if(!tap.floaters) return;
  const n=document.createElement("span"); n.className="floater"; n.textContent=text;
  const r=tap.floaters.getBoundingClientRect();
  let x=r.width/2,y=r.height/2;
  if(e && typeof e.clientX==="number" && e.clientX>0){ x=e.clientX-r.left; y=e.clientY-r.top; }
  else { x+=(Math.random()-.5)*r.width*.45; y+=(Math.random()-.5)*r.height*.35; }
  n.style.left=x+"px"; n.style.top=y+"px";
  tap.floaters.appendChild(n);
  setTimeout(()=>{ if(n.parentNode) n.parentNode.removeChild(n); },1000);
}

function updateQueueLabel(){
  const n=document.getElementById("home-tap-queue"); if(!n) return;
  if(tap.pending>0 || tap.inFlight){ n.hidden=false; n.textContent = tap.inFlight ? "Syncing taps…" : tap.pending+" tap(s) queued…"; }
  else n.hidden=true;
}

function newBatchId(){ return "tap_"+Date.now().toString(36)+"_"+Math.random().toString(36).slice(2,12); }

function onTap(e){
  if(!window.Fox.state.authenticated){ U.toast("Open inside Telegram.","info"); spawnFloater(e,"+0"); return; }
  tap.pending+=1; spawnFloater(e,"+1"); TG.hapticImpact("light");
  tap.button.classList.add("is-tapped"); setTimeout(()=>tap.button.classList.remove("is-tapped"),90);
  updateQueueLabel();
  if(tap.pending>=CFG.TAP_BATCH_SIZE) flushTaps();
  else if(!tap.flushTimer) tap.flushTimer=setTimeout(flushTaps,CFG.TAP_FLUSH_INTERVAL_MS);
}

function applyTapResult(res){
  if(!res) return;
  if(typeof res.balance==="number") setText("home-coins", U.formatNumber(res.balance));
  if(typeof res.dollar_balance_cents==="number") setText("home-dollars", U.formatUSD(res.dollar_balance_cents));
  if(typeof res.total_earned==="number") setText("home-total-earned", U.formatNumber(res.total_earned)+" coins");
}

async function flushTaps(){
  if(tap.flushTimer){ clearTimeout(tap.flushTimer); tap.flushTimer=null; }
  if(tap.inFlight || tap.pending<=0) return;
  if(!window.Fox.state.authenticated){ tap.pending=0; updateQueueLabel(); return; }
  const count = Math.min(tap.pending, CFG.TAP_MAX_LOCAL_QUEUE);
  tap.pending -= count; tap.inFlight = true;
  const batchId = newBatchId(); updateQueueLabel();
  try{ const res = await API.post("/api/taps",{taps:count,batch_id:batchId}); applyTapResult(res); TG.hapticImpact("light"); }
  catch(err){
    tap.pending = Math.min(tap.pending+count, CFG.TAP_MAX_LOCAL_QUEUE);
    if(err && err.status===429) U.toast("Too fast.","info");
    else if(err && err.status===401) tap.pending=0;
    else U.showBanner("Connection problem.","offline");
  } finally {
    tap.inFlight=false; updateQueueLabel();
    if(tap.pending>0 && !tap.flushTimer) tap.flushTimer=setTimeout(flushTaps, CFG.TAP_FLUSH_INTERVAL_MS);
  }
}

function initTapButton(){
  tap.button = document.getElementById("tap-button");
  tap.floaters = document.getElementById("tap-floaters");
  if(tap.button) tap.button.addEventListener("click", onTap, {passive:true});
}

async function load(){
  if(!window.Fox.state.authenticated){ renderPreview(); return; }
  try{ const data = await API.get("/api/profile"); window.Fox.state.profile=data; renderSummary(data); U.hideBanner(); }
  catch(err){ if(err && err.status===401) return; U.showBanner("Backend unavailable.","offline"); }
}

window.Fox = window.Fox || {};
window.Fox.home = { load, initTapButton, flushTaps };
})();
