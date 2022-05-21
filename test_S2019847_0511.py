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

#rep.save(out_file_name+'.png')

# Testing

# Reading the report
rep = xr.open_zarr(report_file_name)

# Write to csv via pandas data frame
rep.to_dataframe().to_csv(report_file_name+'.csv')

# Reading the LSSS report

#LSSS_report_file_name 
#retcode = subprocess.call("/usr/bin/Rscript --vanilla -e 'source(\"/pathto/MyrScript.r\")'", shell=True)

nilz=10*np.log10(rep.isel(category=3).sv)

nilz.T.plot()
plt.show()

plt.savefig(report_file_name+'_sv.png')
plt.close()

t = np.arange(0.0, 2.0, 0.01)
s = 1 + np.sin(2*np.pi*t)
plt.plot(t, s)

plt.title('About as simple as it gets, folks')
plt.show()
