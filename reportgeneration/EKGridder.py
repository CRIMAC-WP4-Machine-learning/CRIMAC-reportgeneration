import numpy as np
import xarray as xr
import dask
from Logger import Logger as Log
from reportgeneration.XGridder import XGridder


"""
    Lossless gridding on EKdata from gridder    
"""
class EKGridder(XGridder):
    def __init__(self, data, v_integration_type='range', v_step=50, h_integration_type='ping', h_step=10, max_range=500):
        self.ping_time = None
        self.distance = None

        # Limit range according to max_range
        data = data.sel(range=slice(0, max_range))

        source_v_bins, target_v_bins = self.calckBins(data, v_integration_type, v_step)
        source_h_bins, target_h_bins = self.calckBins(data, h_integration_type, h_step)
        super().__init__(target_v_bins,source_v_bins, target_h_bins, source_h_bins)
        self.h_integration_type = h_integration_type
        self.data = data
        self.max_range = max_range


    def calckBins(self, data, _type, step):

        sbins = None
        tbins = None
        if _type == 'ping':
            sbins = dask.delayed(xr.DataArray(np.arange(0, len(data['ping_time']))))
            tbins = dask.delayed(xr.DataArray(np.arange(0, len(data['ping_time']), step)))
            self.ping_time = data['ping_time'].isel(ping_time=np.arange(0, len(data['ping_time']), step).astype(np.int32)).values
            #self.distance = data['distance'].values
            """
            self.ping_time = xr.DataArray(
                    data['ping_time'].isel(ping_time=np.arange(0, len(data['ping_time']), step).astype(np.int32)).values
                )

            self.distance = xr.DataArray(
                    data['distance'].sel(ping_time=self.ping_time)
                )
            """

        elif _type == 'time':
            sbins = dask.delayed(self.calckTimeInSeconds)(data['ping_time'])
            tbins = dask.delayed(xr.DataArray(np.arange(0, sbins[-1].compute(), step)))
            self.ping_time = np.arange(data['ping_time'][0].compute().values, data['ping_time'][-1].compute().values,np.timedelta64(step, 's'))
            """
            self.ping_time = dask.delayed(
                xr.DataArray(
                    np.arange(data['ping_time'][0].compute().values, data['ping_time'][-1].compute().values,np.timedelta64(step, 's'))
                )
            )
            """
            """
            self.distance = dask.delayed(
                xr.DataArray(
                    data['distance'].interp(ping_time=self.ping_time)
                )
            )
            """
        elif _type == 'distance':
            sbins = data['distance']
            tbins = dask.delayed(xr.DataArray(np.arange(data['distance'][0], data['distance'][-1], step)))

            sec = self.calckTimeInSeconds(data['ping_time'])
            isec = np.interp(tbins.compute().values, sbins.values, sec)
            mtime = [data['ping_time'].values[0]+np.timedelta64(int(np.round(t*1000)), 'ms') for t in isec]
            self.ping_time = np.array(mtime)
            """
            self.ping_time = dask.delayed(
                xr.DataArray(mtime)
                )

        
            self.distance = dask.delayed(
                xr.DataArray(
                    data['distance'].interp(ping_time=self.ping_time)
                )
            )
            """

            """
            import matplotlib.pyplot as plt

            tbins = tbins.compute()
            plt.figure()
            plt.plot(sbins, sbins, '.r')
            plt.plot(tbins, tbins, '.b')
            plt.xlabel('distance')
            plt.ylabel('distance')

            plt.figure()
            plt.plot(data['ping_time'].values, data['ping_time'].values, '.r')
            plt.plot(self.ping_time.values, self.ping_time.values, '.b')
            plt.xlabel('time')
            plt.ylabel('time')

            print()
            """

        elif _type == 'range':
            sbins = data['range']
            tbins = dask.delayed(xr.DataArray(np.arange(0, data['range'][-1], step)))
        else:
            Log().error('{} integration type not defined'.format(_type))

        return sbins, tbins


    def calckTimeInSeconds(self, mtime):

        dt = (mtime['ping_time'].diff('ping_time') / np.timedelta64(1, 's')).values
        dt = np.insert(dt, 0, 0, axis=0)

        return xr.DataArray(np.cumsum(dt))



    def regrid(self, data=None):

        if data is None:
            data = self.data

        sv_s = data.fillna(0).squeeze()

        gdata = super().regrid(sv_s['sv'].values)

        data = data.sel(range=slice(0, 0))  # We dont ned values in range anymore
        data = data.interp(ping_time=self.ping_time)

        ds = xr.Dataset(
            data_vars=dict(sv=(['ping_time', 'range'], gdata)),
            coords=dict(
                frequency=data['frequency'],
                range=self.target_v_bins.compute().values,
                ping_time=data['ping_time'].values,
                distance= ('ping_time',data['distance'].values),
                latitude= ('ping_time',data['latitude'].values),
                longitude= ('ping_time',data['longitude'].values),
                channel_id= data['channel_id'].values
            )
        )

        return ds


if __name__ == "__main__":

    import matplotlib.pyplot as plt
    import os

    baseDir = r'C:\Users\Ruben\SkyLagring\Sync\Dev\Proj\2019Q3-CRIMAC\2021Q4-Integrator\Data'

    datain = baseDir  # the data directory where the preprocessed data files are located.
    dataout = baseDir  # directory where the reports are written.
    workin = baseDir  # the directory where the zarr prediction masks are located.
    bottomin = baseDir  # the directory where the zarr bottom detection data is located (_optional_).

    MAIN_FREQ = 38000
    MAX_RANGE_SRC = 100
    THRESHOLD = 0.2  # threshold for the classes
    HOR_INTEGRATION_TYPE = 'time' # 'ping' | 'time' | 'distance'

    VERT_INTEGRATION_TYPE = 'range' # 'depth'

    HOR_INTEGRATION_STEP = 100  # seconds | pings | meters | nmi
    VER_INTEGRATION_STEP = 10  # Always in meters

    OUTPUT_NAME = 'S2020842.xml'  # file name output (optional,  default to `out.<zarr/nc>`)
    WRITE_PNG = 'overview.png'  # No file is generated if left out

    category = 'pred_sandeel'
    integrationFreq = 38000

    zarr_gridd = xr.open_zarr(datain + os.sep + r'zarr_gridd_sub.zarr',
                              chunks={'frequency': 'auto', 'ping_time': 'auto', 'range': -1})

    rg = EKGridder(
        zarr_gridd.sel(frequency=integrationFreq),
        VERT_INTEGRATION_TYPE,
        VER_INTEGRATION_STEP,
        HOR_INTEGRATION_TYPE,
        HOR_INTEGRATION_STEP,
        MAX_RANGE_SRC
    )

    xregr = rg.regrid()


    plt.figure()
    plt.title('raw and gridded time gridded on {}'.format(HOR_INTEGRATION_TYPE))
    plt.plot(zarr_gridd['ping_time'].values, zarr_gridd['ping_time'].values, 'x', label='raw ping time')
    plt.plot(xregr['ping_time'].values,xregr['ping_time'].values,'.',label='gidded ping time')
    plt.legend()


    plt.figure()
    plt.subplot(2, 1, 1)
    plt.title('sv')
    plt.imshow(10 * np.log10(zarr_gridd.sel(frequency=integrationFreq)['sv'].T + 10e-20))

    plt.axis('auto')

    plt.subplot(2,1,2)
    plt.title('sv')
    plt.imshow(10 * np.log10(xregr['sv'].squeeze().T + 10e-20))

    plt.axis('auto')
    plt.show()
