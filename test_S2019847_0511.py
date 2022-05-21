repo_dir ='/mnt/d/repos/Github/'
data_dir = '/mnt/d/DATAscratch/crimac-scratch/'
sys.path.append(repo_dir+'CRIMAC-reportgeneration/reportgeneration/')

import reportgeneration.Reportgenerator as rg
import xarray as xr
import dask
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

grid_file_name = data_dir + \
                 '2019/S2019847_0511/ACOUSTIC/GRIDDED/S2019847_0511_sv.zarr'
pred_file_name = data_dir + \
                 '2019/S2019847_0511/ACOUSTIC/GRIDDED/S2019847_0511_labels.zarr'
bot_file_name = data_dir + \
                '2019/S2019847_0511/ACOUSTIC/GRIDDED/S2019847_0511_bottom.zarr'
report_file_name = data_dir + \
                   '2019/S2019847_0511/ACOUSTIC/REPORTS/S2019847_0511_report_0.zarr'
LSSS_report_file_name = data_dir + \
                        '2019/S2019847_0511/ACOUSTIC/LSSS/Reports/ListUserFile20__L2887.0-3069.3.xml'

# Test on depth vs ping
main_freq = 38000
threshold = 0.8
# vitype = 'depth'
vitype = 'range'
vistep = 10
# hitype = 'nmi'
# histep = 0.1
hitype = 'ping'
histep = 1000
max_range = 500

rep = rg.Reportgenerator(grid_file_name,
                         pred_file_name,
                         bot_file_name,
                         report_file_name,
                         main_freq,
                         threshold,
                         vitype,
                         vistep,
                         hitype,
                         histep,
                         max_range)

rep.save(report_file_name)
rep.save(out_file_name+'.png')

# Testing

# Reading the report & original data
grid = xr.open_zarr(grid_file_name)
pred = xr.open_zarr(pred_file_name)
rep = xr.open_zarr(report_file_name)

# Plotting

# "Integrator" based on xarray mean functions multiplied with 500 m,
# should be similar to Sa
hres = (grid.sv.sel(frequency=38000) *
        pred.annotation.sel(category=27)).mean(dim='range').resample(
            ping_time='H').mean() * 500
Sa_raw = 10*np.log10(hres+0.00000001)

# Do the same for the output from the integrator. Should be similar'sih
# as the plot from the original data
lres = rep.sv.sel(category=27).mean(dim='range').resample(
            ping_time='H').mean() * 500
Sa_int = 10*np.log10(lres+0.00000001)

fig, axes = plt.subplots(nrows=2)
Sa_int.plot(ax=axes[0])
Sa_raw.plot(ax=axes[1])
plt.savefig(report_file_name+'_sv.png')

