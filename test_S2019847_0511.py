data_dir = '/mnt/d/DATAscratch/crimac-scratch/'
sys.path.append('/home/nilsolav/repos/GitHub/CRIMAC-reportgeneration/reportgeneration/')
sys.path.append('/home/nilsolav/repos/GitHub/CRIMAC-reportgeneration/')

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

# These are the parameters in the acoustic format
PingAxisIntervalType = "distance"  # see http://vocab.ices.dk/?ref=1455
PingAxisIntervalOrigin = "start"  # see http://vocab.ices.dk/?ref=1457
PingAxisIntervalUnit = "nmi"  # see http://vocab.ices.dk/?ref=1456
PingAxisInterval = 0.1
SvThreshold = 0  # db eller lineære verdiar?
Type = "C"  # C = sA, Nautical area scattering coefficient
Unit = "m2nmi-2"  # see http://vocab.ices.dk/?ref=1460 |

# CRIMAC regridder parameters
main_freq = 38000
threshold = 0.8
vitype = 'range'#'depth'
vistep = 10
hitype = PingAxisIntervalUnit
histep = PingAxisInterval
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
rep.save(report_file_name+'.png')

#
# Testing
#

# Reading the report & original data
grid = xr.open_zarr(grid_file_name)
pred = xr.open_zarr(pred_file_name)
rep = xr.open_zarr(report_file_name)

# Comparing the integrator with xarray averaging

# "Integrator" based on xarray mean functions multiplied with maxrange,
# should be similar to Sa
hres = (grid.sv.sel(frequency=38000) *
        pred.annotation.sel(category=27)).mean(dim='range').resample(
            ping_time='H').mean() * max_range
Sa_raw = 10*np.log10(hres+0.00000001)

# Do the same for the output from the integrator. Should be similar'sih
# as the plot from the original data
lres = rep.sv.sel(category=27).mean(dim='range').resample(
            ping_time='H').mean() * max_range
Sa_int = 10*np.log10(lres+0.00000001)

fig, axes = plt.subplots(nrows=2)
Sa_int.plot(ax=axes[0])
Sa_raw.plot(ax=axes[1])
plt.savefig(report_file_name+'_sv.png')

#
# Saving to ICESAcoustic format
#

# Rename coordinates and variables
rep = rep.rename({'latitude': 'Latitude',
                  'longitude': 'Longitude',
                  'ping_time': 'Time',
                  'sv': 'value',
                  'category': 'SaCategory'})

# Add new coordinates
N = len(rep.Time)
Latitude2 = np.append(rep.LogLatitude[1:].values, np.NaN)
Longitude2 = np.append(rep.LogLongitude[1:].values, np.NaN)
Origin = np.repeat("start", N)
Origin2 = np.repeat("end", N)
BottomDepth = np.repeat(np.nan, N)  # Needs to be added from input data
Validity = np.repeat("V", N)

rep.assign_coords(Latitude2=("Time", Latitude2))
rep.assign_coords(Longitude2=("Time", Longitude2))
rep.assign_coords(Origin=("Time", Origin))
rep.assign_coords(Origin2=("Time", Origin2))
rep.assign_coords(BottomDepth=("Time", BottomDepth))
rep.assign_coords(Validity=("Time", Validity))
rep.assign_coords(Distance=("Time", rep.distance.data))

rep.assign_attrs({"PingAxisIntervalType": PingAxisIntervalType,
                  "PingAxisIntervalOrigin": PingAxisIntervalOrigin,
                  "PingAxisIntervalUnit": PingAxisIntervalUnit,
                  "PingAxisInterval": PingAxisInterval,
                  "Platform": "NaN",
                  "LocalID": "NaN"})
rep.value.assign_attrs({"Type": Type,
                        "Unit": Unit})

# Flatten the data to a dataframe
df = rep.to_dataframe()
"""
  | Sample | ChannelDepthUpper |  | Upper depth of the integrator cell in meters relative surface |
  | Sample | ChannelDepthLower |  | Lower depth of the integrator cell in meters relative surface |
"""


# Save report to pandas tidy file
rep.to_dataframe().to_csv(report_file_name+'.csv')
