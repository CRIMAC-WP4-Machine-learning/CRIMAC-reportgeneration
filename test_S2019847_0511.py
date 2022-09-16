import sys
data_dir = '/mnt/c/DATAscratch/crimac-scratch/'
sys.path.append('/home/nilsolav/repos/CRIMAC-reportgeneration/reportgeneration/')
sys.path.append('/home/nilsolav/repos/CRIMAC-reportgeneration/')

import shutil
import xarray as xr
import dask
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import Reportgenerator as rg

grid_file_name = data_dir + \
                 '2019/S2019847_0511/ACOUSTIC/GRIDDED/S2019847_0511_sv.zarr'
pred_file_name = data_dir + \
                 '2019/S2019847_0511/ACOUSTIC/GRIDDED/S2019847_0511_labels.zarr'
bot_file_name = data_dir + \
                '2019/S2019847_0511/ACOUSTIC/GRIDDED/S2019847_0511_bottom.zarr'
report_file_name = data_dir + \
                   '2019/S2019847_0511/ACOUSTIC/REPORTS/S2019847_0511_report_1.zarr'
LSSS_report_file_name = data_dir + \
                        '2019/S2019847_0511/ACOUSTIC/LSSS/Reports/ListUserFile20__L2887.0-3069.3.xml'

# Delete old report
if os.path.exists(report_file_name):
    print('####### Old report exist: deleting #######')
    shutil.rmtree(report_file_name)

#
# Parameters
#
CLASSTRHRESHOLD = 0.8
SV_THRESHOLD = -100
OUTPUT_TYPE = 'zarr'

# Ping axis
# This one is not used by the regridder but used in the metadata
PingAxisIntervalType = "distance"  # see http://vocab.ices.dk/?ref=1455
PingAxisIntervalOrigin = "start"  # see http://vocab.ices.dk/?ref=1457
PingAxisIntervalUnit = "nmi"  # see http://vocab.ices.dk/?ref=1456
PingAxisInterval = 0.1

# Channel
ChannelDepthStart = 0  # Integration start depth (not implemented)
ChannelDepthEnd = 500
ChannelThickness = 5
ChannelType = 'depth'  # 'range'  # 'depth'

# Values
SvThreshold = 0  # db eller lineære verdiar? Not implemented.
Type = "C"  # C = sA, Nautical area scattering coefficient
Unit = "m2nmi-2"  # see http://vocab.ices.dk/?ref=1460 |
main_freq = 38000  # The frequency to integrate (could be a list in the future)


#
# Do the regridding
#

commit_sha = 'test script'
with rg.Reportgenerator(grid_file_name,
                        pred_file_name,
                        bot_file_name,
                        report_file_name,
                        main_freq,
                        SvThreshold,
                        ChannelType,
                        ChannelThickness,
                        PingAxisIntervalOrigin,
                        PingAxisIntervalUnit,
                        PingAxisInterval,
                        ChannelDepthStart,
                        ChannelDepthEnd,
                        commit_sha) as rep:
    
    rep.saveGridd(report_file_name)
    rep.saveImages(report_file_name+'.png')
    rep.saveReport(report_file_name+'.csv')

#
# Saving to ICESAcoustic format
#

# Reading the report & original data
grid = xr.open_zarr(grid_file_name)
pred = xr.open_zarr(pred_file_name)
report = xr.open_zarr(report_file_name)

#
# Flatten the data to a dataframe and write to file
#

df = report.to_dataframe()
# Add the attributes to the df
#for item in list(report.attrs.items()):
#    df[item[0]] = item[1]
# Save report to pandas tidy file
df.to_csv(report_file_name+'.csv', index=True)

#
# Testing
#

# Comparing the integrator with xarray averaging

# "Integrator" based on xarray mean functions multiplied with maxrange,
# should be similar to Sa
hres = (grid.sv.sel(frequency=38000) *
        pred.annotation.sel(category=27)).mean(dim='range').resample(
            ping_time='H').mean() * ChannelDepthEnd
Sa_raw = 10*np.log10(hres+0.00000001)

# Do the same for the output from the integrator. Should be similar'ish
# as the plot from the original data
lres = report.value.sel(SaCategory=27).mean(dim='ChannelDepthUpper').resample(
            Time='H').mean() * ChannelDepthEnd
Sa_int = 10*np.log10(lres+0.00000001)

fig, axes = plt.subplots(nrows=2)
Sa_int.plot(ax=axes[0])
Sa_raw.plot(ax=axes[1])
plt.savefig(report_file_name+'_sv.png')
