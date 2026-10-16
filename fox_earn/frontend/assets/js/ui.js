(function(){
"use strict";
const el={};
function cache(){ el.view=document.getElementById("view"); el.bottomNav=document.getElementById("bottom-nav"); el.backBtn=document.getElementById("back-btn"); el.refreshBtn=document.getElementById("refresh-btn"); el.toastHost=document.getElementById("toast-host"); el.banner=document.getElementById("status-banner"); el.bannerText=document.getElementById("status-banner-text"); el.bootLoader=document.getElementById("boot-loader"); }
function escapeHtml(v){ if(v===null||v===undefined)return ""; return String(v).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;"); }
function formatNumber(v){ const n=Number(v); if(!isFinite(n))return "0"; return n.toLocaleString("en-US"); }
function formatUSD(cents){ const n=Number(cents||0)/100; if(!isFinite(n))return "$0.00"; return "$"+n.toFixed(2); }
function formatDate(iso){ if(!iso)return "—"; const d=new Date(iso); if(isNaN(d.getTime()))return "—"; const M=["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]; return d.getDate()+" "+M[d.getMonth()]+" "+d.getFullYear(); }
function formatDateTime(iso){ if(!iso)return "—"; const d=new Date(iso); if(isNaN(d.getTime()))return "—"; const hh=String(d.getHours()).padStart(2,"0"); const mm=String(d.getMinutes()).padStart(2,"0"); return formatDate(iso)+" · "+hh+":"+mm; }
function toast(message,kind,durationMs){ if(!el.toastHost)return; const t=kind||"info"; const n=document.createElement("div"); n.className="toast toast-"+t; n.textContent=String(message); el.toastHost.appendChild(n); const life=durationMs||(t==="error"?4200:2600); setTimeout(()=>{ n.classList.add("out"); setTimeout(()=>{ if(n.parentNode) n.parentNode.removeChild(n); },260); },life); }
function showBanner(text,kind){ if(!el.banner||!el.bannerText)return; el.bannerText.textContent=text; el.banner.setAttribute("data-kind",kind||"ok"); el.banner.hidden=false; }
function hideBanner(){ if(el.banner) el.banner.hidden=true; }
function hideBootLoader(){ if(el.bootLoader) el.bootLoader.classList.add("is-hidden"); }
const SUB_SCREENS=["transactions","wallet"];
let currentScreen="home", previousScreen="home";
function showScreen(name){
  const target=document.getElementById("screen-"+name); if(!target) return;
  if(name!==currentScreen){ previousScreen=currentScreen; currentScreen=name; }
  document.querySelectorAll(".screen").forEach(s=>{ s.hidden=(s.id!=="screen-"+name); });
  const isSub=SUB_SCREENS.indexOf(name)!==-1;
  if(el.bottomNav) el.bottomNav.hidden=isSub;
  if(el.backBtn) el.backBtn.hidden=!isSub;
  if(el.bottomNav&&!isSub) el.bottomNav.querySelectorAll(".nav-btn").forEach(b=>b.classList.toggle("is-active",b.getAttribute("data-nav")===name));
  if(el.view) el.view.scrollTop=0; window.scrollTo(0,0);
  const hooks=window.Fox.screenHooks||{}; if(typeof hooks[name]==="function"){ try{ hooks[name](); }catch(e){} }
}
function goBack(){ showScreen(previousScreen&&previousScreen!==currentScreen?previousScreen:"home"); }
function setLoading(btn,loading,text){ if(!btn)return; if(loading){ if(!btn.dataset.originalText) btn.dataset.originalText=btn.textContent; btn.disabled=true; btn.textContent=text||"Please wait…"; } else { btn.disabled=false; if(btn.dataset.originalText){ btn.textContent=btn.dataset.originalText; delete btn.dataset.originalText; } } }
window.Fox=window.Fox||{};
window.Fox.ui={ init:cache, el, escapeHtml, formatNumber, formatUSD, formatDate, formatDateTime, toast, showBanner, hideBanner, hideBootLoader, showScreen, goBack, setLoading };
})();
