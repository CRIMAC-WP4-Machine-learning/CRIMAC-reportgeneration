repo_dir ='/mnt/d/repos/Github/'
data_dir = '/mnt/d/DATAscratch/crimac-scratch/'
sys.path.append(repo_dir+'CRIMAC-reportgeneration/reportgeneration/')

import reportgeneration.Reportgenerator as rg
import xarray as xr
import dask
import matplotlib.pyplot as plt

grid_file_name = data_dir+'2019/S2019847_0511/ACOUSTIC/GRIDDED/S2019847_0511_sv.zarr'
pred_file_name = data_dir+'2019/S2019847_0511/ACOUSTIC/GRIDDED/S2019847_0511_labels.zarr'
bot_file_name = data_dir+'2019/S2019847_0511/ACOUSTIC/GRIDDED/S2019847_0511_bottom.zarr'
out_file_name = data_dir+'2019/S2019847_0511/ACOUSTIC/REPORTS/S2019847_0511_report_0.zarr'

# Test on depth vs ping
main_freq = 38000
threshold = 0.8
vitype = 'depth'
vistep = 10
hitype = 'nmi'
histep = 0.1
#hitype = 'ping'
#histep = 1000
max_range = 500

rep = rg.Reportgenerator(grid_file_name,
                         pred_file_name,
                         bot_file_name,
                         out_file_name,
                         main_freq,
                         threshold,
                         vitype,
                         vistep,
                         hitype,
                         histep,
                         max_range)

rep.save(out_file_name)

rep.save(out_file_name+'.png')

rep = xr.open_zarr(out_file_name)

rep.isel(category=3).plot

plt.show()
plt.savefig(out_file_name+'_sv.png')
plt.close()
