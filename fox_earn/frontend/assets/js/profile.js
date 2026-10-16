(function(){
"use strict";
const U=window.Fox.ui, API=window.Fox.api, TG=window.Fox.tg;
let txOffset=0; const TX_LIMIT=20; let txLoading=false, txExhausted=false;

function setText(id,v){ const n=document.getElementById(id); if(n) n.textContent=v; }

function renderPreview(){
  setText("profile-name","—");
  setText("profile-username","Open inside Telegram to sign in");
  setText("profile-id","—");
  setText("profile-coins","0"); setText("profile-dollars","$0.00"); setText("profile-refs","0");
  setText("profile-wallet-status","—");
  const box=document.getElementById("profile-avatar"); if(box) box.innerHTML='<span id="profile-avatar-fallback">•</span>';
  const tx=document.getElementById("tx-list"); if(tx) tx.innerHTML='<li class="empty-state">Open inside Telegram.</li>';
}

function renderProfile(data){
  const u=data.user||{}, s=data.stats||{};
  setText("profile-name", u.display_name||"—");
  setText("profile-username", u.username?"@"+u.username:"No username");
  setText("profile-id", "Telegram ID: "+(u.telegram_id ? String(u.telegram_id) : "—"));
  setText("profile-coins", U.formatNumber(s.balance||0));
  setText("profile-dollars", U.formatUSD(s.dollar_balance_cents||0));
  setText("profile-refs", U.formatNumber(s.valid_referrals||0));
  setText("profile-wallet-status", data.wallet_active ? "Active ✓" : "Inactive");
  const box=document.getElementById("profile-avatar");
  if(box){
    const photo=u.photo_url||TG.getPhotoUrl();
    if(photo) box.innerHTML='<img src="'+U.escapeHtml(photo)+'" alt="" referrerpolicy="no-referrer"/>';
    else { const init=(u.display_name||TG.getDisplayName()||"•").trim().charAt(0).toUpperCase(); box.innerHTML='<span id="profile-avatar-fallback">'+U.escapeHtml(init)+"</span>"; }
  }
}

function renderTx(rows,append){
  const host=document.getElementById("tx-list"); if(!host) return;
  if(!append && (!rows || !rows.length)){ host.innerHTML='<li class="empty-state">No transactions yet.</li>'; return; }
  const html=rows.map(t=>{
    const pos=Number(t.amount)>=0; const sg=pos?"+":"−";
    const unit = t.unit==="usd_cents" ? U.formatUSD(Math.abs(Number(t.amount))) : U.formatNumber(Math.abs(Number(t.amount)));
    return '<li><span class="tx-main"><span class="tx-title">'+U.escapeHtml(t.label||t.type)+'</span>'+
      '<span class="tx-sub">'+U.escapeHtml(U.formatDateTime(t.created_at))+'</span></span>'+
      '<span class="tx-amount '+(pos?"plus":"minus")+'">'+sg+unit+'</span></li>';
  }).join("");
  if(append) host.insertAdjacentHTML("beforeend",html); else host.innerHTML=html;
}

async function loadTransactions(reset){
  if(txLoading) return;
  if(!window.Fox.state.authenticated){ renderPreview(); return; }
  if(reset){ txOffset=0; txExhausted=false; txLoading=false; }
  if(txExhausted) return;
  txLoading=true;
  const moreBtn=document.getElementById("tx-more-btn"); if(moreBtn) moreBtn.disabled=true;
  try{
    const res=await API.get("/api/transactions?limit="+TX_LIMIT+"&offset="+txOffset);
    const rows=res.transactions||[];
    renderTx(rows, txOffset>0);
    txOffset+=rows.length;
    txExhausted=rows.length<TX_LIMIT;
    if(moreBtn) moreBtn.hidden=txExhausted;
  } catch(err){ const host=document.getElementById("tx-list"); if(host && txOffset===0) host.innerHTML='<li class="empty-state">'+U.escapeHtml(err.message||"Could not load.")+"</li>"; }
  finally { txLoading=false; if(moreBtn) moreBtn.disabled=false; }
}

function initButtons(){
  const b=document.getElementById("tx-more-btn");
  if(b && b.dataset.bound!=="1"){ b.dataset.bound="1"; b.addEventListener("click",()=>loadTransactions(false)); }
  const w=document.getElementById("open-wallet-btn");
  if(w && w.dataset.bound!=="1"){ w.dataset.bound="1"; w.addEventListener("click",()=>{ U.showScreen("wallet"); }); }
}

async function load(){
  if(!window.Fox.state.authenticated){ renderPreview(); return; }
  try{ const d=await API.get("/api/profile"); renderProfile(d); }
  catch(err){ if(err && err.status===401) return; }
}

window.Fox=window.Fox||{}; window.Fox.screenHooks=window.Fox.screenHooks||{};
window.Fox.screenHooks.profile=()=>{ initButtons(); load(); };
window.Fox.screenHooks.transactions=()=>loadTransactions(true);
window.Fox.profile={ load, initTransactionsButton:initButtons, loadTransactions };
})();
