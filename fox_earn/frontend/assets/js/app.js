(function(){
"use strict";
const CFG=window.FOX_CONFIG, U=window.Fox.ui, API=window.Fox.api, TG=window.Fox.tg;
window.Fox.state={ ready:false, authenticated:false, profile:null };

function sleep(ms){ return new Promise(r=>setTimeout(r,ms)); }

function setPreview(reason){
  window.Fox.state.authenticated=false;
  API.clearToken();
  U.showBanner(reason||"Open inside Telegram to sign in.","offline");
}

async function authenticate(){
  if(!TG.isInsideTelegram()){ setPreview("Preview mode — open inside Telegram."); return false; }
  try{
    const res=await API.authenticate(TG.state.initData);
    if(res && res.token){ API.setToken(res.token); window.Fox.state.authenticated=true; U.hideBanner(); return true; }
    throw new Error("No token.");
  } catch(err){
    if(err && (err.code==="network_error" || err.code==="timeout")){
      U.showBanner("Backend unreachable. Retrying…","offline");
      await sleep(2000);
      try{ const r2=await API.authenticate(TG.state.initData); if(r2 && r2.token){ API.setToken(r2.token); window.Fox.state.authenticated=true; U.hideBanner(); return true; } }catch(e){}
      setPreview("Cannot reach server. Preview mode."); return false;
    }
    if(err && err.code==="maintenance_mode"){ setPreview("Maintenance mode."); return false; }
    setPreview("Sign-in failed: "+(err.message||"unknown")); return false;
  }
}

function bindNavigation(){
  document.querySelectorAll("[data-nav]").forEach(b=>b.addEventListener("click",()=>{ U.showScreen(b.getAttribute("data-nav")); TG.hapticImpact("light"); }));
  document.querySelectorAll("[data-goto]").forEach(b=>b.addEventListener("click",()=>{ U.showScreen(b.getAttribute("data-goto")); TG.hapticImpact("light"); }));
  if(U.el.backBtn) U.el.backBtn.addEventListener("click",()=>{ U.goBack(); TG.hapticImpact("light"); });
  if(U.el.refreshBtn) U.el.refreshBtn.addEventListener("click", async ()=>{ U.setLoading(U.el.refreshBtn,true,""); await refreshAll(true); U.setLoading(U.el.refreshBtn,false); U.toast("Refreshed.","success"); });
  const rb=document.getElementById("reload-app-btn"); if(rb) rb.addEventListener("click",()=>window.location.reload());
}

async function refreshAll(force){
  await Promise.all([
    window.Fox.home     ? window.Fox.home.load()      : null,
    window.Fox.tasks    ? window.Fox.tasks.load()     : null,
    window.Fox.referrals? window.Fox.referrals.load(force) : null,
    window.Fox.wallet   ? window.Fox.wallet.load(force) : null,
    window.Fox.profile  ? window.Fox.profile.load()   : null
  ]);
}

function startHealthMonitor(){
  if(!API.isConfigured()) return;
  if(!window.Fox.state.authenticated) return;
  let wasDown=false;
  async function check(){
    try{ await API.health(); if(wasDown){ U.toast("Backend reachable again.","success"); wasDown=false; refreshAll(true); } }
    catch(err){ if(!wasDown){ wasDown=true; U.showBanner("Backend unavailable.","offline"); } }
  }
  setInterval(check, CFG.HEALTH_RETRY_MS); check();
}

async function boot(){
  U.init();
  window.addEventListener("unhandledrejection",ev=>console.error("[FOX]",ev.reason));
  API.setUnauthorizedHandler(()=>U.showBanner("Session expired.","offline"));
  TG.init();
  if(window.Fox.home) window.Fox.home.initTapButton();
  bindNavigation();

  if(API.isConfigured()) await authenticate();
  else setPreview("Backend URL not configured.");

  await refreshAll(true);
  U.showScreen("home");
  startHealthMonitor();
  U.hideBootLoader();
  window.Fox.state.ready=true;
}
if(document.readyState==="loading") document.addEventListener("DOMContentLoaded",boot);
else boot();
})();
