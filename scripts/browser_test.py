"""Browser integration tests with explicitly mocked SDK/RPC, no live claims."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[1]
ADDRESS = '0x' + 'a' * 40
MOCK = '''window.GenLayerSDK={studionet:{},generatePrivateKey:()=>\"0xmock\",createAccount:()=>({address:\"0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\"}),createClient:()=>({request:async()=>true,readContract:async({functionName})=>JSON.stringify(functionName==='list_audits'?['ui-audit']:window.fixture),writeContract:async(args)=>{window.sent=args;if(window.failWrite)throw Error('network down');return '0x'+'b'.repeat(64)}})};'''
fixture={'id':'ui-audit','title':'UI audit','owner':ADDRESS,'status':'RESOLVED','dispute_deadline':0,'window_seconds':3600,
 'requirements':['Requirement one about supply.','Requirement two about deployer.','Requirement three about locks.'],
 'subject':{'url':'https://raw.githubusercontent.com/example/repo/'+'a'*40+'/subject.md','digest':'c'*64},
 'evidence':[{'index':0,'url':'https://raw.githubusercontent.com/example/repo/'+'a'*40+'/dash.md','digest':'d'*64}],
 'dispute':[],
 'result':{'verdict':'COMPLIANT','labels':['PASS','PASS','PASS'],'reason':'Grounded test fixture only, not live consensus.',
           'citations':[{'source':0,'quote':'Fixture subject text with a grounded citation quote.'}],
           'manifest':[{'index':0,'bytes':120,'digest_ok':True},{'index':1,'bytes':90,'digest_ok':True}]}}
results=[]
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,args=['--no-sandbox'])
 for width in [1440,390]:
  page=browser.new_page(viewport={'width':width,'height':1000})
  errors=[]
  page.on('pageerror',lambda e:errors.append(str(e)))
  page.route('**/genlayer-sdk.bundle.js',lambda r:r.fulfill(body=MOCK,content_type='application/javascript'))
  page.route('**/deployment.json',lambda r:r.fulfill(json={'address':ADDRESS}))
  page.route('**/studio.genlayer.com/api',lambda r:r.fulfill(json={'jsonrpc':'2.0','id':1,'result':{'status':'FINALIZED','result_name':'MAJORITY_AGREE','tx_execution_result_name':'FINISHED_WITH_RETURN'}}))
  page.add_init_script('window.fixture='+json.dumps(fixture))
  page.goto('http://127.0.0.1:8766/')
  page.wait_for_function("document.querySelector('#deployment').textContent.includes('0x')")
  page.click('#connect');page.wait_for_function("document.querySelector('#notice').textContent.includes('ready')",timeout=60000)
  page.click('.audit-item');page.wait_for_selector('#ledger .source')
  assert page.locator('#audit-view h2').inner_text()=='UI audit'
  assert page.locator('#audit-view .COMPLIANT').count()>=1
  assert page.locator('#dispute').is_disabled()
  assert page.locator('#resolve').is_disabled()
  assert page.evaluate('window.xss') is None
  assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
  assert page.evaluate("LedgerSentry.successful({status:'FINALIZED',result_name:'MAJORITY_AGREE',tx_execution_result_name:'FINISHED_WITH_ERROR'})") is False
  assert page.evaluate("LedgerSentry.successful({status:'FINALIZED',result_name:'MAJORITY_AGREE'})") is False
  page.locator('summary').filter(has_text='Open a new audit').click()
  page.locator('#audit-form input[name=id]').fill('ui-created')
  page.locator('#audit-form input[name=title]').fill('Created by browser test')
  page.locator('#audit-form input[name=subject_uri]').fill('https://raw.githubusercontent.com/example/repo/'+'a'*40+'/subject.md')
  page.locator('#audit-form input[name=subject_digest]').fill('c'*64)
  page.click('#audit-form button[type=submit]');page.wait_for_function("document.querySelector('#notice').textContent.includes('Execution verified')",timeout=60000)
  assert page.evaluate('window.sent.functionName')=='open_audit'
  assert page.evaluate('window.sent.args[0]')=='ui-created'
  page.evaluate('window.failWrite=true')
  page.click('#audit-form button[type=submit]');page.wait_for_function("document.querySelector('#notice').textContent.includes('network down')",timeout=60000)
  assert not errors, errors
  page.screenshot(path=str(ROOT/f'evidence/ui-{width}.png'),full_page=True)
  results.append({'width':width,'checks':['audit_read','ledger','terminal_guards','escaped_content','no_overflow','receipt_fail_closed','write_args','write_readback','network_failure','no_js_errors'],'passed':True,'mode':'MOCKED SDK/RPC'})
  page.close()
 browser.close()
(ROOT/'evidence/browser-tests.json').write_text(json.dumps(results,indent=2))
print(json.dumps(results,indent=2))
print('BROWSER_TEST_PASS')
