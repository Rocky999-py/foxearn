(function(){
"use strict";
const U=window.Fox.ui, API=window.Fox.api, TG=window.Fox.tg;
let loaded=false, walletState=null;
let activeActivation=null, pendingScreenshot=null, withdrawTimerId=null;
const MAX_BYTES = 5 * 1024 * 1024;

function setText(id,v){ const n=document.getElementById(id); if(n) n.textContent=v; }
function showError(id,m){ const b=document.getElementById(id); if(!b) return; if(m){ b.textContent=m; b.hidden=false; } else { b.hidden=true; b.textContent=""; } }

function initTabs(){
  document.querySelectorAll("#wallet-tabs .tab").forEach(t=>{
    if(t.dataset.bound==="1") return; t.dataset.bound="1";
    t.addEventListener("click",()=>{
      document.querySelectorAll("#wallet-tabs .tab").forEach(x=>x.classList.remove("is-active"));
      t.classList.add("is-active");
      const tab=t.getAttribute("data-tab");
      document.querySelectorAll("#screen-wallet .tab-panel").forEach(p=>{ p.hidden = p.getAttribute("data-panel")!==tab; });
      TG.hapticImpact("light");
    });
  });
}

function renderPreview(){
  const locked=document.getElementById("wa-locked");
  const enabled=document.getElementById("wa-enabled");
  if(locked){ locked.hidden=false; }
  if(enabled) enabled.hidden=true;
  setText("wa-fee-header","$20.00 USD"); setText("wa-fee-header2","$20.00 USD");
  setText("wd-available","$0.00"); setText("wd-coins","0"); setText("wd-wallet-status","—"); setText("wd-min","$0.00");
  const sel=document.getElementById("wd-method");
  if(sel){ sel.innerHTML=""; const o=document.createElement("option"); o.value=""; o.textContent="—"; sel.appendChild(o); sel.disabled=true; }
  setTimerDisplay(0);
}

function renderMethods(methods){
  const host=document.getElementById("wa-methods"); if(!host) return;
  if(!methods.length){ host.innerHTML='<div class="card"><p class="empty-state">No payment methods enabled.</p></div>'; return; }
  host.innerHTML = methods.map(m=>{
    const cls = m.code==="okx" ? "okx" : m.code==="bybit" ? "bybit" : "binance";
    const initials = m.code.slice(0,2).toUpperCase();
    return '<button class="pay-card" data-method="'+U.escapeHtml(m.code)+'" type="button">'+
      '<span class="pay-logo '+cls+'">'+U.escapeHtml(initials)+'</span>'+
      '<span class="pay-info"><span class="pay-name">'+U.escapeHtml(m.label)+'</span>'+
      '<span class="pay-fee">$'+(Number(m.fee_cents||0)/100).toFixed(2)+' USD</span></span>'+
      '<span class="pay-arrow">›</span></button>';
  }).join("");
  host.querySelectorAll("[data-method]").forEach(b=>b.addEventListener("click",()=>selectMethod(b.getAttribute("data-method"))));
}

function selectMethod(code){
  const methods=(walletState && walletState.wallet_methods) || [];
  const m=methods.find(x=>x.code===code); if(!m) return;
  const form=document.getElementById("wa-form-wrap");
  const instr=document.getElementById("wa-instructions");
  const title=document.getElementById("wa-form-title");
  activeActivation={ method:code, fee_cents:m.fee_cents||0, label:m.label };
  document.querySelectorAll("#wa-methods .pay-card").forEach(p=>p.classList.toggle("is-selected", p.getAttribute("data-method")===code));
  if(title) title.textContent="Pay with "+m.label;
  if(instr){
    const lines=[];
    lines.push("<p><b>Amount:</b> $"+((m.fee_cents||0)/100).toFixed(2)+" USD</p>");
    if(m.instructions) lines.push("<p class='mt-8'>"+U.escapeHtml(m.instructions)+"</p>");
    if(m.destination) lines.push("<p class='mt-8'><b>Destination:</b> <code>"+U.escapeHtml(m.destination)+"</code></p>");
    instr.innerHTML=lines.join("");
  }
  if(form) form.hidden=false;
  TG.hapticImpact("light");
  form.scrollIntoView({behavior:"smooth",block:"start"});
}

function resetScreenshot(){
  pendingScreenshot=null;
  const input=document.getElementById("wa-screenshot"); if(input) input.value="";
  const img=document.getElementById("wa-preview-img"); if(img) img.removeAttribute("src");
  const wrap=document.getElementById("wa-preview-wrap"); if(wrap) wrap.hidden=true;
  const zone=document.getElementById("wa-upload-zone"); if(zone) zone.classList.remove("has-file");
  const txt=document.getElementById("wa-upload-text"); if(txt) txt.textContent="Tap to attach a screenshot";
}

function initScreenshot(){
  const input=document.getElementById("wa-screenshot");
  const zone=document.getElementById("wa-upload-zone");
  const wrap=document.getElementById("wa-preview-wrap");
  const img=document.getElementById("wa-preview-img");
  const txt=document.getElementById("wa-upload-text");
  const rm=document.getElementById("wa-preview-remove");
  if(!input || input.dataset.bound==="1") return;
  input.dataset.bound="1";
  input.addEventListener("change",()=>{
    const file=input.files && input.files[0]; if(!file) return;
    if(!/^image\/(png|jpeg|jpg|webp)$/i.test(file.type)){ U.toast("PNG, JPG or WEBP only.","error"); resetScreenshot(); return; }
    if(file.size>MAX_BYTES){ U.toast("Max 5 MB.","error"); resetScreenshot(); return; }
    const r=new FileReader();
    r.onload=()=>{
      pendingScreenshot={ dataUrl:String(r.result), name:file.name };
      if(img) img.src=pendingScreenshot.dataUrl;
      if(wrap) wrap.hidden=false;
      if(zone) zone.classList.add("has-file");
      if(txt) txt.textContent="Screenshot attached ✓";
      TG.hapticImpact("light");
    };
    r.onerror=()=>{ U.toast("Could not read image.","error"); resetScreenshot(); };
    r.readAsDataURL(file);
  });
  if(rm) rm.addEventListener("click",(e)=>{ e.preventDefault(); e.stopPropagation(); resetScreenshot(); });
}

async function submitActivation(){
  showError("wa-error","");
  if(!activeActivation){ U.toast("Select a payment method first.","info"); return; }
  if(!pendingScreenshot){ showError("wa-error","Attach a payment screenshot."); return; }
  const tref=document.getElementById("wa-txref");
  const btn=document.getElementById("wa-submit");
  U.setLoading(btn,true,"Submitting…");
  try{
    const res=await API.post("/api/wallet/activate/submit",{
      method:activeActivation.method,
      tx_ref: tref ? tref.value.trim() : "",
      screenshot_base64: pendingScreenshot.dataUrl
    });
    U.toast("Submitted. Request #"+res.id+" pending.","success");
    TG.hapticNotify("success");
    activeActivation=null; resetScreenshot();
    const form=document.getElementById("wa-form-wrap"); if(form) form.hidden=true;
    await load(true);
  } catch(err){ showError("wa-error",err.message||"Submission failed."); }
  finally { U.setLoading(btn,false); }
}

function renderActivations(list){
  const host=document.getElementById("wa-history"); if(!host) return;
  if(!list.length){ host.innerHTML='<li class="empty-state">No requests yet.</li>'; return; }
  const P={pending:'<span class="pill pill-amber">Pending</span>',approved:'<span class="pill pill-green">Approved</span>',rejected:'<span class="pill pill-red">Rejected</span>'};
  host.innerHTML=list.map(a=>'<li><span class="li-main">'+
    '<span class="li-name">'+U.escapeHtml(a.method.toUpperCase())+" · $"+((Number(a.fee_cents||0)/100).toFixed(2))+'</span>'+
    '<span class="li-sub">'+U.escapeHtml(U.formatDateTime(a.created_at))+'</span></span>'+
    (P[a.status]||'<span class="pill pill-muted">'+U.escapeHtml(a.status)+'</span>')+"</li>").join("");
}

function renderWithdrawals(reqs){
  const host=document.getElementById("wd-list"); if(!host) return;
  if(!reqs.length){ host.innerHTML='<li class="empty-state">No requests yet.</li>'; return; }
  const P={pending:'<span class="pill pill-amber">Pending</span>',approved:'<span class="pill pill-cyan">Approved</span>',rejected:'<span class="pill pill-red">Rejected</span>',paid:'<span class="pill pill-green">Paid</span>'};
  host.innerHTML=reqs.map(r=>'<li><span class="li-main">'+
    '<span class="li-name">'+U.formatUSD(r.amount_cents)+" · "+U.escapeHtml(r.method)+'</span>'+
    '<span class="li-sub">'+U.escapeHtml(U.formatDateTime(r.created_at))+'</span></span>'+
    (P[r.status]||'<span class="pill pill-muted">'+U.escapeHtml(r.status)+'</span>')+"</li>").join("");
}

function render(data){
  walletState=data;
  const locked=document.getElementById("wa-locked");
  const enabled=document.getElementById("wa-enabled");
  const feeUSD="$"+((data.wallet_fee_cents||0)/100).toFixed(2)+" USD";
  setText("wa-fee-header",feeUSD); setText("wa-fee-header2",feeUSD);
  if(data.wallet_enabled){ if(locked) locked.hidden=true; if(enabled) enabled.hidden=false; renderMethods(data.wallet_methods||[]); }
  else { if(locked) locked.hidden=false; if(enabled) enabled.hidden=true; }
  renderActivations(data.wallet_activations||[]);
  setText("wd-available", U.formatUSD(data.summary.dollar_balance_cents||0));
  setText("wd-coins", U.formatNumber(data.summary.balance||0));
  setText("wd-wallet-status", data.wallet_active?"Active":"Inactive");
  setText("wd-min", U.formatUSD(data.min_withdrawal_cents||0));
  const sel=document.getElementById("wd-method");
  if(sel){
    const ms=data.withdrawal_methods||[]; sel.innerHTML="";
    if(!ms.length){ const o=document.createElement("option"); o.value=""; o.textContent="No methods enabled"; sel.appendChild(o); sel.disabled=true; }
    else { sel.disabled=false; ms.forEach(m=>{ const o=document.createElement("option"); o.value=m.code; o.textContent=m.label; sel.appendChild(o); }); }
  }
  renderWithdrawals(data.withdrawals||[]);
  startWithdrawTimer(data.withdrawal_open===true, data.withdrawal_target_ms, data.withdrawal_timer_enabled);
  const wdB=document.getElementById("wd-submit");
  if(wdB) wdB.disabled = !data.withdrawal_open || !data.wallet_active || !(data.withdrawal_methods||[]).length;
}

function startWithdrawTimer(isOpen, targetMs, enabled){
  const state=document.getElementById("wd-window-state");
  const note=document.getElementById("wd-timer-note");
  if(withdrawTimerId){ clearInterval(withdrawTimerId); withdrawTimerId=null; }
  if(!enabled){ if(state){ state.textContent="Disabled"; state.className="pill pill-muted"; } if(note) note.textContent="Withdrawals disabled by the administrator."; setTimerDisplay(0); return; }
  if(isOpen){ if(state){ state.textContent="OPEN"; state.className="pill pill-green"; } if(note) note.textContent="Withdrawals open. Submit below."; setTimerDisplay(0); return; }
  if(state){ state.textContent="CLOSED"; state.className="pill pill-amber"; }
  if(note) note.textContent="Withdrawals open when the timer ends.";
  const tick=()=>{ const ms=Math.max(0, (targetMs||0) - Date.now()); setTimerDisplay(ms); if(ms<=0 && withdrawTimerId){ clearInterval(withdrawTimerId); withdrawTimerId=null; if(window.Fox.wallet) window.Fox.wallet.load(true); } };
  tick(); withdrawTimerId=setInterval(tick,1000);
}

function setTimerDisplay(ms){
  const totalSec=Math.floor(ms/1000);
  const d=Math.floor(totalSec/86400);
  const h=Math.floor((totalSec%86400)/3600);
  const m=Math.floor((totalSec%3600)/60);
  const s=totalSec%60;
  const pad=(n)=>String(n).padStart(2,"0");
  const setN=(id,v)=>{ const el=document.getElementById(id); if(el) el.textContent=v; };
  setN("tm-days", pad(d)); setN("tm-hours", pad(h)); setN("tm-minutes", pad(m)); setN("tm-seconds", pad(s));
}

function initWithdrawSubmit(){
  const btn=document.getElementById("wd-submit");
  if(!btn || btn.dataset.bound==="1") return; btn.dataset.bound="1";
  btn.addEventListener("click", async ()=>{
    showError("wd-error","");
    if(!window.Fox.state.authenticated){ U.toast("Open inside Telegram.","info"); return; }
    if(!walletState) return;
    const method=document.getElementById("wd-method").value;
    const amountStr=document.getElementById("wd-amount").value;
    const dest=document.getElementById("wd-destination").value.trim();
    const amount=parseFloat(amountStr);
    if(!method){ showError("wd-error","Choose a method."); return; }
    if(!isFinite(amount)||amount<=0){ showError("wd-error","Enter a valid amount."); return; }
    if(!dest){ showError("wd-error","Enter destination."); return; }
    const cents=Math.round(amount*100);
    if(!window.confirm("Submit withdrawal of $"+amount.toFixed(2)+"?")) return;
    U.setLoading(btn,true,"Submitting…");
    try{
      await API.post("/api/withdrawals",{amount_cents:cents, method, destination:dest, idempotency_key:"wd_"+Date.now().toString(36)+"_"+Math.random().toString(36).slice(2,8)});
      U.toast("Withdrawal submitted.","success"); TG.hapticNotify("success");
      document.getElementById("wd-amount").value=""; document.getElementById("wd-destination").value="";
      await load(true);
    } catch(err){ showError("wd-error",err.message||"Failed."); }
    finally { U.setLoading(btn,false); }
  });
}

function bindAll(){
  initTabs(); initScreenshot(); initWithdrawSubmit();
  const waSub=document.getElementById("wa-submit");
  if(waSub && waSub.dataset.bound!=="1"){ waSub.dataset.bound="1"; waSub.addEventListener("click",submitActivation); }
  const waCan=document.getElementById("wa-cancel");
  if(waCan && waCan.dataset.bound!=="1"){ waCan.dataset.bound="1"; waCan.addEventListener("click",()=>{ activeActivation=null; resetScreenshot(); const f=document.getElementById("wa-form-wrap"); if(f) f.hidden=true; document.querySelectorAll("#wa-methods .pay-card").forEach(p=>p.classList.remove("is-selected")); }); }
}

async function load(force){
  if(loaded && !force) return;
  if(!window.Fox.state.authenticated){ renderPreview(); loaded=true; return; }
  try{ const d=await API.get("/api/wallet"); render(d); loaded=true; }
  catch(err){ const e=document.getElementById("wd-eligibility"); if(e) e.textContent=err.message||"Could not load wallet."; }
}

window.Fox=window.Fox||{}; window.Fox.screenHooks=window.Fox.screenHooks||{};
window.Fox.screenHooks.wallet=()=>{ bindAll(); load(false); };
window.Fox.wallet={ load, bindAll };
})();
