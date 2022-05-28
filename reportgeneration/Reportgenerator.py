import xarray as xr
import shutil
from numcodecs import Blosc
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os
import dask
from Logger import Logger as Log
from reportgeneration.EKGridder import EKGridder
from pathlib import Path


class Reportgenerator:

    def __init__(self,grid_fname=None, pred_fname=None,bot_fname=None,out_fname=None, freq=38000, threshold=0.5, vtype='range', vstep=50, htype='ping', hstep=50, max_range=500):
        Log().info('####### Reportgenerator ########')
        self.vtype = vtype
        self.out_fname = out_fname
        self.tmp_path_name = None
        zarr_grid = xr.open_zarr(grid_fname, chunks={'frequency': 'auto', 'ping_time': 'auto', 'range': -1})
        zarr_grid = zarr_grid.drop_vars(['angle_alongship', 'angle_athwartship'])
        zarr_pred = xr.open_zarr(pred_fname)
        if bot_fname is None:
            zarr_bot = None
        else:
            zarr_bot = xr.open_zarr(bot_fname)

        self.has_out_file = False
        # If there is a output file, start griding after last timestamp in file
        if out_fname is not None and os.path.exists(out_fname):
            Log().info('Existing file found, trying to append')
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


        self.worker_data = []

        for cat in zarr_pred["annotation"]["category"]:
            masked_sv = self.applyMask_(zarr_grid, zarr_pred, zarr_bot, cat=cat, freq=38000)

            if vtype == 'depth':
                self.rangeToDepthCorrection(masked_sv)

            ekgridder = EKGridder(masked_sv, vtype, vstep, htype, hstep, max_range)
            if ekgridder.target_h_bins.shape[0] <= 2:
                self.worker_data = None
                Log().info('Not enough data to make a grid.')
                break

            Log().info(f'Gridding category: {cat.values.flatten()[0]}')
            rg = ekgridder.regrid()

            rg = rg.assign_coords(category=[cat])

            self.worker_data.append(rg)

        """
        for cat, masked_sv in masked:

            if vtype == 'depth':
                self.rangeToDepthCorrection(masked_sv)

            ekgridder = EKGridder(masked_sv, vtype, vstep, htype, hstep, max_range)
            if ekgridder.target_h_bins.shape[0] <= 2:
                self.worker_data = None
                Log().info('Not enough data to make a grid.')
                break

            rg = ekgridder.regrid()


            rg = rg.assign_coords(category=[cat])

            self.worker_data.append(rg)
        """
        self.ds = None

    def rangeToDepthCorrection(self, masked_sv):
        print()
        # masked_sv.heave[0,0:1000].values+masked_sv.transducer_draft[0,0:1000].values
        pass

    def applyMask_(self, data=None, pred=None, bot=None,cat=None, freq=38000):

        fdata = data.sel(frequency=freq)

        mask = pred["annotation"].sel(category=cat.values)
        if cat.values.flatten()[0] < 0:
            mask = xr.where(mask < 0, 1, mask)

        mask = mask.transpose('ping_time', 'range')
        """
        import matplotlib.pylab as plt
        plt.imshow(mask[::200, :].values.astype(float))
        plt.axis('auto')
        plt.show()
        """
        with dask.config.set(**{'array.slicing.split_large_chunks': True}):
            masked_sv = fdata['sv'].data * mask.data#fdata['sv'] * mask

        #masked_sv = masked_sv.assign_coords(distance=fdata.distance)
        fdata['sv'].data = masked_sv
        return fdata


    def applyMask(self, data=None, pred=None,bot=None,freq=38000):

        self.masked = []
        for cat in pred["annotation"]["category"]:
            Log().info(f'Gridding category: {cat.values.flatten()[0]}')

            fdata = data.sel(frequency=freq)

            mask = pred["annotation"].sel(category=cat.values)
            if cat.values.flatten()[0] < 0:
                mask = xr.where(mask < 0, 1,mask)

            mask = mask.transpose('ping_time', 'range')
            """
            import matplotlib.pylab as plt
            plt.imshow(mask[::200, :].values.astype(float))
            plt.axis('auto')
            plt.show()
            """
            with dask.config.set(**{'array.slicing.split_large_chunks': True}):
                masked_sv = fdata['sv'] * mask

            masked_sv = masked_sv.assign_coords(distance=fdata.distance)

            self.masked.append((cat, masked_sv))

        return self.masked


    def getGridd(self):

        if self.ds is None and self.worker_data is not None:

            # Hack to avoid crash when we save final grid
            # Store grid for each category
            # Then reload and concatenate

            # Enshure tmp directory exists
            self.tmp_path_name = str(Path(self.out_fname).parent) + os.sep + '__tmp_main_out'
            if not os.path.exists(self.tmp_path_name):
                os.makedirs(self.tmp_path_name)

            # Store each category
            fnames = []
            for d in self.worker_data:
                fname = self.tmp_path_name+os.sep+f'gridd_{d["category"].values[0]}.zarr'
                fnames.append(fname)
                d.to_zarr(fnames[-1], mode='w')

            # Reload and concatinate
            self.worker_data = []
            for fname in fnames:
                d = xr.open_zarr(fname)
                self.worker_data.append(d)
            #### End hack

            self.ds = xr.concat(self.worker_data, dim='category')

            # Assume first bin in range is nan and last bin in range do not contain data from whole bin
            r0 = self.ds['range'].values[1]
            r1 = self.ds['range'].values[-2]
            self.ds = self.ds.sel(range=slice(r0, r1))

            self.ds = self.ds.isel(ping_time=slice(1, len(self.ds['ping_time']) - 1))

        return self.ds

    def save(self, fname):

        file_path, file_ext = os.path.splitext(fname)
        file_ext = file_ext.lower()

        if self.getGridd() is None:
            return

        if file_ext == '.zarr':
            if self.has_out_file:
                self.ds.to_zarr(fname, mode='a',append_dim='ping_time')
            else:

                compressor = Blosc(cname='zstd', clevel=3, shuffle=Blosc.BITSHUFFLE)

                encoding = {var: {"compressor": compressor} for var in self.ds.data_vars}

                Log().info(f'Writing gridded data to : {fname}')
                #self.ds.compute()                                   # Crash for large dataset 150GB
                self.ds.to_zarr(fname, mode='w', encoding=encoding) # Crash for large dataset 150GB
                #self.ds.to_dataframe().netcdf(fname + '.csv')        # Crash for large dataset 150GB
                #self.ds.to_dataframe().to_csv(fname + '.csv')       # Crash for large dataset 150GB
                Log().info(f'Done writing file {fname}')

        elif file_ext == '.png':

            vmax = -20
            vmin = -80
            for cat in self.ds['category']:
                Log().info(f'Generating image for category : {cat.values.flatten()[0]}')
                data = self.ds.sel(category=cat)

                fig = plt.figure(figsize=(12, 6))
                ax = plt.axes()
                plt.title('{} @ {}'.format(cat.values, data['channel_id'].values))

                # Set axis limits
                x_lims = mdates.date2num(data['ping_time'].values)

                extent = [x_lims[0], x_lims[-1].astype(float), data['range'].values[-1], data['range'].values[0]]

                im = plt.gca().imshow(10 * np.log10(data['sv'].transpose().values + 10e-20), vmin=vmin,vmax=vmax, extent=extent, origin='upper')

                plt.ylabel('Sv {}(m)'.format(self.vtype))

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
                plt.close()
        else:
            Log().error('{} format not supported'.format(fname[-4:]))

    def cleanup(self):
        if self.tmp_path_name is not None and os.path.exists(self.tmp_path_name):
            shutil.rmtree(self.tmp_path_name)


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

    gridd = rg.getGridd()
    if gridd is not None:
        dstDir = str(Path(args.out).parent)
        for cat in gridd['category']:
            Log().info(f'Generating integration image for category : {cat.values.flatten()[0]}')
            sv = gridd.sel(category=cat.values)['sv']
            if 'range' in gridd.coords._names:
                sum_sv = sv.sum(dim='range')
            elif 'depth' in gridd.coords._names:
                sum_sv = sv.sum(dim='depth')

            sum_sv.plot()
            if not os.path.exists(dstDir):
                os.makedirs(dstDir)
            plt.savefig(dstDir+os.sep+f'cat_{cat.values.flatten()[0]}.png')
            plt.close()

    rg.cleanup()
