import pathlib,json,datetime,time,threading,requests,xarray as xr
ROOT=pathlib.Path(__file__).resolve().parent
LOCK=threading.Lock()
def fetch(task,headers):
 product,var,g=task;folder=ROOT/'measurements'/product;folder.mkdir(parents=True,exist_ok=True);out=folder/(g['time_start'][:7]+'.nc')
 if out.exists():return str(out)
 session=requests.Session();session.headers.update(headers)
 urls=[x['href'] for x in g['links'] if not x.get('inherited') and 'opendap' in x.get('href','').lower()]
 url=urls[0]
 # Request only the analysis variable and coordinates, avoiding malformed ancillary time bounds.
 if product=='GLDAS_NOAH025_M':url+='?'+var+',time,lat,lon'
 def extract(ds):
  da=ds[var];la=da['lat'];lo=da['lon'];da=da.sel(lat=la[(la>=22)&(la<=32)],lon=lo[(lo>=24)&(lo<=36)]).load()
  if not da.size or not bool(da.notnull().any()):raise RuntimeError('No finite data')
  result=da.to_dataset();result.attrs.update({'source_granule_id':g['id'],'source_url':url,'requested_bbox':'24,22,36,32','retrieved_at':datetime.datetime.now(datetime.timezone.utc).isoformat()})
  with LOCK:
   temp=out.with_suffix('.live.partial.nc');result.to_netcdf(temp);temp.replace(out)
 try:
  with xr.open_dataset(url,engine='pydap',backend_kwargs={'session':session,'timeout':60}) as ds:extract(ds)
 except Exception as first:
  if product!='GLDAS_NOAH025_M':raise
  # Range-based HTTPS access to the actual HDF5 file, avoiding OPeNDAP conversion.
  import fsspec
  dataurl=next(x['href'] for x in g['links'] if not x.get('inherited') and x.get('rel','').endswith('/data#') and x['href'].startswith('https:'))
  url=dataurl
  with fsspec.open(dataurl,'rb',headers=headers,block_size=262144) as file:
   with xr.open_dataset(file,engine='h5netcdf') as ds:extract(ds)
 return str(out)
