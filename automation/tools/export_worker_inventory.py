#!/usr/bin/env python3
"""ABUTRON safe read-only current worker inventory, for PUBLIC code review."""
import collections,datetime,hashlib,json,re,subprocess
from pathlib import Path
O=Path('/tmp/abutron-automation-export-20261118');O.mkdir(mode=0o700,parents=True)
NOW=datetime.datetime.now(datetime.timezone.utc).isoformat()
PREFIX=re.compile(r'^(abutron|apex|fp-|deriv|mt5|restic|actions\.runner)',re.I)
SENSITIVE=re.compile(r'(?<![a-zA-Z0-9])[a-f0-9]{32}(?![a-zA-Z0-9])',re.I)
LOGIN=re.compile(r'(?<!\w)\d{5,12}(?!\w)')
CATEGORY=[
('recovery_backup',r'backup|restic|offsite|cold.archive|restore|recovery|snapshot'),
('risk_compliance',r'owner.risk|risk.guard|risk-|exposure|equity|stop.risk|loss.guard|trailing|drawdown'),
('execution_reconciliation',r'order|dispatch|ack|receipt|reconcil|preflight|single.writer|bridge|reservation'),
('evidence_market_data',r'market|candle|history|quote|broker.native|feed|tick|m5|hcc|native.cost'),
('model_research',r'brain|trainer|train-|research|qlib|rdagent|learning|shadow|candidate|oos|holdout|correlation|confidence|paper|signal'),
('crm_licensing_portal',r'crm|licens|portal|signup|client|v7|admin|account|mailer|web'),
('mt5_runtime',r'mt5|wine|deriv|fpmarkets|xvfb|terminal'),
('infrastructure_operations',r'mcp|tunnel|runner|github|gh-|monitor|watchdog|operator|health|audit|daemon')]
EXISTING={
'abutron-v9-eight-account-learning-archive-ro':'native_trade_archive.py',
'abutron-v9-all-owner-causal-candidate-trainer':'causal_owner_candidate_trainer.py',
'abutron-v9-four-owner-chronological-holdout-ro':'chronological_owner_holdout.py',
'abutron-v9-forward-frozen-owner-oos-ro':'frozen_entry_trade_oos.py',
'abutron-v9-prospective-broker-m5-shadow-ro':'prospective_m5_shadow.py',
'abutron-v9-shadow-correlation-confidence-ro':'correlation_confidence.py',
'abutron-fp-native-m5-archive-ro':'fp_native_m5_collector.py'}
def run(*a):
 try:return subprocess.run(a,capture_output=True,text=True,timeout=35,check=False).stdout
 except Exception:return ''
def clean(s):
 s=re.sub(r'[a-fA-F0-9]{32}', '[CONNECTION_PROFILE]', str(s));s=LOGIN.sub('[BROKER_LOGIN]',s);s=re.sub(r'\d{5,12}', '[NUMERIC_ID]', s)
 s=re.sub(r'(?<!\d)(?:\d{1,3}\.){3}\d{1,3}(?!\d)','[IP]',s)
 s=re.sub(r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}','[EMAIL]',s)
 return s
def sha(p):
 try:
  f=Path(p)
  if not f.is_file() or f.is_symlink():return None
  return hashlib.sha256(f.read_bytes()).hexdigest()
 except Exception:return None
def parse_unit(p):
 try:txt=Path(p).read_text(errors='replace')
 except Exception:return {}
 out=collections.defaultdict(list)
 for line in txt.splitlines():
  if '=' not in line or line.strip().startswith(('#',';')):continue
  k,v=line.strip().split('=',1)
  if k.isalpha():out[k].append(v)
 return out
def first(obj,key):return (obj.get(key) or [''])[0]
def category(n):
 if re.search(r'client-mt5-[a-f0-9]{32}',n):return 'mt5_runtime'
 return next((k for k,p in CATEGORY if re.search(p,n,re.I)),'other')
units=[]
for line in run('systemctl','list-unit-files','--all','--no-legend','--no-pager').splitlines():
 p=line.split()
 if len(p)<2:continue
 name,state=p[:2]
 if PREFIX.search(name) and name.endswith(('.service','.timer','.socket','.path')):units.append((name,state))
properties=('Id','ActiveState','SubState','Result','FragmentPath','User','NoNewPrivileges','ProtectSystem','PrivateNetwork','ReadWritePaths')
show={}
for i in range(0,len(units),60):
 args=[x for x,y in units[i:i+60]]
 out=run('systemctl','show','--no-pager',*['--property='+x for x in properties],*args)
 for block in out.split('\n\n'):
  row=dict(s.split('=',1) for s in block.splitlines() if '=' in s)
  if row.get('Id'):show[row['Id']]=row
records=[];refs={}
for name,install in sorted(units):
 m=show.get(name,{});frag=m.get('FragmentPath','');config=parse_unit(frag) if frag.startswith('/') else {}
 kind=name.rsplit('.',1)[1];grp=category(name)
 exec_raw=first(config,'ExecStart')
 paths=re.findall(r'/(?:usr|opt|var|home)/[^\s;"\'\\]+',exec_raw)
 candidate=None
 for path in paths:
  path=path.rstrip(');')
  if path.endswith(('.py','.sh','.js','.mjs')) or (path.startswith('/usr/local/sbin/') and Path(path).is_file()):candidate=path
 if not candidate and paths:candidate=paths[0]
 basename=clean(Path(candidate).name) if candidate else None
 sd=sha(candidate) if candidate else None
 if candidate:
  key=(basename,sd)
  if key not in refs:
   refs[key]={'source_basename':basename,'source_sha256':sd,'source_size_bytes':None,'categories':set(),
   'unit_references':0,'publication':'REVIEW_REQUIRED_NOT_EXPORTED'}
   try:refs[key]['source_size_bytes']=Path(candidate).stat().st_size
   except Exception:pass
  refs[key]['unit_references']+=1;refs[key]['categories'].add(grp)
 schedule={k:[clean(v)[:100] for v in config.get(k,[])] for k in
 ('OnCalendar','OnActiveSec','OnBootSec','OnStartupSec','OnUnitActiveSec','OnUnitInactiveSec','AccuracySec','RandomizedDelaySec','Persistent') if config.get(k)}
 pub=EXISTING.get(name.removesuffix('.service')) if kind=='service' else None
 rec={'id':'unit-%04d'%(len(records)+1),'unit_name_sanitized':clean(name),'type':kind,'category':grp,
  'install_state':install,'active_state':m.get('ActiveState','unknown'),
  'sub_state':m.get('SubState','unknown'),'last_result':m.get('Result','unknown'),
  'definition_sha256':sha(frag) if frag else None,
  'source_basename':basename,'source_sha256':sd,
  'run_as':clean(m.get('User') or first(config,'User') or 'system'),
  'no_new_privileges':m.get('NoNewPrivileges','unknown'),
  'protect_system':m.get('ProtectSystem','unknown'),
  'private_network':m.get('PrivateNetwork','unknown'),
  'explicit_write_allowance':bool(m.get('ReadWritePaths') or config.get('ReadWritePaths')),
  'schedule':schedule,'source_public_ref':('ABUTRON-FX-V9/ops/issue25/scripts/'+pub if pub else None),
  'raw_unit_text_exported':False}
 records.append(rec)
for v in refs.values():v['categories']=sorted(v['categories'])
cats=collections.Counter(r['category'] for r in records)
summary={'snapshot_utc':NOW,'total':len(records),
 'unit_types':dict(collections.Counter(r['type'] for r in records)),
 'install_states':dict(collections.Counter(r['install_state'] for r in records)),
 'active_states':dict(collections.Counter(r['active_state'] for r in records)),
 'categories':dict(sorted(cats.items())),'unique_source_files':len(refs),
 'existing_public_v9_script_unit_refs':sum(bool(r['source_public_ref']) for r in records),
 'scope':'ABUTRON, APEX, FP, Deriv, MT5, restic and actions.runner prefixes; other OS services omitted',
 'limitations':['point-in-time','only metadata','no source bytes or full unit texts','no secrets','no customer evidence','no execution certification']}
(O/'summary.public.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
(O/'systemd-units.public.json').write_text(json.dumps({'schema':'abutron.systemd.sanitized.v1','snapshot_utc':NOW,'units':records},indent=2,sort_keys=True)+'\n')
(O/'worker-sources.public.json').write_text(json.dumps({'schema':'abutron.worker.source_index.v1','snapshot_utc':NOW,'sources':sorted(refs.values(),key=lambda x:(x['source_basename'],x['source_sha256'] or ''))},indent=2,sort_keys=True)+'\n')
print(json.dumps(summary,sort_keys=True))
