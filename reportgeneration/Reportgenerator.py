
import xarray as xr
from numcodecs import Blosc
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os

from reportgeneration.EKMaskedGridder import EKMaskedGridder


class Reportgenerator:

    def __init__(self,data=None, pred=None, freq=38000, threshold=0.5, vtype='range', vstep=50, htype='ping', hstep=50, max_range=500):
        self.ekmg = EKMaskedGridder(data, pred, freq, threshold, vtype, vstep, htype, hstep, max_range)
        self.ds = None

    def save(self, fname):


        file_path, file_ext = os.path.splitext(fname)
        file_ext = file_ext.lower()

        # Do griding if it has not already been done
        if file_ext in ['.zarr', '.png'] and self.ds is None:
            self.ds = self.ekmg.gridd()

        if file_ext == '.zarr':
            compressor = Blosc(cname='zstd', clevel=3, shuffle=Blosc.BITSHUFFLE)
            encoding = {var: {"compressor": compressor} for var in self.ds.data_vars}
            self.ds.to_zarr(fname, mode="w", encoding=encoding)
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

                im = plt.gca().imshow(10 * np.log10(data.transpose()['sv'].values + 10e-90), vmin=vmin,vmax=vmax, extent=extent,origin='upper')

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
            print('{} format not supported'.format(fname[-4:]))


if __name__ == "__main__":


    baseDir = r'C:\Users\Ruben\SkyLagring\Sync\Dev\Proj\2019Q3-CRIMAC\2021Q4-Integrator\Data'

    datain = baseDir  # the data directory where the preprocessed data files are located.
    dataout = baseDir  # directory where the reports are written.
    workin = baseDir  # the directory where the zarr prediction masks are located.
    bottomin = baseDir  # the directory where the zarr bottom detection data is located (_optional_).

    MAIN_FREQ = 38000
    MAX_RANGE_SRC = 100
    THRESHOLD = 0.2  # threshold for the classes
    HOR_INTEGRATION_TYPE = 'ping' # 'ping' | 'time' | 'distance'

    VERT_INTEGRATION_TYPE = 'range' # 'depth'

    HOR_INTEGRATION_STEP = 10  # seconds | pings | meters | nmi
    VER_INTEGRATION_STEP = 5  # Always in meters

    OUTPUT_NAME = 'S2020842.xml'  # file name output (optional,  default to `out.<zarr/nc>`)
    WRITE_PNG = 'overview.png'  # No file is generated if left out

    zarr_gridd = xr.open_zarr(datain + os.sep + r'zarr_gridd_sub.zarr',
                              chunks={'frequency': 'auto', 'ping_time': 'auto', 'range': -1})
    zarr_pred = xr.open_zarr(workin + os.sep + r'zarr_pred_sub.zarr')

    rg = Reportgenerator(
        zarr_gridd,
        zarr_pred,
        MAIN_FREQ,
        THRESHOLD,
        VERT_INTEGRATION_TYPE,
        VER_INTEGRATION_STEP,
        HOR_INTEGRATION_TYPE,
        HOR_INTEGRATION_STEP,
        MAX_RANGE_SRC
    )

    rg.save(dataout + os.sep + r'zarr_report.zarr')
    rg.save(dataout + os.sep + r'zarr_report.png')
