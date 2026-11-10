"""Capture exact CLI receipts; no reconstructed screenshots or product rows."""
import hashlib
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

base, page, evidence, visual = sys.argv[1:]
evidence, visual = Path(evidence), Path(visual)
evidence.mkdir(parents=True, exist_ok=True)
visual.mkdir(parents=True, exist_ok=True)
commands = []


def cli(*args):
    command = ['orca', *args, '--page', page, '--json']
    result = subprocess.run(command, capture_output=True, text=True, timeout=45)
    data = json.loads(result.stdout)
    commands.append({'argv': command, 'response': data})
    if not data.get('ok'):
        raise RuntimeError(data)
    return data['result']


def evaluate(expression):
    data = cli('eval', '--expression', expression)['result']
    return json.loads(data) if isinstance(data, str) else data


probe = '''JSON.stringify((()=>{
 const screen=document.querySelector('#screen');
 const rect=n=>n?.getBoundingClientRect().toJSON();
 const dates=[...screen.querySelectorAll('[data-date-text]')];
 return {ready:window.ready,error:window.replayError,viewport:[innerWidth,innerHeight],
  scroll:[scrollX,scrollY],document:[document.documentElement.clientWidth,document.documentElement.scrollWidth],
  topbar:rect(document.querySelector('.topbar')),sidebar:rect(document.querySelector('.sidebar')),
  strip:rect(screen.querySelector('.training-observed-filters')),
  actions:[...screen.querySelectorAll('.training-observed-actions button')].map(n=>({text:n.textContent,rect:rect(n)})),
  dates:dates.map(n=>({key:n.dataset.classFilter,type:n.type,placeholder:n.placeholder,rect:rect(n)})),
  triggers:[...screen.querySelectorAll('.class-filter-multiselect')].map(n=>({text:n.textContent,rect:rect(n)})),
  rows:screen.querySelectorAll('tbody tr[data-class-id]').length,
  table:{rect:rect(screen.querySelector('.table-wrap')),scrollWidth:screen.querySelector('.table-wrap').scrollWidth,clientWidth:screen.querySelector('.table-wrap').clientWidth},
  authenticatedUser:window.CenterEdu.state.user,
  guard:typeof normalizeObservedControls==='function',
  resources:performance.getEntriesByType('resource').map(n=>new URL(n.name).pathname)};
})())'''

receipts = {'scope': 'exact canonical shell assets; explicit local empty API; no auth session or DB', 'captures': []}
for phase in ['before', 'after']:
    cli('goto', '--url', base + '/visual.html' + ('?before' if phase == 'before' else ''))
    time.sleep(.5)
    for width, height in [(1440, 900), (390, 844)]:
        cli('exec', '--command', f'set viewport {width} {height}')
        evaluate('window.scrollTo(0,0); true')
        time.sleep(.15)
        value = evaluate(probe)
        assert value['ready'] and value['viewport'] == [width, height], value
        name = f'{phase}-empty-shell-{width}x{height}-top.png'
        shutil.copyfile(cli('screenshot')['path'], visual / name)
        receipts['captures'].append({'phase': phase, 'probe': value, 'image': name})
        if phase == 'after':
            evaluate('window.scrollTo(0,600); true')
            time.sleep(.15)
            value = evaluate(probe)
            name = f'{phase}-empty-shell-{width}x{height}-scrolled.png'
            shutil.copyfile(cli('screenshot')['path'], visual / name)
            receipts['captures'].append({'phase': phase, 'probe': value, 'image': name})

cli('goto', '--url', base + '/harness.html')
time.sleep(.3)
for width, height in [(1440, 900), (390, 844)]:
    cli('exec', '--command', f'set viewport {width} {height}')
    result = evaluate('runControls().then(x=>JSON.stringify(x))')
    assert result['probe']['viewport'] == [width, height], result
    assert all(check['pass'] for check in result['checks']), result
    (evidence / f'handlers-{width}x{height}.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')

for capture in receipts['captures']:
    capture['sha256'] = hashlib.sha256((visual / capture['image']).read_bytes()).hexdigest()
(evidence / 'empty-shell-receipts.json').write_text(json.dumps(receipts, ensure_ascii=False, indent=2)+'\n')
(evidence / 'commands-dom.json').write_text(json.dumps(commands, ensure_ascii=False, indent=2)+'\n')
print(json.dumps({'captures': len(receipts['captures']), 'handlerChecksPerViewport':len(result['checks'])}))
