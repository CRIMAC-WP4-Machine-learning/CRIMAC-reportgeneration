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
# Ruben: refactor these to ICESAcoustic variable names:
hitype = PingAxisIntervalUnit
histep = PingAxisInterval

ChannelDepthIntervalStart = 0  # Integration start depth (not implemented)
vistep = 10
max_range = 500

# CRIMAC regridder parameters
SvThreshold = 0  # db eller lineære verdiar?
Type = "C"  # C = sA, Nautical area scattering coefficient
Unit = "m2nmi-2"  # see http://vocab.ices.dk/?ref=1460 |
main_freq = 38000
threshold = 0.8  # dont think this is needed. The allocation is not binary.

vitype = 'range'  # 'depth'

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
# Saving to ICESAcoustic format
#

# (Ruben: This part needs to be added to the main classes)

# Reading the report & original data
grid = xr.open_zarr(grid_file_name)
pred = xr.open_zarr(pred_file_name)
report = xr.open_zarr(report_file_name)

# Rename coordinates and variables
report = report.rename({'latitude': 'Latitude',
                        'longitude': 'Longitude',
                        'ping_time': 'Time',
                        'sv': 'value',
                        'range': 'ChannelDepthUpper',
                        'category': 'SaCategory'})

# Add new coordinates
N = len(report.Time)
Latitude2 = np.append(report.Latitude[1:].values, np.NaN)  # Adress end point
Longitude2 = np.append(report.Longitude[1:].values, np.NaN)  # Address last
Origin = np.repeat("start", N)
Origin2 = np.repeat("end", N)
BottomDepth = np.repeat(np.nan, N)  # Needs to be added from input data
Validity = np.repeat("V", N)
# Upper depth of the integrator cell in meters relative surface
ChannelDepthLower = np.append(
    report.ChannelDepthUpper[1:].values, np.NaN)  # Adress end point

report = report.assign_coords(Latitude2=("Time", Latitude2))
report = report.assign_coords(Longitude2=("Time", Longitude2))
report = report.assign_coords(Origin=("Time", Origin))
report = report.assign_coords(Origin2=("Time", Origin2))
report = report.assign_coords(BottomDepth=("Time", BottomDepth))
report = report.assign_coords(Validity=("Time", Validity))
report = report.assign_coords(ChannelDepthLower=("ChannelDepthUpper",
                                                 ChannelDepthLower))

# Ruben: Is this log distance?:
report = report.assign_coords(Distance=("Time", report.distance[1, :].values))

# Add attributes
report = report.assign_attrs({"PingAxisIntervalType": PingAxisIntervalType,
                              "PingAxisIntervalOrigin": PingAxisIntervalOrigin,
                              "PingAxisIntervalUnit": PingAxisIntervalUnit,
                              "PingAxisInterval": PingAxisInterval,
                              "Platform": "NaN",
                              "LocalID": "NaN",
                              "Type": Type,
                              "Unit": Unit})

# (Ruben: end refactoring)

#
# Flatten the data to a dataframe
#

df = report.to_dataframe()
# Add the attributes to the df
for item in list(report.attrs.items()):
    df[item[0]] = item[1]
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
            ping_time='H').mean() * max_range
Sa_raw = 10*np.log10(hres+0.00000001)

# Do the same for the output from the integrator. Should be similar'sih
# as the plot from the original data
lres = report.value.sel(SaCategory=27).mean(dim='ChannelDepthUpper').resample(
            Time='H').mean() * max_range
Sa_int = 10*np.log10(lres+0.00000001)

fig, axes = plt.subplots(nrows=2)
Sa_int.plot(ax=axes[0])
Sa_raw.plot(ax=axes[1])
plt.savefig(report_file_name+'_sv.png')
