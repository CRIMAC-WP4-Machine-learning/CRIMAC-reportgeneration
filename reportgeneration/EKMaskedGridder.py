import dask
import xarray as xr
import numpy as np
from reportgeneration.EKGridder import EKGridder
from Logger import Logger as Log
from dask.diagnostics import ProgressBar
import pdb

"""
    Lossless gridding masked with predictions on EKdata from gridder and prediction from predictor
    Gridds on one frequency over all categories    
"""
class EKMaskedGridder:
    def __init__(self,data=None, pred=None,bot=None,freq=38000, threshold=0.5,vtype='range',vstep=50,htype='ping',hstep=50, max_range=500):
        self.worker_data = []
        self.vtype = vtype
        # Ruben: Check the diff on this part:
        for cat in pred["annotation"]["category"]:
            Log().info(f'Gridding category: {cat.values.flatten()[0]}')
            #pdb.set_trace()
            result = self.maskAndRegrid(
                data,
                pred["annotation"].sel(category=cat.values),
                bot,
                cat,
                freq,
                threshold,
                vtype,
                vstep,
                htype,
                hstep,
                max_range
            )
            # Insert metadata
            # https://github.com/CRIMAC-WP4-Machine-learning/CRIMAC-data-organisation
            self.worker_data.append(result)

    def maskAndRegrid(self, data, mask,bot, cat, FREQ, THR, V_TYPE, V_STEP, H_TYPE, H_STEP, max_range):

        data = data.sel(frequency=FREQ)

        mask = mask.transpose('ping_time', 'range')
        """
        import matplotlib.pylab as plt
        plt.imshow(mask[::200, :].values.astype(float))
        plt.axis('auto')
        plt.show()
        """

        with dask.config.set(**{'array.slicing.split_large_chunks': False}):
            masked_sv = data * mask

        masked_sv = masked_sv.assign_coords(distance=data.distance)

        rg = EKGridder(masked_sv, V_TYPE, V_STEP, H_TYPE, H_STEP, max_range).regrid()
        rg = rg.assign_coords(category=[cat])

        return rg




if __name__ == "__main__":

    import matplotlib.pyplot as plt
    import os

    baseDir = r'Z:\Dev\Data\CRIMAC\Data\03Subset\01'

    datain = baseDir  # the data directory where the preprocessed data files are located.
    dataout = baseDir  # directory where the reports are written.
    workin = baseDir  # the directory where the zarr prediction masks are located.
    bottomin = baseDir  # the directory where the zarr bottom detection data is located (_optional_).

    MAIN_FREQ = 38000
    MAX_RANGE_SRC = 100
    THRESHOLD = 0.2  # threshold for the classes
    HOR_INTEGRATION_TYPE = 'ping' # 'ping' | 'time' | 'distance'

    VERT_INTEGRATION_TYPE = 'range' # 'depth'

    HOR_INTEGRATION_STEP = 100  # seconds | pings | meters | nmi
    VER_INTEGRATION_STEP = 10  # Always in meters

    OUTPUT_NAME = 'S2020842.xml'  # file name output (optional,  default to `out.<zarr/nc>`)
    WRITE_PNG = 'overview.png'  # No file is generated if left out

    zarr_gridd = xr.open_zarr(datain + os.sep + r'zarr_gridd_sub.zarr',
                              chunks={'frequency': 'auto', 'ping_time': 'auto', 'range': -1})
    zarr_pred = xr.open_zarr(workin + os.sep + r'zarr_pred_sub.zarr')

    ekmg = EKMaskedGridder(
        zarr_gridd,
        zarr_pred,
        MAIN_FREQ,
        THRESHOLD,
        VERT_INTEGRATION_TYPE,
        VER_INTEGRATION_STEP,
        HOR_INTEGRATION_TYPE,
        HOR_INTEGRATION_STEP,
        MAX_RANGE_SRC)

    allData = ekmg.gridd()

    for cat in allData['category'].values:

        plt.figure()
        plt.subplot(2, 1, 1)
        plt.title('sv : {}'.format(cat))
        plt.imshow(10 * np.log10(zarr_gridd.sel(frequency=MAIN_FREQ)['sv'].T + 10e-20))

        plt.axis('auto')

        plt.subplot(2,1,2)
        plt.title('sv')
        plt.imshow(10 * np.log10(allData.sel(category=cat).transpose()['sv'].values + 10e-20))

        plt.axis('auto')
    plt.show()
