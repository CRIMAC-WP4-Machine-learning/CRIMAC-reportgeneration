
import xarray as xr
from numcodecs import Blosc
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os
from Logger import Logger as Log
from reportgeneration.EKMaskedGridder import EKMaskedGridder


class Reportgenerator:

    def __init__(self,grid_fname=None, pred_fname=None,out_fname=None, freq=38000, threshold=0.5, vtype='range', vstep=50, htype='ping', hstep=50, max_range=500):
        Log().info('####### Reportgenerator ########')
        zarr_grid = xr.open_zarr(grid_fname, chunks={'frequency': 'auto', 'ping_time': 'auto', 'range': -1})
        zarr_pred = xr.open_zarr(pred_fname)
        self.has_out_file = False
        # If there is a output file, start griding after last timestamp in file
        if out_fname is not None and os.path.exists(out_fname):

            self.has_out_file = True
            zarr_out = xr.open_zarr(out_fname)
            start_time = zarr_out['ping_time'].values[-1]
            stop_time = zarr_grid['ping_time'].values[-1]
            zarr_grid = zarr_grid.sel(ping_time=slice(start_time, stop_time))
            zarr_pred = zarr_pred.sel(ping_time=slice(start_time, stop_time))

            Log().info('Existing output file time span: \nt0={}\nt1={}'.format(zarr_out['ping_time'].values[0],start_time))
            Log().info('Got new data spanning:\nt0={}\nt1={}'.format(zarr_grid['ping_time'].values[0],stop_time))

        self.ekmg = EKMaskedGridder(zarr_grid, zarr_pred, freq, threshold, vtype, vstep, htype, hstep, max_range)
        self.ds = None

    def save(self, fname):

        file_path, file_ext = os.path.splitext(fname)
        file_ext = file_ext.lower()

        # Do griding if it has not already been done
        if file_ext in ['.zarr', '.png'] and self.ds is None:
            self.ds = self.ekmg.gridd()

            # Assume first bin in range is nan and last bin in range do not contain data from whole bin
            r0 = self.ds['range'].values[1]
            r1 = self.ds['range'].values[-2]
            self.ds = self.ds.sel(range=slice(r0, r1))

            # Remove first and last bin along ping axis to remove nan and use info on whole bins only
            p0 = self.ds['ping_time'].values[1]
            p1 = self.ds['ping_time'].values[-2]
            self.ds = self.ds.sel(ping_time=slice(p0, p1))

        if file_ext == '.zarr':
            compressor = Blosc(cname='zstd', clevel=3, shuffle=Blosc.BITSHUFFLE)
            encoding = {var: {"compressor": compressor} for var in self.ds.data_vars}
            if self.has_out_file:
                self.ds.to_zarr(fname, mode='a',append_dim='ping_time')
            else:
                self.ds.to_zarr(fname, mode='w', encoding=encoding)

        elif file_ext == '.png':

            vmax = -20
            vmin = -80
            for cat in self.ds['category']:

                data = self.ds.sel(category=cat)

                fig = plt.figure(figsize=(12, 6))
                ax = plt.axes()
                plt.title('{} @ {}'.format(cat.values, data['channel_id'].values))

                # Set axis limits
                x_lims = mdates.date2num(data['ping_time'].values)
                extent = [x_lims[0], x_lims[-1].astype(float), data['range'].values[-1], data['range'].values[0]]

                im = plt.gca().imshow(10 * np.log10(data.transpose()['sv'].values + 10e-20), vmin=vmin,vmax=vmax, extent=extent, origin='upper')

                plt.ylabel('Sv {}(m)'.format(self.ekmg.vtype))

                # Format time axis
                locator = mdates.AutoDateLocator(minticks=3, maxticks=20)
                formatter = mdates.ConciseDateFormatter(locator)
                plt.gca().xaxis.set_major_locator(locator)
                plt.gca().xaxis.set_major_formatter(formatter)

                plt.axis('auto')
                plt.axis('tight')
                plt.subplots_adjust(left=0.043, bottom=0.067, right=0.9, top=0.95)

                # Make colorbar tighter
                cax = fig.add_axes([ax.get_position().x1 + 0.01, ax.get_position().y0, 0.02, ax.get_position().height])
                plt.colorbar(im, cax=cax)

                plt.savefig('{}_{}.png'.format(file_path, cat.values))

        else:
            Log().error('{} format not supported'.format(fname[-4:]))


if __name__ == "__main__":


    baseDir = r'Z:\Dev\Data\CRIMAC\Data\03Subset\03'

    datain = baseDir  # the data directory where the preprocessed data files are located.
    dataout = baseDir+r'\..'  # directory where the reports are written.
    workin = baseDir  # the directory where the zarr prediction masks are located.
    bottomin = baseDir  # the directory where the zarr bottom detection data is located (_optional_).

    MAIN_FREQ = 38000
    MAX_RANGE_SRC = 100
    THRESHOLD = 0.2  # threshold for the classes
    HOR_INTEGRATION_TYPE = 'ping' # 'ping' | 'time' | 'distance'
    HOR_INTEGRATION_STEP = 100  # seconds | pings | meters | nmi

    VERT_INTEGRATION_TYPE = 'range' # 'depth'
    VER_INTEGRATION_STEP = 10  # Always in meters

    OUTPUT_NAME = 'zarr_report.zarr'  # file name output (optional,  default to `out.<zarr/nc>`)
    WRITE_PNG = 'zarr_report.png'  # No file is generated if left out

    grid_file_name = '{}'.format(datain + os.sep + r'zarr_gridd_sub.zarr')
    pred_file_name = '{}'.format(workin + os.sep + r'zarr_pred_sub.zarr')
    out_file_name = '{}'.format(dataout + os.sep + r'zarr_report.zarr')
    Log(loggerFileName=dataout)
    rg = Reportgenerator(
        grid_file_name,
        pred_file_name,
        out_file_name,
        MAIN_FREQ,
        THRESHOLD,
        VERT_INTEGRATION_TYPE,
        VER_INTEGRATION_STEP,
        HOR_INTEGRATION_TYPE,
        HOR_INTEGRATION_STEP,
        MAX_RANGE_SRC
    )

    rg.save(dataout + os.sep + OUTPUT_NAME)
    rg.save(dataout + os.sep + WRITE_PNG)
