import pathlib,sys,json,time,importlib,concurrent.futures,traceback
ROOT=pathlib.Path(__file__).resolve().parent
if len(sys.argv)>1:sys.path.insert(0,sys.argv[1])
import earthaccess,xarray as xr
print('NASA download recovery. Credentials stay in memory. This session supports fixes without another login.',flush=True)
auth=earthaccess.login(strategy='interactive',persist=False)
if not auth.authenticated:raise RuntimeError('Login failed')
headers=dict(earthaccess.get_requests_https_session().headers)
import regional_worker
status={'complete':False,'state':'running','products':{},'errors':[]}
def save():
 temp=ROOT/'live_status.tmp';temp.write_text(json.dumps(status,indent=2));temp.replace(ROOT/'live_status.json')
tasks=[]
for product,var in [('M2TMNXSLV','T2M'),('GLDAS_NOAH025_M','SoilMoi0_10cm_inst')]:
 g=json.loads((ROOT/'manifests'/f'{product}.json').read_text())['granules'];tasks.extend((product,var,x) for x in g)
tasks=[x for pair in zip(tasks[:288],tasks[288:]) for x in pair]
while True:
 missing=[t for t in tasks if not (ROOT/'measurements'/t[0]/(t[2]['time_start'][:7]+'.nc')).exists()]
 for p in ['M2TMNXSLV','GLDAS_NOAH025_M']:status['products'][p]={'completed':288-sum(t[0]==p for t in missing),'expected':288}
 save()
 if not missing:break
 importlib.reload(regional_worker)
 # Reload between bounded batches so endpoint repairs retain this authenticated session.
 batch=missing[:24];errors=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
  futures={pool.submit(regional_worker.fetch,t,headers):t for t in batch}
  for f in concurrent.futures.as_completed(futures):
   t=futures[f]
   try:
    f.result();status['products'][t[0]]['completed']+=1;print(t[0],t[2]['time_start'][:7],'OK',flush=True)
   except Exception as e:
    errors.append({'product':t[0],'month':t[2]['time_start'][:7],'error':str(e)[:800],'trace':traceback.format_exc()[-3000:]});print(t[0],type(e).__name__,flush=True)
   status['errors']=errors;save()
 if errors:
  status['state']='retrying_failed_batch';save();time.sleep(15)
 else:status['state']='running'
import runpy
runpy.run_path(str(ROOT/'assemble_cubes.py'),run_name='__main__')
print('COMPLETE',flush=True)
input('Press Enter to close...')
