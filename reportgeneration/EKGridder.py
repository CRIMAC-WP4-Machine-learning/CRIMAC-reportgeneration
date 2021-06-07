import numpy as np
import xarray as xr
import dask
from reportgeneration.XGridder import XGridder


"""
    Lossless gridding on EKdata from gridder    
"""
class EKGridder(XGridder):
    def __init__(self, data, v_integration_type='range', v_step=50, h_integration_type='ping', h_step=10, max_range=500):
        self.ping_time = None

        # Limit range according to max_range
        data = data.sel(range=slice(0, max_range))

        source_v_bins, target_v_bins = self.calckBins(data, v_integration_type, v_step)
        source_h_bins, target_h_bins = self.calckBins(data, h_integration_type, h_step)
        super().__init__(target_v_bins,source_v_bins, target_h_bins, source_h_bins)

        self.data = data
        self.max_range = max_range


    def calckBins(self, data, _type, step):

        sbins = None
        tbins = None
        if _type == 'ping':
            sbins = dask.delayed(xr.DataArray(np.arange(0, len(data['ping_time']))))
            tbins = dask.delayed(xr.DataArray(np.arange(0, len(data['ping_time']), step)))
            self.ping_time = data['ping_time'][np.arange(0, len(data['ping_time']), step)].values
        elif _type == 'range':
            sbins = data['range']
            tbins = dask.delayed(xr.DataArray(np.arange(0, data['range'][-1], step)))
        else:
            print('{} integration type not defined'.format(_type))

        return sbins, tbins



    def regrid(self, data=None):

        if data is None:
            data = self.data

        sv_s = data['sv'].fillna(0).squeeze()

        gdata = super().regrid(sv_s)

        ds = xr.Dataset(
            data_vars = dict(sv=(['ping_time', 'range'], gdata)),
            coords=dict(
                frequency = data['frequency'],
                range = self.target_v_bins.compute().values,
                ping_time = self.ping_time
            )
        )

        return ds


if __name__ == "__main__":

    import matplotlib.pyplot as plt
    import os
    import sys

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

    category = 'pred_sandeel'
    integrationFreq = 38000

    zarr_gridd = xr.open_zarr(datain + os.sep + r'zarr_gridd_sub.zarr',
                              chunks={'frequency': 'auto', 'ping_time': 'auto', 'range': -1})

    rg = EKGridder(
        zarr_gridd,
        VERT_INTEGRATION_TYPE,
        VER_INTEGRATION_STEP,
        HOR_INTEGRATION_TYPE,
        HOR_INTEGRATION_STEP,
        MAX_RANGE_SRC
    )

    xregr = rg.regrid()

    for f in xregr['frequency']:
        plt.figure()
        plt.subplot(2, 1, 1)
        plt.title('sv')
        plt.imshow(10 * np.log10(zarr_gridd.sel(frequency=f)['sv'].T + 10e-20))

        plt.axis('auto')

        plt.subplot(2,1,2)
        plt.title('sv')
        plt.imshow(10 * np.log10(xregr['sv'].squeeze().T + 10e-20))

        plt.axis('auto')
        plt.show()
