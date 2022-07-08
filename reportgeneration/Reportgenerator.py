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
from Resources import Resources as Res


class Reportgenerator:

    def __init__(self, grid_fname=None, pred_fname=None, bot_fname=None, out_fname=None, freq=38000, SvThreshold=-100, vtype='range', vstep=50,PingAxisIntervalOrigin='start', htype='ping', hstep=50, ChannelDepthStart=0, ChannelDepthEnd=500):
        Log().info('####### Reportgenerator ########')
        self.vtype = vtype
        self.vstep = vstep
        self.htype = htype
        self.hstep = hstep
        self.PingAxisIntervalOrigin = PingAxisIntervalOrigin
        self.out_fname = out_fname
        Res().setTmpDir(str(Path(self.out_fname).parent) + os.sep + 'tmp')
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
            start_time = zarr_out['Time'].values[-1]
            stop_time = zarr_grid['ping_time'].values[-1]
            zarr_grid = zarr_grid.sel(ping_time=slice(start_time, stop_time))
            zarr_pred = zarr_pred.sel(ping_time=slice(start_time, stop_time))
            zarr_bot = zarr_bot.sel(ping_time=slice(start_time, stop_time))

            Log().info(
                'Existing output file time span: \nt0={}\nt1={}'.format(zarr_out['Time'].values[0], start_time))
            Log().info('Got new data spanning:\nt0={}\nt1={}'.format(zarr_grid['ping_time'].values[0], stop_time))
        else:
            Log().info('Starting new outputfile')

        bottomRange = self.extractRangeToBottom(zarr_bot)
        bottomRange = xr.DataArray(bottomRange, coords={'time': (['time'], zarr_pred.ping_time.values)},
                                   dims=['time'])
        bottomDepth = None
        self.worker_data = []

        for cat in zarr_pred["annotation"]["category"]:

            zarr_grid = xr.where(zarr_grid < np.power(10, SvThreshold/10), 0, zarr_grid)

            masked_sv = self.applyMask(zarr_grid, zarr_pred, cat=cat, freq=freq)

            if vtype == 'depth':
                masked_sv = self.rangeToDepthCorrection(masked_sv)
                if bottomDepth is None:
                    bottomRange += (masked_sv['transducer_draft'] + masked_sv['heave']).values
                # Range is now depth
                masked_sv['range'] = masked_sv['range'] + masked_sv['transducer_draft'][0].values

            ekgridder = EKGridder(masked_sv, vtype, vstep, PingAxisIntervalOrigin, htype, hstep, ChannelDepthStart, ChannelDepthEnd)
            if ekgridder.target_h_bins.shape[0] <= 2:
                self.worker_data = None
                Log().info('Not enough data to make a grid.')
                break

            Log().info(f'Gridding category: {cat.values.flatten()[0]}')

            if bottomDepth is None:
                BottomDepth = bottomRange.groupby_bins('time', ekgridder.ping_time).mean()

            rg = ekgridder.regrid()

            if vtype == 'depth':
                rg = rg.rename({'range': 'depth'})

            rg = rg.assign_coords(category=[cat])
            rg = rg.assign_coords(BottomDepth=("ping_time", np.append(BottomDepth.values, np.NaN)))
            self.worker_data.append(rg)

        self.ds = None

    def rangeToDepthCorrection_(self, masked_sv):

        dr = masked_sv['range'].diff('range')[0].values
        ridx = (masked_sv['transducer_draft']+masked_sv['heave'])/dr
        ridx = xr.DataArray.round(ridx).astype(int).data

        """
        # Debug check echogram before heav and draft compensated
        plt.figure()
        plt.imshow(10 * np.log10(masked_sv['sv'][0:1000,:].transpose().values + 10e-20), vmin=-80,vmax=-20, origin='upper')
        plt.axis('auto')
        """

        for offset in np.unique(ridx.compute()):
            colidx = dask.array.argwhere(ridx == offset)
            colidx = colidx.compute().flatten()

            # This is a bottleneck. How to speed up?
            # Try to use storage, see ZarrGridder
            masked_sv['sv'][colidx, :] = masked_sv['sv'][colidx, :].shift(range=offset)

        """
        # Debug check echogram after heav and draft compensated
        plt.figure()
        plt.imshow(10 * np.log10(masked_sv['sv'][0:1000, :].transpose().values + 10e-20), vmin=-80, vmax=-20,
                   origin='upper')
        plt.axis('auto')
        plt.show()
        """
        return masked_sv

    def rangeToDepthCorrection(self, masked_sv):

        dr = masked_sv['range'].diff('range')[0].values
        ridx = (masked_sv['transducer_draft']+masked_sv['heave'])/dr
        ridx = xr.DataArray.round(ridx).astype(int).data

        """
        # Debug check echogram before heav and draft compensated
        plt.figure()
        plt.imshow(10 * np.log10(masked_sv['sv'][0:1000,:].transpose().values + 10e-20), vmin=-80,vmax=-20, origin='upper')
        plt.axis('auto')
        """

        depth_masked_sv = masked_sv.copy()
        for offset in np.unique(ridx.compute()):
            colidx = dask.array.argwhere(ridx == offset)
            colidx = colidx.compute().flatten()

            # This is a bottleneck. How to speed up?
            # Try to use storage, see ZarrGridder
            depth_masked_sv['sv'][colidx, :] = masked_sv['sv'][colidx, :].shift(range=offset)

        masked_sv = depth_masked_sv

        """
        # Debug check echogram after heav and draft compensated
        plt.figure()
        plt.imshow(10 * np.log10(masked_sv['sv'][0:1000, :].transpose().values + 10e-20), vmin=-80, vmax=-20,
                   origin='upper')
        plt.axis('auto')
        plt.show()
        """
        return masked_sv

    def extractRangeToBottom(self, bot):

        # Replace nan with 0, bottom and subbottom is 1
        bot['bottom_range'] = xr.where(bot['bottom_range'].isnull(), 0, 1)

        # Diff in range direction gives 1 at bottom
        bot_ = bot['bottom_range'].diff(dim='range')

        # Find index of bottom
        botIdx = bot_.data.argmax(1)

        # Find range to bottom
        range = bot_['range'].isel(range=botIdx)

        return range.values

    def applyMask(self, data=None, pred=None, cat=None, freq=38000):

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
            masked_sv = fdata['sv'].data * mask.data

        fdata['sv'].data = masked_sv
        return fdata


    def getGridd(self):

        if self.ds is None and self.worker_data is not None:

            # Hack to avoid crash when we save final grid
            # Store grid for each category
            # Then reload and concatenate

            # Ensure tmp directory exists
            tmp_path_name = Res().getTmpDir() + os.sep + '__tmp_main_out'

            if not os.path.exists(tmp_path_name):
                os.makedirs(tmp_path_name)

            # Store each category
            fnames = []
            for d in self.worker_data:
                fname = tmp_path_name+os.sep+f'gridd_{d["category"].values[0]}.zarr'
                fnames.append(fname)
                d.to_zarr(fnames[-1], mode='w',safe_chunks=False)

            # Reload and concatenate
            self.worker_data = []
            for fname in fnames:
                d = xr.open_zarr(fname)
                self.worker_data.append(d)
            #### End hack

            self.ds = xr.concat(self.worker_data, dim='category')

            # Assume first bin in range is nan and last bin in range do not contain data from whole bin
            r0 = self.ds[self.vtype].values[1]
            r1 = self.ds[self.vtype].values[-2]
            self.ds = self.ds.sel({self.vtype:slice(r0, r1)})

            self.ds = self.ds.isel(ping_time=slice(1, len(self.ds['ping_time']) - 1))

            self.ds = self.formatToRapport(self.ds)

        return self.ds

    def formatToRapport(self, ds):

        if 'range' in ds.coords:
            range_or_depth = 'range'
        else :
            range_or_depth = 'depth'

        ds = ds.rename({'latitude': 'Latitude',
                        'longitude': 'Longitude',
                        'ping_time': 'Time',
                        'sv': 'value',
                        range_or_depth: 'ChannelDepthUpper',
                        'category': 'SaCategory'})

        # Add new coordinates
        N = len(ds.Time)
        Latitude2 = np.append(ds.Latitude[1:].values, np.NaN)  # Adress end point
        Longitude2 = np.append(ds.Longitude[1:].values, np.NaN)  # Address last point
        Origin = np.repeat("start", N)
        Origin2 = np.repeat("end", N)
        Validity = np.repeat("V", N)
        # Upper depth of the integrator should use the ChannelDepthStart
        ChannelDepthLower = np.append(ds.ChannelDepthUpper[1:].values, np.NaN)  # Adress end point

        ds = ds.assign_coords(Latitude2=("Time", Latitude2))
        ds = ds.assign_coords(Longitude2=("Time", Longitude2))
        ds = ds.assign_coords(Origin=("Time", Origin))
        ds = ds.assign_coords(Origin2=("Time", Origin2))
        ds = ds.assign_coords(Validity=("Time", Validity))

        ds = ds.assign_coords(ChannelDepthLower=("ChannelDepthUpper", ChannelDepthLower))

        # Ruben: Is this log distance? check this.
        # Arne Johannes: should we also have a Distance2?

        distance = ds.distance[0, :].values
        ds = ds.drop('distance') # This needs to be dropped due to new coordinate Distance
        ds = ds.assign_coords(Distance=("Time", distance))

        # Add attributes

        # http://vocab.ices.dk/?ref=1455
        if self.htype=='nmi':
            PingAxisIntervalType = 'distance'
            PingAxisIntervalUnit = 'nmi'
        else:
            PingAxisIntervalType = self.htype

        if self.htype=='ping':
            PingAxisIntervalUnit = 'ping'
        elif self.htype=='time':
            PingAxisIntervalUnit = 'sec'


        PingAxisInterval = self.hstep

        ds = ds.assign_attrs({
            "PingAxisIntervalType": PingAxisIntervalType,
            "PingAxisIntervalOrigin": self.PingAxisIntervalOrigin, # see http://vocab.ices.dk/?ref=1457
            "PingAxisIntervalUnit": PingAxisIntervalUnit,
            "PingAxisInterval": PingAxisInterval,
            "Platform": "NaN",
            "LocalID": "NaN",
            "Type": "C",
            "Unit": "m2nmi-2"})

        return ds


    def saveGridd(self,fname):

        file_path, file_ext = os.path.splitext(fname)
        file_ext = file_ext.lower()

        if self.getGridd() is None:
            return

        if file_ext == '.zarr':

            if self.has_out_file:
                self.ds.to_zarr(fname, mode='a', append_dim='time')
            else:
                compressor = Blosc(cname='zstd', clevel=3, shuffle=Blosc.BITSHUFFLE)
                encoding = {var: {"compressor": compressor} for var in self.ds.data_vars}
                Log().info(f'Writing gridded data to : {fname}')
                self.ds.to_zarr(fname, mode='w', encoding=encoding)
                Log().info(f'Done writing file {fname}')
        else:
            Log().error('{} format not supported'.format(fname[-4:]))

    def saveImages(self, fname):

        file_path, file_ext = os.path.splitext(fname)
        file_ext = file_ext.lower()

        if self.getGridd() is None:
            return

        if file_ext == '.png':

            vmax = -20
            vmin = -80
            for cat in self.ds['SaCategory']:
                Log().info(f'Generating image for category : {cat.values.flatten()[0]}')
                data = self.ds.sel(SaCategory=cat)

                fig = plt.figure(figsize=(12, 6))
                ax = plt.axes()
                plt.title('{} @ {}'.format(cat.values, data['channel_id'].values))

                # Set axis limits
                x_lims = mdates.date2num(data['Time'].values)

                extent = [x_lims[0], x_lims[-1].astype(float), data['ChannelDepthUpper'].values[-1],
                          data['ChannelDepthUpper'].values[0]]

                im = plt.gca().imshow(10 * np.log10(data['value'].transpose().values + 10e-20), vmin=vmin,vmax=vmax, extent=extent, origin='upper')

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

    def saveReport(self, fname):

        file_path, file_ext = os.path.splitext(fname)
        file_ext = file_ext.lower()

        if self.getGridd() is None:
            return

        if file_ext == '.csv':

            for cat in self.ds['SaCategory']:
                ds = self.ds.sel(SaCategory=cat).copy()

                ds['value'] = ds['value'] * 4 * np.pi * 1852**2 * self.vstep
                df = self.ds.to_dataframe()
                # Add the attributes to the df
                for item in list(self.ds.attrs.items()):
                    df[item[0]] = item[1]
                # Save report to pandas tidy file

                df.to_csv('{}_{}.csv'.format(file_path, cat.values), index=True)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        tmpDir = Res().getTmpDir()
        if os.path.exists(tmpDir):
            shutil.rmtree(tmpDir)


"""
python Reportgenerator.py \
    --data S2019847_0511_sv.zarr
    --pred S2019847_0511_labels.zarr
    --bot S2019847_0511_bottom.zarr
    --out S2019847_0511_report.zarr
    --img S2019847_0511_report.png
    --thr -80
    --freq 38000
    --depth_start 0
    --depth_end 500
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
    parser.add_argument("--depth_start", type=float, help="Start range/depth to integrate over (m)")
    parser.add_argument("--depth_end", type=float, help="End range/depth to integrate over (m)")
    parser.add_argument("--htype", type=str,choices=['ping', 'time' , 'nmi'], help="Type of horizontal integration")
    parser.add_argument("--hstep", type=float, help="Step unit for horizontal integration : #pings | seconds | nautical miles)")
    parser.add_argument("--vtype", type=str, choices=['range', 'depth'], help="Type of vertical integration")
    parser.add_argument("--vstep", type=float,help="Step unit for horizontal integration : meters")

    args = parser.parse_args()

    with Reportgenerator(
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
        args.depth_start,
        args.depth_end
    ) as rg:

        rg.save(args.out)
        rg.save(args.img)

        gridd = rg.getGridd()
        if gridd is not None:
            dstDir = str(Path(args.out).parent)
            for cat in gridd['SaCategory']:
                Log().info(f'Generating integration image for category : {cat.values.flatten()[0]}')
                sv = gridd.sel(SaCategory=cat.values)['value']

                sum_sv = sv.sum(dim='ChannelDepthUpper')

                sum_sv.plot()
                if not os.path.exists(dstDir):
                    os.makedirs(dstDir)
                plt.savefig(dstDir+os.sep+f'cat_{cat.values.flatten()[0]}.png')
                plt.close()


