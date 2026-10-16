(function(){
"use strict";
const U=window.Fox.ui, API=window.Fox.api, TG=window.Fox.tg;
let loaded=false;
function setText(id,v){ const n=document.getElementById(id); if(n) n.textContent=v; }

function renderPreview(){
  const input=document.getElementById("ref-link-input"); if(input) input.value="Open inside Telegram";
  setText("ref-count-text","0");
  setText("ref-eligibility-text","Open inside Telegram to see your referrals.");
  const host=document.getElementById("ref-milestones");
  if(host) host.innerHTML='<li class="empty-state">Open inside Telegram.</li>';
}

function render(data){
  const link=data.referral_link||"";
  const input=document.getElementById("ref-link-input"); if(input) input.value=link||"—";
  const valid=Number(data.valid_referrals||0);
  const minReq=Number(data.min_referrals_to_unlock||3);
  const unlocked = valid >= minReq;
  setText("ref-count-text", U.formatNumber(valid));
  setText("ref-eligibility-text", unlocked ? "🎉 Reward claims unlocked." : "You need "+minReq+" valid referrals. "+Math.max(0,minReq-valid)+" more to go.");

  const host=document.getElementById("ref-milestones"); if(!host) return;
  const ms=data.milestones||[];
  if(!ms.length){ host.innerHTML='<li class="empty-state">No milestones configured.</li>'; return; }
  host.innerHTML = ms.map(m=>{
    const claimed=!!m.claimed, qualified=valid>=Number(m.count);
    let state,label,disabled;
    if(claimed){ state="claimed"; label="Claimed"; disabled=true; }
    else if(!unlocked){ state="locked"; label="Locked"; disabled=true; }
    else if(!qualified){ state="not_qualified"; label="Not yet"; disabled=true; }
    else { state="available"; label="Claim $"+(Number(m.reward_cents||0)/100).toFixed(2); disabled=false; }
    return '<li><div class="ms-left">'+
      '<span class="ms-title">'+U.escapeHtml(String(m.count))+' '+(Number(m.count)===1?"Invite":"Invites")+'</span>'+
      '<span class="ms-reward">$'+(Number(m.reward_cents||0)/100).toFixed(2)+'</span>'+
      '<span class="ms-status">'+U.escapeHtml(
        state==="locked"?("Requires "+minReq+" valid referrals"):
        state==="not_qualified"?("Reach "+m.count+" valid referrals"):
        state==="claimed"?"Already claimed":"Ready to claim")+'</span></div>'+
      '<button class="btn '+(state==="available"?"btn-primary":"btn-ghost")+' btn-compact ms-btn" '+
        (disabled?"disabled ":"")+'data-claim="'+m.count+'" data-state="'+state+'">'+label+'</button></li>';
  }).join("");
  host.querySelectorAll("[data-claim]").forEach(b=>{
    if(b.dataset.state!=="available") return;
    b.addEventListener("click",()=>claimMilestone(b));
  });
}

async function claimMilestone(btn){
  const count=btn.getAttribute("data-claim");
  if(!window.confirm("Claim $10 for the "+count+"-invite milestone?")) return;
  U.setLoading(btn,true,"Claiming…");
  try{
    const res = await API.post("/api/referrals/claim",{milestone:parseInt(count,10)});
    U.toast("Claimed $"+(Number(res.reward_cents||0)/100).toFixed(2)+"!","success"); TG.hapticNotify("success");
    await load(true); if(window.Fox.home) window.Fox.home.load();
  } catch(err){ U.toast(err.message||"Could not claim.","error"); U.setLoading(btn,false); }
}

function initCopy(){
  const btn=document.getElementById("ref-copy-btn"), input=document.getElementById("ref-link-input");
  if(!btn||!input || btn.dataset.bound==="1") return; btn.dataset.bound="1";
  btn.addEventListener("click", async ()=>{
    if(!window.Fox.state.authenticated){ U.toast("Open inside Telegram.","info"); return; }
    const v=input.value;
    if(!v || v==="—" || v==="Loading…"){ U.toast("Link not ready.","error"); return; }
    try{
      if(navigator.clipboard && navigator.clipboard.writeText) await navigator.clipboard.writeText(v);
      else { input.removeAttribute("readonly"); input.select(); input.setSelectionRange(0,99999); document.execCommand("copy"); input.setAttribute("readonly","readonly"); }
      U.toast("Copied!","success"); TG.hapticNotify("success");
    } catch(e){ U.toast("Copy failed.","error"); }
  });
}

async function load(force){
  if(loaded && !force) return;
  if(!window.Fox.state.authenticated){ renderPreview(); loaded=true; return; }
  try{ const d=await API.get("/api/referrals"); render(d); loaded=true; }
  catch(err){ const h=document.getElementById("ref-milestones"); if(h) h.innerHTML='<li class="empty-state">'+U.escapeHtml(err.message||"Could not load.")+"</li>"; }
}

window.Fox=window.Fox||{}; window.Fox.screenHooks=window.Fox.screenHooks||{};
window.Fox.screenHooks.friends=()=>{ initCopy(); load(false); };
window.Fox.referrals={ load, initCopy };
})();
