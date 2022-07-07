import os
#os.chdir('/home/nilsolav/repos/CRIMAC-reportgeneration')
#os.chdir('/home/nilsolav/repos/CRIMAC-reportgeneration/reportgeneration')
#print(os.getcwd())

import reportgeneration.Reportgenerator as rg
import xarray as xr
from Logger import Logger as Log

Log().info('####### Setting up #######')

# Set and check file directories
dirs = ['/datain/', '/predin/', '/dataout/']
datain, predin, dataout = dirs
for d in dirs:
    _dir = os.path.expanduser(d)
    if not os.path.exists(_dir):
        Log().error('####### {} could not be found #######'.format(_dir))

# Generate the file references
grid_file_name = datain+os.getenv('SURVEY'+'_sv.zarr', 'S2019847_0511_sv.zarr')
pred_file_name = predin+os.getenv('PREDICTIONFILE',
                                  'S2019847_0511_labels.zarr')
bot_file_name = datain+os.getenv('SURVEY'+'_bottom.zarr', 'S2019847_0511_bottom.zarr')
report_file_name = dataout+os.getenv('REPORTFILE',
                                     'S2019847_0511_predictions_1_report.zarr')

# Check if input files exist
files = [grid_file_name, pred_file_name, bot_file_name]
for d in files:
    _dir = os.path.expanduser(d)
    if not os.path.exists(_dir):
        print('{} could not be found.'.format(_dir))
    else:
        print('{} is available.'.format(_dir))        
print('{} is set as report file name.'.format(report_file_name))

print(' ')
Log().info('####### Setting up env variables #######')

# Env vars
PingAxisIntervalType = os.getenv('PING_AXIS_INTERVAL_TYPE', 'distance')
PingAxisIntervalOrigin = os.getenv('PING_AXIS_INTERVAL_ORIGIN', 'start')
PingAxisIntervalUnit = os.getenv('PING_AXIS_INTERVAL_UNIT', 'nmi')
PingAxisInterval = float(os.getenv('PING_AXIS_INTERVAL', 0.1))

# Channel
ChannelDepthStart = float(os.getenv('CHANNEL_DEPTH_START', 0))
ChannelDepthEnd = float(os.getenv('CHANNEL_DEPTH_END', 500))
ChannelThickness = float(os.getenv('CHANNEL_THICKNESS', 5))
ChannelType = os.getenv('CHANNEL_TYPE', 'depth')

# Values
SvThreshold = float(os.getenv('SV_THRESHOLD', -100))
Type = os.getenv('TYPE', 'C')
Unit = os.getenv('UNIT', 'm2nmi-2')
main_freq = int(os.getenv('MAIN_FREQ', 38000))
output_type = os.getenv('OUTPUT_TYPE', 'zarr')
classthreshold = float(os.getenv('CLASSTRHRESHOLD', 0.8))

# Print env vars
v = [PingAxisIntervalType, PingAxisIntervalOrigin, PingAxisIntervalUnit,
     PingAxisInterval, ChannelDepthStart, ChannelDepthEnd, ChannelThickness,
     ChannelType, SvThreshold, Type, Unit, main_freq, output_type, classthreshold]
vt = ['PingAxisIntervalType', 'PingAxisIntervalOrigin', 'PingAxisIntervalUnit',
      'PingAxisInterval', 'ChannelDepthStart', 'ChannelDepthEnd', 'ChannelThickness',
      'ChannelType', 'SvThreshold', 'Type', 'Unit', 'main_freq', 'output_type', 'classthreshold']
for i, _v in enumerate(v):
    print(vt[i]+': '+str(v[i])+' '+str(type(_v)))
print(' ')

#
# Do the regridding
#
with rg.Reportgenerator(grid_file_name,
                        pred_file_name,
                        bot_file_name,
                        report_file_name,
                        main_freq,
                        SvThreshold,
                        ChannelType,
                        ChannelThickness,
                        PingAxisIntervalUnit,
                        PingAxisInterval,
                        ChannelDepthStart,
                        ChannelDepthEnd) as rep:
    
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
for item in list(report.attrs.items()):
    df[item[0]] = item[1]
# Save report to pandas tidy file
df.to_csv(report_file_name+'.csv', index=True)

# That's it
