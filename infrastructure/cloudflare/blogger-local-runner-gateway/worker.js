const REST_ALLOWED = new Set([
  'GET /v1/health',
  'POST /v1/audit',
  'POST /v1/preflight',
  'POST /v1/create-blog',
  'POST /v1/preflight/settings-profile',
  'POST /v1/configure-settings',
  'POST /v1/adopt-model-v20'
]);

const DEFAULT_TZ = '(GMT-03:00) Horário Padrão de Brasília – São Paulo';
const BASE = 'https://blogger-local-runner-gateway.comercebem-ar.workers.dev';
const RESOURCE = BASE + '/mcp';
const SCOPES = ['mcp','offline_access'];

const TOOLS = [
  {name:'health',description:'Verifica se o Blogger local runner está ativo e autenticado.',inputSchema:{type:'object',properties:{},additionalProperties:false},annotations:{readOnlyHint:true,destructiveHint:false,idempotentHint:true,openWorldHint:false}},
  {name:'audit',description:'Executa auditoria segura e somente leitura do Chrome oficial/Blogger via CDP loopback.',inputSchema:{type:'object',properties:{},additionalProperties:false},annotations:{readOnlyHint:true,destructiveHint:false,idempotentHint:true,openWorldHint:false}},
  {name:'preflight_blog',description:'Valida de forma somente leitura se título e endereço estão prontos para criação de um blog.',inputSchema:{type:'object',properties:{title:{type:'string',minLength:1,maxLength:100},address:{type:'string',minLength:3,maxLength:63,pattern:'^[a-z0-9](?:[a-z0-9-]{1,61}[a-z0-9])?$'}},required:['title','address'],additionalProperties:false},annotations:{readOnlyHint:true,destructiveHint:false,idempotentHint:true,openWorldHint:false}},
  {name:'create_blog',description:'Cria um blog Blogger pelo Chrome oficial. Exige confirmação literal CREATE BLOG e usa proteções contra duplicação e CDP remoto.',inputSchema:{type:'object',properties:{title:{type:'string',minLength:1,maxLength:100},address:{type:'string',minLength:3,maxLength:63,pattern:'^[a-z0-9](?:[a-z0-9-]{1,61}[a-z0-9])?$'},confirm:{type:'string',enum:['CREATE BLOG']}},required:['title','address','confirm'],additionalProperties:false},annotations:{readOnlyHint:false,destructiveHint:false,idempotentHint:false,openWorldHint:true}},
  {name:'preflight_settings',description:'Valida em modo somente leitura o perfil de configurações/SEO para um Blog ID específico.',inputSchema:{type:'object',properties:{expected_blog_id:{type:'string',pattern:'^[0-9]+$'},description:{type:'string',minLength:1,maxLength:500},search_description:{type:'string',minLength:1,maxLength:150},timezone:{type:'string',default:DEFAULT_TZ,maxLength:180}},required:['expected_blog_id','description','search_description'],additionalProperties:false},annotations:{readOnlyHint:true,destructiveHint:false,idempotentHint:true,openWorldHint:false}},
  {name:'configure_settings',description:'Aplica o perfil validado de configurações/SEO no Blog ID esperado. Exige confirmação literal APPLY SETTINGS; robots personalizados permanecem intocados.',inputSchema:{type:'object',properties:{expected_blog_id:{type:'string',pattern:'^[0-9]+$'},description:{type:'string',minLength:1,maxLength:500},search_description:{type:'string',minLength:1,maxLength:150},timezone:{type:'string',default:DEFAULT_TZ,maxLength:180},confirm:{type:'string',enum:['APPLY SETTINGS']}},required:['expected_blog_id','description','search_description','confirm'],additionalProperties:false},annotations:{readOnlyHint:false,destructiveHint:false,idempotentHint:true,openWorldHint:true}},
  {name:'adopt_model_v20',description:'Adota o TEMA MODELO V20 em um Blog ID específico, preservando posts existentes, com backup e validação pública. Exige confirmação literal ADOPT MODEL V20.',inputSchema:{type:'object',properties:{expected_blog_id:{type:'string',pattern:'^[0-9]+$'},blog_title:{type:'string',minLength:1,maxLength:100},blog_url:{type:'string',minLength:12,maxLength:300},palette:{type:'string',enum:['auto','blue','emerald','plum','terracotta','teal','burgundy','indigo','amber'],default:'auto'},confirm:{type:'string',enum:['ADOPT MODEL V20']}},required:['expected_blog_id','blog_title','blog_url','confirm'],additionalProperties:false},annotations:{readOnlyHint:false,destructiveHint:false,idempotentHint:true,openWorldHint:true}}
];

function json(data,status=200,extra={}){return new Response(JSON.stringify(data),{status,headers:{'content-type':'application/json; charset=utf-8','cache-control':'no-store','x-content-type-options':'nosniff',...extra}})}
function b64u(bytes){let s='';for(const b of bytes)s+=String.fromCharCode(b);return btoa(s).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'')}
function fromB64u(s){s=s.replace(/-/g,'+').replace(/_/g,'/');while(s.length%4)s+='=';const raw=atob(s);return Uint8Array.from(raw,c=>c.charCodeAt(0))}
async function oauthKey(env){const d=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(env.OAUTH_SECRET));return crypto.subtle.importKey('raw',d,{name:'AES-GCM'},false,['encrypt','decrypt'])}
async function seal(env,obj){const key=await oauthKey(env);const iv=crypto.getRandomValues(new Uint8Array(12));const plain=new TextEncoder().encode(JSON.stringify(obj));const cipher=new Uint8Array(await crypto.subtle.encrypt({name:'AES-GCM',iv},key,plain));return b64u(iv)+'.'+b64u(cipher)}
async function openSealed(env,token){try{const [a,b]=String(token||'').split('.');if(!a||!b)return null;const key=await oauthKey(env);const plain=await crypto.subtle.decrypt({name:'AES-GCM',iv:fromB64u(a)},key,fromB64u(b));return JSON.parse(new TextDecoder().decode(plain))}catch(_){return null}}
function htmlEscape(s){return String(s??'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;')}
async function runnerFetchToken(env,t,path,method,body){const headers=new Headers({'authorization':'Bearer '+t});if(body!==undefined)headers.set('content-type','application/json');const init={method,headers,redirect:'manual'};if(body!==undefined)init.body=JSON.stringify(body);return env.BLOGGER_RUNNER.fetch(new Request('http://127.0.0.1:8765'+path,init))}
async function validateRunnerToken(env,t){try{return (await runnerFetchToken(env,t,'/v1/health','GET')).status===200}catch(_){return false}}
async function resolveRunnerToken(env,request){const auth=request.headers.get('authorization')||'';if(!auth.startsWith('Bearer '))return null;const bearer=auth.slice(7).trim();const o=await openSealed(env,bearer);const now=Math.floor(Date.now()/1000);if(o&&o.kind==='access'&&o.exp>now&&typeof o.runner_token==='string')return o.runner_token;if(await validateRunnerToken(env,bearer))return bearer;return null}
function oauthUnauthorized(){return json({jsonrpc:'2.0',id:null,error:{code:-32001,message:'Unauthorized'}},401,{'www-authenticate':'Bearer resource_metadata="'+BASE+'/.well-known/oauth-protected-resource"'})}

async function handleToolCall(env,t,name,args){
  const map={
    health:['GET','/v1/health',undefined],
    audit:['POST','/v1/audit',{}],
    preflight_blog:['POST','/v1/preflight',{title:args.title,address:args.address}],
    create_blog:['POST','/v1/create-blog',{title:args.title,address:args.address,confirm:args.confirm}],
    preflight_settings:['POST','/v1/preflight/settings-profile',{expected_blog_id:args.expected_blog_id,description:args.description,search_description:args.search_description,timezone:args.timezone||DEFAULT_TZ}],
    configure_settings:['POST','/v1/configure-settings',{expected_blog_id:args.expected_blog_id,description:args.description,search_description:args.search_description,timezone:args.timezone||DEFAULT_TZ,confirm:args.confirm}],
    adopt_model_v20:['POST','/v1/adopt-model-v20',{expected_blog_id:args.expected_blog_id,blog_title:args.blog_title,blog_url:args.blog_url,palette:args.palette||'auto',confirm:args.confirm}]
  };
  if(!map[name])return{isError:true,content:[{type:'text',text:JSON.stringify({ok:false,error:'unknown_tool'})}]};
  const [method,path,body]=map[name];
  const upstream=await runnerFetchToken(env,t,path,method,body);
  let data;
  try{data=await upstream.json()}catch(_){data={ok:false,error:'invalid_runner_response'}}
  return{isError:upstream.status>=400,content:[{type:'text',text:JSON.stringify(data)}],structuredContent:data}
}

async function handleMcp(request,env){
  if(request.method!=='POST')return new Response('Method Not Allowed',{status:405,headers:{Allow:'POST'}});
  let msg;
  try{msg=await request.json()}catch(_){return json({jsonrpc:'2.0',id:null,error:{code:-32700,message:'Parse error'}},400)}
  if(Array.isArray(msg))return json({jsonrpc:'2.0',id:null,error:{code:-32600,message:'Batch requests are not supported'}},400);
  const t=await resolveRunnerToken(env,request);
  if(!t)return oauthUnauthorized();
  const method=msg?.method;
  const id=Object.prototype.hasOwnProperty.call(msg||{},'id')?msg.id:null;
  if(method==='initialize'){
    const requested=msg?.params?.protocolVersion;
    const supported=['2026-07-28','2025-11-25','2025-06-18','2025-03-26'];
    const protocolVersion=supported.includes(requested)?requested:'2026-07-28';
    return json({jsonrpc:'2.0',id,result:{protocolVersion,capabilities:{tools:{listChanged:false}},serverInfo:{name:'blogger-local-runner',version:'0.4-mcp-oauth'}}})
  }
  if(method==='notifications/initialized')return new Response(null,{status:204});
  if(method==='ping')return json({jsonrpc:'2.0',id,result:{}});
  if(method==='tools/list')return json({jsonrpc:'2.0',id,result:{tools:TOOLS}});
  if(method==='resources/list')return json({jsonrpc:'2.0',id,result:{resources:[]}});
  if(method==='prompts/list')return json({jsonrpc:'2.0',id,result:{prompts:[]}});
  if(method==='tools/call'){
    const result=await handleToolCall(env,t,msg?.params?.name,msg?.params?.arguments||{});
    return json({jsonrpc:'2.0',id,result})
  }
  return json({jsonrpc:'2.0',id,error:{code:-32601,message:'Method not found'}})
}

function resourceMetadata(){return{resource:RESOURCE,authorization_servers:[BASE],scopes_supported:SCOPES,bearer_methods_supported:['header']}}
function authMetadata(){return{issuer:BASE,authorization_endpoint:BASE+'/oauth/authorize',token_endpoint:BASE+'/oauth/token',registration_endpoint:BASE+'/oauth/register',response_types_supported:['code'],grant_types_supported:['authorization_code','refresh_token'],token_endpoint_auth_methods_supported:['none'],code_challenge_methods_supported:['S256'],scopes_supported:SCOPES}}

async function registerClient(request,env){
  let body;
  try{body=await request.json()}catch(_){return json({error:'invalid_client_metadata'},400)}
  const uris=Array.isArray(body.redirect_uris)?body.redirect_uris.filter(x=>typeof x==='string'&&x.length<2048):[];
  if(!uris.length)return json({error:'invalid_redirect_uri'},400);
  for(const uri of uris){
    try{
      const u=new URL(uri);
      if(u.protocol!=='https:'&&u.hostname!=='localhost'&&u.hostname!=='127.0.0.1')return json({error:'invalid_redirect_uri'},400)
    }catch(_){return json({error:'invalid_redirect_uri'},400)}
  }
  const now=Math.floor(Date.now()/1000);
  const client_id=await seal(env,{kind:'client',redirect_uris:uris,client_name:String(body.client_name||'ChatGPT MCP').slice(0,120),iat:now,exp:now+31536000});
  return json({client_id,client_id_issued_at:now,redirect_uris:uris,client_name:String(body.client_name||'ChatGPT MCP').slice(0,120),token_endpoint_auth_method:'none',grant_types:['authorization_code','refresh_token'],response_types:['code']},201)
}

async function loadClient(env,id,redirect){
  const c=await openSealed(env,id);
  const now=Math.floor(Date.now()/1000);
  if(!c||c.kind!=='client'||c.exp<=now||!Array.isArray(c.redirect_uris)||!c.redirect_uris.includes(redirect))return null;
  return c
}

async function authorizeGet(request,env){
  const u=new URL(request.url),rt=u.searchParams.get('response_type')||'',id=u.searchParams.get('client_id')||'',redirect=u.searchParams.get('redirect_uri')||'',state=u.searchParams.get('state')||'',challenge=u.searchParams.get('code_challenge')||'',method=u.searchParams.get('code_challenge_method')||'',scope=u.searchParams.get('scope')||'mcp offline_access';
  if(rt!=='code'||method!=='S256'||!challenge)return new Response('Solicitação OAuth inválida.',{status:400});
  const client=await loadClient(env,id,redirect);
  if(!client)return new Response('Cliente OAuth inválido.',{status:400});
  const target=new URL(redirect);
  const page='<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Autorizar Blogger Local Runner</title><style>body{font-family:system-ui;max-width:560px;margin:48px auto;padding:0 20px}input{width:100%;box-sizing:border-box;padding:12px;margin:8px 0 16px}button{padding:12px 18px;font-weight:700}.muted{color:#666;font-size:14px}</style></head><body><h1>Blogger Local Runner</h1><p>Autorize <b>'+htmlEscape(client.client_name||'ChatGPT')+'</b> a usar as ferramentas locais do Blogger.</p><p class="muted">Retorno: '+htmlEscape(target.hostname)+'</p><form method="post" action="/oauth/authorize"><input type="hidden" name="client_id" value="'+htmlEscape(id)+'"><input type="hidden" name="redirect_uri" value="'+htmlEscape(redirect)+'"><input type="hidden" name="state" value="'+htmlEscape(state)+'"><input type="hidden" name="code_challenge" value="'+htmlEscape(challenge)+'"><input type="hidden" name="scope" value="'+htmlEscape(scope)+'"><label>Token local do runner</label><input type="password" name="runner_token" required minlength="32" autocomplete="off"><button type="submit">Autorizar ChatGPT</button></form><p class="muted">O token é validado diretamente contra o runner no seu PC.</p></body></html>';
  return new Response(page,{status:200,headers:{'content-type':'text/html; charset=utf-8','cache-control':'no-store','x-frame-options':'DENY','content-security-policy':"default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'"}})
}

async function authorizePost(request,env){
  const f=await request.formData(),id=String(f.get('client_id')||''),redirect=String(f.get('redirect_uri')||''),state=String(f.get('state')||''),challenge=String(f.get('code_challenge')||''),scope=String(f.get('scope')||'mcp offline_access'),runner=String(f.get('runner_token')||'');
  if(!(await loadClient(env,id,redirect))||!challenge)return new Response('Cliente OAuth inválido.',{status:400});
  if(!(await validateRunnerToken(env,runner)))return new Response('Token do runner inválido ou runner indisponível.',{status:401});
  const now=Math.floor(Date.now()/1000);
  const code=await seal(env,{kind:'code',client_id:id,redirect_uri:redirect,code_challenge:challenge,scope,runner_token:runner,iat:now,exp:now+300});
  const out=new URL(redirect);
  out.searchParams.set('code',code);
  if(state)out.searchParams.set('state',state);
  const next=out.toString();
  const page='<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Token validado</title><style>body{font-family:system-ui;max-width:560px;margin:48px auto;padding:0 20px}a{display:inline-block;padding:12px 18px;background:#111;color:#fff;text-decoration:none;border-radius:8px;font-weight:700}.muted{color:#666;font-size:14px}</style></head><body><h1>Token validado</h1><p>O runner no seu PC aceitou o token.</p><p><a href="'+htmlEscape(next)+'">Continuar para o ChatGPT</a></p><p class="muted">O código de autorização expira em poucos minutos.</p></body></html>';
  return new Response(page,{status:200,headers:{'content-type':'text/html; charset=utf-8','cache-control':'no-store','x-frame-options':'DENY','content-security-policy':"default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; frame-ancestors 'none'"}})
}

async function sha256b64u(s){return b64u(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(s))))}

async function tokenEndpoint(request,env){
  let f;
  try{f=await request.formData()}catch(_){return json({error:'invalid_request'},400)}
  const grant=String(f.get('grant_type')||''),now=Math.floor(Date.now()/1000);
  if(grant==='authorization_code'){
    const c=await openSealed(env,String(f.get('code')||'')),id=String(f.get('client_id')||''),redirect=String(f.get('redirect_uri')||''),verifier=String(f.get('code_verifier')||'');
    if(!c||c.kind!=='code'||c.exp<=now||c.client_id!==id||c.redirect_uri!==redirect||!verifier||(await sha256b64u(verifier))!==c.code_challenge)return json({error:'invalid_grant'},400);
    const access=await seal(env,{kind:'access',runner_token:c.runner_token,scope:c.scope,iat:now,exp:now+3600});
    const refresh=await seal(env,{kind:'refresh',runner_token:c.runner_token,scope:c.scope,iat:now,exp:now+2592000});
    return json({access_token:access,token_type:'Bearer',expires_in:3600,refresh_token:refresh,scope:c.scope})
  }
  if(grant==='refresh_token'){
    const r=await openSealed(env,String(f.get('refresh_token')||''));
    if(!r||r.kind!=='refresh'||r.exp<=now||!(await validateRunnerToken(env,r.runner_token)))return json({error:'invalid_grant'},400);
    const access=await seal(env,{kind:'access',runner_token:r.runner_token,scope:r.scope,iat:now,exp:now+3600});
    const refresh=await seal(env,{kind:'refresh',runner_token:r.runner_token,scope:r.scope,iat:now,exp:now+2592000});
    return json({access_token:access,token_type:'Bearer',expires_in:3600,refresh_token:refresh,scope:r.scope})
  }
  return json({error:'unsupported_grant_type'},400)
}

async function handleRest(request,env){
  const incoming=new URL(request.url),key=request.method.toUpperCase()+' '+incoming.pathname;
  if(!REST_ALLOWED.has(key))return json({ok:false,error:'not_found'},404);
  const target=new URL('http://127.0.0.1:8765'+incoming.pathname+incoming.search);
  const headers=new Headers(request.headers);
  for(const h of ['cf-connecting-ip','cf-ipcountry','cf-ray','cf-visitor','x-forwarded-proto'])headers.delete(h);
  const init={method:request.method,headers,redirect:'manual'};
  if(!['GET','HEAD'].includes(request.method.toUpperCase()))init.body=request.body;
  try{
    const upstream=await env.BLOGGER_RUNNER.fetch(new Request(target,init));
    const outHeaders=new Headers(upstream.headers);
    outHeaders.set('cache-control','no-store');
    outHeaders.set('x-content-type-options','nosniff');
    return new Response(upstream.body,{status:upstream.status,headers:outHeaders})
  }catch(_){return json({ok:false,error:'runner_unavailable'},503)}
}

export default{
  async fetch(request,env){
    const url=new URL(request.url);
    if(url.pathname==='/mcp')return handleMcp(request,env);
    if(url.pathname==='/.well-known/oauth-protected-resource'||url.pathname==='/.well-known/oauth-protected-resource/mcp')return json(resourceMetadata());
    if(url.pathname==='/.well-known/oauth-authorization-server')return json(authMetadata());
    if(url.pathname==='/oauth/register'&&request.method==='POST')return registerClient(request,env);
    if(url.pathname==='/oauth/authorize'&&request.method==='GET')return authorizeGet(request,env);
    if(url.pathname==='/oauth/authorize'&&request.method==='POST')return authorizePost(request,env);
    if(url.pathname==='/oauth/token'&&request.method==='POST')return tokenEndpoint(request,env);
    return handleRest(request,env)
  }
};
