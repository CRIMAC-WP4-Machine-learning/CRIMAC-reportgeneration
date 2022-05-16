
import xarray as xr
from numcodecs import Blosc
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os
from Logger import Logger as Log
from reportgeneration.EKMaskedGridder import EKMaskedGridder


class Reportgenerator:

    def __init__(self,grid_fname=None, pred_fname=None,bot_fname=None,out_fname=None, freq=38000, threshold=0.5, vtype='range', vstep=50, htype='ping', hstep=50, max_range=500):
        Log().info('####### Reportgenerator ########')
        zarr_grid = xr.open_zarr(grid_fname, chunks={'frequency': 'auto', 'ping_time': 'auto', 'range': -1})
        zarr_pred = xr.open_zarr(pred_fname)
        if bot_fname is None:
            zarr_bot = None
        else:
            zarr_bot = xr.open_zarr(bot_fname)
        self.has_out_file = False
        # If there is a output file, start griding after last timestamp in file
        if out_fname is not None and os.path.exists(out_fname):
            self.has_out_file = True
            zarr_out = xr.open_zarr(out_fname)
            start_time = zarr_out['ping_time'].values[-1]
            stop_time = zarr_grid['ping_time'].values[-1]
            zarr_grid = zarr_grid.sel(ping_time=slice(start_time, stop_time))
            zarr_pred = zarr_pred.sel(ping_time=slice(start_time, stop_time))
            zarr_bot = zarr_bot.sel(ping_time=slice(start_time, stop_time))

            Log().info('Existing output file time span: \nt0={}\nt1={}'.format(zarr_out['ping_time'].values[0],start_time))
            Log().info('Got new data spanning:\nt0={}\nt1={}'.format(zarr_grid['ping_time'].values[0],stop_time))
        else:
            Log().info('Starting new outputfile')

        self.ekmg = EKMaskedGridder(zarr_grid, zarr_pred, zarr_bot, freq, threshold, vtype, vstep, htype, hstep, max_range)

        self.ds = None

    def save(self, fname):

        file_path, file_ext = os.path.splitext(fname)
        file_ext = file_ext.lower()

        # Do griding if it has not already been done
        if file_ext in ['.zarr', '.png'] and self.ds is None:

            self.ds = xr.concat(self.ekmg.worker_data, dim='category')

            # Assume first bin in range is nan and last bin in range do not contain data from whole bin
            r0 = self.ds['range'].values[1]
            r1 = self.ds['range'].values[-2]
            self.ds = self.ds.sel(range=slice(r0, r1))

            self.ds = self.ds.isel(ping_time=slice(1, len(self.ds['ping_time'])-1))

        if file_ext == '.zarr':

            if self.has_out_file:
                self.ds.to_zarr(fname, mode='a',append_dim='ping_time')
            else:

                compressor = Blosc(cname='zstd', clevel=3, shuffle=Blosc.BITSHUFFLE)

                encoding = {var: {"compressor": compressor} for var in self.ds.data_vars}


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
                im = plt.gca().imshow(10 * np.log10(data['sv'].transpose().values + 10e-20), vmin=vmin,vmax=vmax, extent=extent, origin='upper')
                #im = plt.gca().imshow(10 * np.log10(data['sv'].transpose() + 10e-20), origin='upper')
                #a=10 * np.log10(data['sv'].transpose() + 10e-20)
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
"""
python Reportgenerator.py \
    --data S2019847_0511_sv.zarr
    --pred S2019847_0511_labels.zarr
    --bot S2019847_0511_bottom.zarr
    --out S2019847_0511_report.zarr
    --img S2019847_0511_report.png
    --thr 0.8
    --freq 38000
    --range 500
    --htype ping
    --hstep 100
    --vtype range
    --vstep 10
"""

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=str, help="Acoustic Sv data")
    parser.add_argument("--pred", type=str, help="Predictions")
    parser.add_argument("--bot", type=str, help="Bottom data")
    parser.add_argument("--out", type=str, help="Out data file")
    parser.add_argument("--img", type=str, help="Save image file")
    parser.add_argument("--thr", type=float, help="Threshold for predictions")
    parser.add_argument("--freq", type=float, help="Frequency to gridd")
    parser.add_argument("--range", type=float, help="Range to integrate over (m)")
    parser.add_argument("--htype", type=str,choices=['ping', 'time' , 'nmi'], help="Type of horizontal integration")
    parser.add_argument("--hstep", type=float, help="Step unit for horizontal integration : #pings | seconds | nautical miles)")
    parser.add_argument("--vtype", type=str, choices=['range', 'depth'], help="Type of vertical integration")
    parser.add_argument("--vstep", type=float,help="Step unit for horizontal integration : meters")

    args = parser.parse_args()

    rg = Reportgenerator(
        args.data,
        args.pred,
        args.bot,
        args.out,
        args.freq,
        args.thr,
        args.vtype,
        args.vstep,
        args.htype,
        args.hstep,
        args.range
    )

    rg.save(args.out)

    rg.save(args.img)

