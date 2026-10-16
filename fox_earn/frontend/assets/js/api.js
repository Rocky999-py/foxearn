(function(){
"use strict";
const CFG = window.FOX_CONFIG;
class ApiError extends Error{ constructor(m,s,c,d){ super(m); this.name="ApiError"; this.status=s||0; this.code=c||"unknown_error"; this.details=d||null; } }
const state={ token:null, online:true, onUnauthorized:null };

function loadToken(){ try{ state.token=localStorage.getItem(CFG.TOKEN_STORAGE_KEY)||null; }catch(e){ state.token=null; } return state.token; }
function setToken(t){ state.token=t||null; try{ if(t) localStorage.setItem(CFG.TOKEN_STORAGE_KEY,t); else localStorage.removeItem(CFG.TOKEN_STORAGE_KEY); }catch(e){} }
function clearToken(){ setToken(null); }
function getToken(){ return state.token; }

function apiUrl(p){
  const b=String(CFG.API_BASE_URL||"").replace(/\/+$/,"");
  const s=p.startsWith("/")?p:"/"+p;
  return b+s;
}
function isConfigured(){
  const b=String(CFG.API_BASE_URL||"");
  if(b.length===0) return true;  // same-origin is always fine
  return b.indexOf("REPLACE_WITH_YOUR_BACKEND_URL")===-1;
}

async function request(method,path,body,options){
  const opts=options||{};
  if(!isConfigured()) throw new ApiError("Backend URL not configured.",0,"not_configured");
  const ctrl=new AbortController();
  const timer=setTimeout(()=>ctrl.abort(), CFG.REQUEST_TIMEOUT_MS);
  const headers={"Accept":"application/json"};
  if(body!==undefined && body!==null) headers["Content-Type"]="application/json";
  if(state.token && !opts.skipAuth) headers["Authorization"]="Bearer "+state.token;
  if(opts.idempotencyKey) headers["Idempotency-Key"]=opts.idempotencyKey;
  headers["ngrok-skip-browser-warning"]="true";
  let r;
  try{
    r=await fetch(apiUrl(path),{method,headers,
      body:(body!==undefined&&body!==null)?JSON.stringify(body):undefined,
      signal:ctrl.signal,cache:"no-store",credentials:"omit",mode:"cors"});
    state.online=true;
  } catch(err){
    clearTimeout(timer); state.online=false;
    if(err&&err.name==="AbortError") throw new ApiError("Server took too long.",0,"timeout");
    throw new ApiError("Cannot reach server.",0,"network_error");
  }
  clearTimeout(timer);
  let payload=null;
  const text=await r.text().catch(()=>"");
  if(text){ try{ payload=JSON.parse(text); }catch(e){ payload={detail:text.slice(0,400)}; } }
  if(!r.ok){
    const detail=payload&&payload.detail;
    let message="Request failed.", code="http_"+r.status;
    if(typeof detail==="string") message=detail;
    else if(detail&&typeof detail==="object"){ message=detail.message||detail.msg||message; code=detail.code||code; }
    else if(Array.isArray(detail)&&detail.length){
      const f=detail[0]||{}; const loc=Array.isArray(f.loc)?f.loc.join("."):"";
      message=(loc?loc+": ":"")+(f.msg||"Invalid input."); code="validation_error";
    }
    if(r.status===401){ clearToken(); if(typeof state.onUnauthorized==="function") state.onUnauthorized(); }
    throw new ApiError(message,r.status,code,payload);
  }
  return payload;
}

window.Fox=window.Fox||{};
window.Fox.api={
  ApiError, loadToken, setToken, getToken, clearToken, isConfigured,
  setUnauthorizedHandler(fn){ state.onUnauthorized=fn; },
  isOnline(){ return state.online; },
  get(p,o){ return request("GET",p,undefined,o); },
  post(p,b,o){ return request("POST",p,b,o); },
  patch(p,b,o){ return request("PATCH",p,b,o); },
  del(p,o){ return request("DELETE",p,undefined,o); },
  health(){ return request("GET","/health",undefined,{skipAuth:true}); },
  authenticate(initData){ return request("POST","/api/auth/telegram",{init_data:initData},{skipAuth:true}); }
};
})();
