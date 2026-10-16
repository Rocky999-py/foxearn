(function(){
"use strict";
const tg = (window.Telegram && window.Telegram.WebApp) ? window.Telegram.WebApp : null;
const state={ available:!!tg, initData:"", user:null, startParam:"", colorScheme:"dark", version:"0" };
function init(){
  if(!tg) return {available:false, initData:"", user:null, startParam:""};
  try{ tg.ready(); }catch(e){}
  try{ tg.expand(); }catch(e){}
  try{ if(typeof tg.disableVerticalSwipes==="function") tg.disableVerticalSwipes(); }catch(e){}
  try{ if(typeof tg.setHeaderColor==="function") tg.setHeaderColor("#070d1b"); if(typeof tg.setBackgroundColor==="function") tg.setBackgroundColor("#070d1b"); }catch(e){}
  state.initData=tg.initData||"";
  state.version=String(tg.version||"0");
  state.colorScheme=tg.colorScheme||"dark";
  state.startParam=(tg.initDataUnsafe&&tg.initDataUnsafe.start_param)||"";
  if(tg.initDataUnsafe&&tg.initDataUnsafe.user) state.user=tg.initDataUnsafe.user;
  return { available:true, initData:state.initData, user:state.user, startParam:state.startParam };
}
function hasValidInitData(){ return typeof state.initData==="string" && state.initData.length>20 && state.initData.indexOf("hash=")!==-1; }
function isInsideTelegram(){ return state.available && hasValidInitData(); }
function hapticImpact(s){ if(!tg||!tg.HapticFeedback)return; try{ tg.HapticFeedback.impactOccurred(s||"light"); }catch(e){} }
function hapticNotify(t){ if(!tg||!tg.HapticFeedback)return; try{ tg.HapticFeedback.notificationOccurred(t||"success"); }catch(e){} }
function openLink(u,tryIV){ if(!u)return; if(tg&&typeof tg.openLink==="function"){ try{ tg.openLink(u,{try_instant_view:!!tryIV}); return; }catch(e){} } window.open(u,"_blank","noopener,noreferrer"); }
function openTelegramLink(u){ if(!u)return; if(tg&&typeof tg.openTelegramLink==="function"){ try{ tg.openTelegramLink(u); return; }catch(e){} } window.open(u,"_blank","noopener,noreferrer"); }
function shareUrl(u,t){ const s="https://t.me/share/url?url="+encodeURIComponent(u)+"&text="+encodeURIComponent(t||""); openTelegramLink(s); }
function getDisplayName(){ const u=state.user; if(!u)return ""; const f=[u.first_name,u.last_name].filter(Boolean).join(" ").trim(); return f||u.username||""; }
function getPhotoUrl(){ const u=state.user; return (u&&u.photo_url)?u.photo_url:""; }
window.Fox=window.Fox||{};
window.Fox.tg={ init, state, isInsideTelegram, hasValidInitData, hapticImpact, hapticNotify, openLink, openTelegramLink, shareUrl, getDisplayName, getPhotoUrl };
})();
