import numpy as np
import xarray as xr
import dask
from Logger import Logger as Log
from reportgeneration.XGridder import XGridder


"""
    Lossless gridding on EKdata from gridder    
"""
class EKGridder(XGridder):
    def __init__(self, data, v_integration_type='range', v_step=50,PingAxisIntervalOrigin='start', h_integration_type='ping', h_step=10, ChannelDepthStart=0, ChannelDepthEnd=500):
        self.ping_time = None
        self.distance = None
        self.PingAxisIntervalOrigin = PingAxisIntervalOrigin
        data = data.sel(range=slice(ChannelDepthStart, ChannelDepthEnd))

        source_v_bins, target_v_bins = self.calckBins(data, v_integration_type, v_step, ChannelDepthStart, ChannelDepthEnd)
        source_h_bins, target_h_bins = self.calckBins(data, h_integration_type, h_step, ChannelDepthStart, ChannelDepthEnd)
        super().__init__(target_v_bins, source_v_bins, target_h_bins, source_h_bins)
        self.h_integration_type = h_integration_type
        self.data = data
        self.max_range = ChannelDepthEnd


    def calckBins(self, data, _type, step, ChannelDepthStart, ChannelDepthEnd):

        sbins = None
        tbins = None
        if _type == 'ping':
            sbins = xr.DataArray(np.arange(0, len(data['ping_time'])))

            if self.PingAxisIntervalOrigin == 'start':
                tbins = xr.DataArray(np.arange(0, len(data['ping_time']), step))
            if self.PingAxisIntervalOrigin == 'middle':
                tbins = xr.DataArray(np.arange(-step/2, len(data['ping_time']), step))

            self.ping_time = data['ping_time'].isel(ping_time=np.arange(0, len(data['ping_time']), step).astype(np.int32)).values

        elif _type == 'time':
            sbins = self.calckTimeInSeconds(data['ping_time'])

            if self.PingAxisIntervalOrigin == 'start':
                tbins = xr.DataArray(np.arange(0, sbins[-1].compute(), step))
            if self.PingAxisIntervalOrigin == 'middle':
                tbins = xr.DataArray(np.arange(-step/2, sbins[-1].compute(), step))

            self.ping_time = np.arange(data['ping_time'][0].compute().values, data['ping_time'][-1].compute().values,np.timedelta64(int(step), 's'))

        elif _type == 'nmi':

            sbins = data['distance']

            # Last distance can be nan, use previous

            if self.PingAxisIntervalOrigin == 'start':
                tbins = xr.DataArray(np.arange(data['distance'][0], data['distance'][-1], step))
            if self.PingAxisIntervalOrigin == 'middle':
                tbins = xr.DataArray(np.arange(data['distance'][0]-step/2, data['distance'][-1], step))

            sec = self.calckTimeInSeconds(data['ping_time'])
            isec = np.interp(tbins.compute().values, sbins.values, sec)
            mtime = [data['ping_time'].values[0]+np.timedelta64(int(np.round(t*1000)), 'ms') for t in isec]
            self.ping_time = np.array(mtime)

            """
            import matplotlib.pyplot as plt

            tbins = tbins.compute()
            plt.figure()
            plt.plot(sbins, sbins, '.r', label='Orginal sample')
            plt.plot(tbins, tbins, '.b', label='gridded sample')
            plt.xlabel('distance')
            plt.ylabel('distance')
            plt.legend()

            plt.figure()
            plt.plot(data['ping_time'].values, data['ping_time'].values, '.r',label='Orginal sample')
            plt.plot(self.ping_time, self.ping_time, '.b',label='gridded sample')
            plt.xlabel('time')
            plt.ylabel('time')
            plt.legend()
            plt.show()
            """

        elif _type == 'range':
            sbins = data['range']
            tbins = xr.DataArray(np.arange(data['range'][0], data['range'][-1], step))
        elif _type == 'depth':
            # Range is converted to depth in Reportgenerator
            sbins = data['range']
            #tbins = xr.DataArray(np.arange(data['range'][0], data['range'][-1], step))
            # changed target grid to support channel start and end:
            tbins = xr.DataArray(np.arange(ChannelDepthStart, ChannelDepthEnd, step))


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
        gdata = super().regrid(sv_s['sv'])

        # Regrid axis
        data = data.sel(range=slice(0, 0))  # We dont ned values in range anymore

        data = data.interp(ping_time=self.ping_time)

        # Form correct data cars and coordinates on final grid
        data = data.drop(['range', 'sv'])
        data = data.assign_coords(range = self.target_v_bins.values)
        gdata = dask.array.expand_dims(gdata, axis=0)

        ds = xr.Dataset(data_vars=data.data_vars, coords=data.coords)
        ds = ds.assign(sv=(['category', 'ping_time', 'range'], gdata))

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
