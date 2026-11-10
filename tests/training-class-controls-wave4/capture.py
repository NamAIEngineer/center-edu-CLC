"""Run real renderer handlers through configured ORCA DOM; never app auth/DB.
Usage: python3 tests/training-class-controls-wave4/capture.py BASE_URL PAGE_ID EVIDENCE_DIR
Start serve.py separately; close its own session after capture.
"""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
base, page, out = sys.argv[1:]
out = Path(out); out.mkdir(parents=True, exist_ok=True)
def cli(*args):
    result = subprocess.run(['orca', *args, '--page', page, '--json'], text=True, capture_output=True, timeout=30)
    data = json.loads(result.stdout)
    if not data.get('ok'): raise RuntimeError(data)
    return data
def evaluate(expression):
    data = cli('eval','--expression',expression)
    value = data['result']['result']
    return json.loads(value) if isinstance(value,str) else value
receipts = {'scope':'real DOM + real route handlers; synthetic API fixture only; no app shell/auth/DB/reference', 'page':page, 'captures':[]}
for phase in ['before','after']:
    url = base + '/tests/training-class-controls-wave4/harness.html' + ('?baseline' if phase=='before' else '')
    cli('goto','--url',url)
    for width,height in [(1440,900),(390,844)]:
        cli('exec','--command',f'set viewport {width} {height}')
        probe=evaluate('JSON.stringify(probe())')
        assert probe['viewport']==[width,height],probe
        shot=cli('screenshot')['result']
        destination=out/f'{phase}-{width}x{height}.png'
        shutil.copyfile(shot['path'],destination)
        receipts['captures'].append({'phase':phase,'probe':probe,'screenshot':destination.name,'sha256':hashlib.sha256(destination.read_bytes()).hexdigest()})
    if phase=='before':
        receipts['baseline_multi']=evaluate('(()=>{const s=control("status");s.options[1].selected=true;s.options[2].selected=true;s.dispatchEvent(new Event("change",{bubbles:true}));return new Promise(resolve=>setTimeout(()=>resolve(JSON.stringify({selected:selected("status"),filters:document.querySelector("#screen").__trainingClassFilterState.filters,calls})),220));})()')
    else:
        receipts['handler_tests']=evaluate('runControls().then(x=>JSON.stringify(x)).catch(e=>JSON.stringify({error:String(e),probe:probe()}))')
        if receipts['handler_tests'].get('error'):
            (out/'browser-controls.json').write_text(json.dumps(receipts,ensure_ascii=False,indent=2)+'\n')
            raise AssertionError(receipts['handler_tests'])
(out/'browser-controls.json').write_text(json.dumps(receipts,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'captures':len(receipts['captures']),'checks':len(receipts['handler_tests']['checks']),'all_pass':all(item['pass'] for item in receipts['handler_tests']['checks']),'baseline_selected':receipts['baseline_multi']['selected']},ensure_ascii=False))
