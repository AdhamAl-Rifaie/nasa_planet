import sys,pathlib,json,numpy as np
from netCDF4 import Dataset,num2date,date2num
import xarray as xr
root=pathlib.Path(__file__).resolve().parent;s=json.loads((root/'live_status.json').read_text())
for product,var in [('M2TMNXSLV','T2M'),('GLDAS_NOAH025_M','SoilMoi0_10cm_inst')]:
 values=[];dates=[]
 for p in sorted((root/'measurements'/product).glob('????-??.nc')):
  with Dataset(p) as d:
   v=d[var];v.set_auto_maskandscale(False);a=np.array(v[:]);fill=getattr(v,'_FillValue',np.nan);a=np.where(a==fill,np.nan,a);values.append(a)
   dates.extend(num2date(d['time'][:],d['time'].units,only_use_cftime_datetimes=False))
   lat=d['lat'][:];lon=d['lon'][:];units=v.units
 times=np.array([np.datetime64(str(t)) for t in dates])
 cube=xr.Dataset({var:(('time','lat','lon'),np.concatenate(values,axis=0),{'units':units})},coords={'time':times,'lat':lat,'lon':lon})
 cube.to_netcdf(root/'measurements'/f'{product}_Egypt_2001_2024.nc')
 s['products'][product].update({'validated':True,'variable':var,'units':units,'shape':dict(cube[var].sizes),'missing_fraction':float(cube[var].isnull().mean())});print(product,'assembled',flush=True)
s.update({'complete':True,'state':'measurement_download_complete'});(root/'live_status.json').write_text(json.dumps(s,indent=2));(root/'download_status.json').write_text(json.dumps(s,indent=2))
