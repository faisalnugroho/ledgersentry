'use strict';
const $ = s => document.querySelector(s);
const SDK = window.GenLayerSDK;
const RPC = 'https://studio.genlayer.com/api';
const EXPLORER = 'https://explorer-studio.genlayer.com';
let deployment, account, client, selected = null, record = null, busy = false;
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const sleep = ms => new Promise(r => setTimeout(r, ms));
function notice(text, error = false) { $('#notice').textContent = text; $('#notice').className = error ? 'error' : ''; }
function ready() { if (!deployment?.address) throw Error('No verified deployment configured.'); if (!client) throw Error('Create a testnet session first.'); }
async function rpc(method, params) { const response = await fetch(RPC, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({jsonrpc:'2.0',id:1,method,params})}); if (!response.ok) throw Error('RPC unavailable: HTTP '+response.status); const data = await response.json(); if (data.error) throw Error(data.error.message || JSON.stringify(data.error)); return data.result; }
async function read(method, args = []) { ready(); const data = await client.readContract({address:deployment.address,functionName:method,args}); return typeof data === 'string' ? JSON.parse(data) : data; }
function updateActions() {
  const open = record && record.status === 'OPEN', disputed = record && record.status === 'DISPUTED';
  const now = Math.floor(Date.now() / 1000);
  $('#add-evidence-details').hidden = !open;
  $('#dispute-details').hidden = !open;
  $('#add-dispute-evidence-details').hidden = !disputed;
  $('#dispute').disabled = busy || !open;
  const challengeActive = record && record.challenge_deadline > now;
  $('#resolve').disabled = busy || (!open && !(disputed && record.dispute_deadline <= now)) || (!open && !disputed && challengeActive);
  $('#resolve').textContent = disputed && record.dispute_deadline > now ? 'Response window active' : (!open && !disputed && challengeActive) ? 'Challenge period active' : open ? 'Resolve audit' : 'Resolve audit';
}
async function action(fn) { if(busy) return; busy = true; document.querySelectorAll('button').forEach(b=>b.disabled=true); try { await fn(); } catch(e) { notice(e.message || String(e), true); } finally {busy=false; document.querySelectorAll('button').forEach(b=>b.disabled=false); updateActions();} }
async function connect() { if (client) { notice('This tab already has a testnet signing session.'); return; } if (!SDK) throw Error('GenLayer SDK failed to load.'); let pk = sessionStorage.getItem('ledgersentry-burner'); if(!pk) {pk=SDK.generatePrivateKey();sessionStorage.setItem('ledgersentry-burner',pk);} account=SDK.createAccount(pk);client=SDK.createClient({chain:SDK.studionet,account});$('#wallet').textContent='Testnet burner: '+account.address+' · Session-only. Never send real assets.';$('#connect').textContent='Testnet session active';notice('Session active. Requesting testnet faucet…'); await client.request({method:'sim_fundAccount',params:[account.address,1e18]}); await loadAudits();notice('Testnet session ready. No real funds are involved.'); }
async function loadAudits() { const ids=await read('list_audits'); const container=$('#audit-list');container.replaceChildren();for(const id of ids.slice().reverse()) {const button=document.createElement('button');button.className='audit-item'+(id===selected?' selected':'');button.textContent=id;button.onclick=()=>action(()=>loadAudit(id));container.append(button);} if(!ids.length) container.textContent='No on-chain audits yet.'; }
function verdictBadge(v){return v?`<span class="badge ${esc(v)}">${esc(v)}</span>`:''}
function renderAudit(data) { record=data;selected=data.id;$('#audit-actions').hidden=false;
  const reqs=(data.requirements||[]).map((r,i)=>`<li>${esc(r)}</li>`).join('');
  const sources=[{index:0,url:data.subject.url,digest:data.subject.digest}].concat((data.evidence||[]).map(e=>({index:e.index+1,url:e.url,digest:e.digest}))).concat((data.dispute||[]).map(e=>({index:'D'+e.index,url:e.url,digest:e.digest})));
  $('#audit-view').innerHTML=`<div class="row"><div><p class="eyebrow">${esc(data.id)}</p><h2>${esc(data.title)}</h2></div><span class="badge ${esc(data.status)}">${esc(data.status)}</span>${verdictBadge(data.result?.verdict)}</div>
  <ol class="reqs">${reqs}</ol>
  <p class="mono muted">Audit owner: ${esc(data.owner)}</p>
  ${data.status==='DISPUTED'?`<p class="mono">Dispute deadline (chain time): ${data.dispute_deadline}</p>`:''}
  <p class="fine">${(data.evidence||[]).length} original evidence · ${(data.dispute||[]).length} dispute evidence · window ${data.window_seconds}s</p>
  <div id="ledger">${sources.length?sources.map(s=>`<article class="source"><div class="row"><h3>Source ${s.index}</h3><span class="mono muted">${esc(s.digest.slice(0,16))}…</span></div><a class="fine" href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.url)}</a></article>`).join(''):'<p class="muted">No sources committed.</p>'}</div>
  ${data.result?.verdict?`<div class="result"><p>${esc(data.result.reason)}</p><p class="fine">Labels: ${esc((data.result.labels||[]).join(' · '))}</p><div class="manifest mono fine">${(data.result.manifest||[]).map(m=>`Source ${m.index}: ${m.digest_ok?'verified':'UNUSABLE'} (${m.bytes} bytes)`).join('<br>')}</div>${(data.result.citations||[]).map(c=>`<blockquote><b>Source ${c.source}</b> — ${esc(c.quote)}</blockquote>`).join('')}<details><summary>Inspect recorded result</summary><pre>${esc(JSON.stringify(data.result,null,2))}</pre></details></div>`:'<p class="muted">Not resolved yet.</p>'}`;
  updateActions();document.querySelectorAll('.audit-item').forEach(b=>b.classList.toggle('selected',b.textContent===selected)); }
async function loadAudit(id) { const data=await read('get_audit',[id]);renderAudit(data);notice('Fresh on-chain state loaded.'); }
function successful(tx) {const leader=tx.consensus_data?.leader_receipt?.[0];const execution=tx.tx_execution_result_name||leader?.execution_result;return tx.status==='FINALIZED'&&tx.result_name==='MAJORITY_AGREE'&&['SUCCESS','FINISHED_WITH_RETURN'].includes(execution);}
async function waitTransaction(hash) { for(let i=0;i<90;i++){try{const tx=await rpc('eth_getTransactionByHash',[hash]);if(tx&&['FINALIZED','UNDETERMINED','CANCELED'].includes(tx.status)){if(!successful(tx))throw Error('Transaction finished without confirmed successful execution. Inspect its explorer receipt; no success is assumed.');return tx;}}catch(e){if(e.message.includes('without confirmed'))throw e;if(i===89)throw e;}await sleep(10000);}throw Error('Transaction still pending. Do not resubmit blindly; inspect the saved hash and refresh on-chain state.'); }
async function write(method,args,aid) {ready();notice('Sending '+method+' to Studionet…');const hash=await client.writeContract({address:deployment.address,functionName:method,args,value:0n,leaderOnly:false});sessionStorage.setItem('ledgersentry-last-tx',hash);$('#tx').innerHTML=`Transaction: <a href="${EXPLORER}/tx/${esc(hash)}" target="_blank" rel="noopener">${esc(hash)} ↗</a>`;notice('Transaction submitted. Waiting for consensus AND successful execution…');await waitTransaction(hash);await loadAudit(aid);await loadAudits();notice('Execution verified and on-chain state read back.');return hash;}
async function hashInput(urlInput,digestInput) {const url=urlInput.value; if(!/^https:\/\/raw\.githubusercontent\.com\/[A-Za-z0-9_-]+\/[A-Za-z0-9_.-]+\/[0-9a-f]{40}\/[A-Za-z0-9_./-]+\.(md|txt)$/.test(url)||url.split('/').slice(3).some(x=>['','.','..'].includes(x)))throw Error('Use a commit-pinned raw.githubusercontent.com .md or .txt URL.');const response=await fetch(url);if(!response.ok)throw Error('Source fetch failed: HTTP '+response.status);const bytes=await response.arrayBuffer();if(bytes.byteLength<50||bytes.byteLength>3000)throw Error('Subject must contain 50–3,000 UTF-8 bytes.');new TextDecoder('utf-8',{fatal:true}).decode(bytes);const hash=await crypto.subtle.digest('SHA-256',bytes);digestInput.value=Array.from(new Uint8Array(hash),b=>b.toString(16).padStart(2,'0')).join('');notice('SHA-256 computed from fetched source bytes. No transaction sent.');}
$('#connect').onclick=()=>action(connect);$('#refresh').onclick=()=>action(loadAudits);$('#reload').onclick=()=>action(()=>loadAudit(selected));
$('#dispute').onclick=()=>action(()=>write('open_dispute',[selected],selected));
$('#resolve').onclick=()=>action(()=>write('resolve',[selected],selected));
$('#hash').onclick=()=>action(()=>{const f=$('#audit-form');return hashInput(f.elements.subject_uri,f.elements.subject_digest);});
$('#audit-form').onsubmit=e=>{e.preventDefault();action(async()=>{const d=new FormData(e.target);let reqs;try{reqs=JSON.parse(d.get('requirements_json'));}catch(_){throw Error('Requirements must be a JSON array of strings.');}await write('open_audit',[d.get('id'),d.get('title'),d.get('subject_uri'),d.get('subject_digest'),JSON.stringify(reqs),Number(d.get('window_seconds')),Number(d.get('challenge_seconds'))],d.get('id'));});};
$('#ev-hash').onclick=()=>action(()=>{const f=$('#evidence-form');return hashInput(f.elements.url,f.elements.digest);});
$('#evidence-form').onsubmit=e=>{e.preventDefault();action(async()=>{const d=new FormData(e.target);await write('add_evidence',[selected,d.get('url'),d.get('digest')],selected);});};
$('#de-hash').onclick=()=>action(()=>{const f=$('#dispute-evidence-form');return hashInput(f.elements.url,f.elements.digest);});
$('#dispute-evidence-form').onsubmit=e=>{e.preventDefault();action(async()=>{const d=new FormData(e.target);await write('add_dispute_evidence',[selected,d.get('url'),d.get('digest')],selected);});};
(async()=>{try{const response=await fetch('./deployment.json',{cache:'no-store'});if(!response.ok)throw Error('Deployment configuration is unavailable.');deployment=await response.json();if(!/^0x[0-9a-fA-F]{40}$/.test(deployment.address||''))throw Error('No verified contract address configured yet.');$('#deployment').innerHTML=`Contract: <a href="${EXPLORER}/contracts/${esc(deployment.address)}" target="_blank" rel="noopener">${esc(deployment.address)} ↗</a>`;const last=sessionStorage.getItem('ledgersentry-last-tx');if(/^0x[0-9a-fA-F]{64}$/.test(last||''))$('#tx').innerHTML=`Last transaction in this tab: <a href="${EXPLORER}/tx/${last}" target="_blank" rel="noopener">${last} ↗</a>`;}catch(e){notice(e.message,true);$('#deployment').textContent='Deployment unavailable — writes disabled until configured.';}})();
window.LedgerSentry={successful,renderAudit};
