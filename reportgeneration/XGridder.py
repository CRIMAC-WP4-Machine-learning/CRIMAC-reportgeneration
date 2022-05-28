import numpy as np
import xarray as xr
import dask
from NPGridder import NPGridder, GridType
#from ZarrGridder import ZarrGridder,GridType

"""
    Lossless griding on Xarrays    
"""

class XGridder(NPGridder):
#class XGridder(ZarrGridder):

    def __init__(self, target_v_bins=None, source_v_bins=None, target_h_bins=None, source_h_bins=None):
        super().__init__(target_v_bins, source_v_bins, target_h_bins, source_h_bins)

    def _regrid(self, W, data):
        # Regridd

        data_mod = dask.array.vstack((data, np.zeros(data.shape[1])))

        return np.dot(W, data_mod)

    def regrid(self, data):

        if self.griddType == GridType.OneDimension:
            W = self._resampleWeight(self.target_v_bins.values, self.source_v_bins.values)
            gridded = self._regrid(W, data.transpose()).transpose()

            return gridded

        elif self.griddType == GridType.TwoDimension:
            WX = self._resampleWeight(self.target_v_bins.values, self.source_v_bins.values)
            griddedX = self._regrid(WX, data.transpose()).transpose()

            WY = self._resampleWeight(self.target_h_bins.values, self.source_h_bins.values)
            griddedXY = self._regrid(WY, griddedX)

            return griddedXY



if __name__ == "__main__":

    import matplotlib.pyplot as plt
    from scipy import interpolate

    noBootstraps = 1000
    n_pings = 1000
    maxRange = 100

    pingStep = 5
    rangeStep = 5
    ratio=[]
    for i in range(0, noBootstraps):

        # generate data
        sampleRange = xr.DataArray(np.arange(0, maxRange, 0.18))
        samplePings = xr.DataArray(np.arange(0, n_pings, 1))
        sv_s = xr.DataArray((np.random.random((n_pings, len(sampleRange))) * 100000).astype(float))
        downSampleRange = xr.DataArray(np.arange(0, maxRange, rangeStep))
        downSamplePing = xr.DataArray(np.arange(0, n_pings, pingStep))

        gridder = XGridder(downSampleRange, sampleRange, downSamplePing, samplePings)

        regrid_sv_s_pings = gridder.regrid(sv_s)
        regrid_sv_s_pings = regrid_sv_s_pings.compute()
        # Project result to old gridd
        f = interpolate.interp2d(downSampleRange, downSamplePing, regrid_sv_s_pings, kind='linear')

        idxp = np.where((samplePings >= downSamplePing[2]) & (samplePings <= downSamplePing[-2]))[0]
        samplePings = samplePings[idxp]
        idxr = np.where((sampleRange >= downSampleRange[2]) & (sampleRange <= downSampleRange[-2]))[0]
        sampleRange = sampleRange[idxr]
        z = f(sampleRange, samplePings)
        sv_s = sv_s[idxp, :].squeeze()[:, idxr].squeeze()

        sumGridd = z.sum()
        sumRaw = sv_s.sum().values

        ratio.append(sumGridd / sumRaw)

    print('sumGridd {}'.format(sumGridd))
    print('sumRaw   {}'.format(sumRaw))
    print('diff   {}'.format(sumGridd - sumRaw))
    print('ratio   {}'.format(sumGridd / sumRaw))

    plt.figure()
    plt.hist(ratio, bins=200)
    plt.title('N={}'.format(len(ratio)))
    plt.xlabel('Ratio')
    plt.ylabel('Count')

    plt.figure()
    plt.subplot(2, 1, 1)
    plt.imshow(sv_s.T)
    plt.subplot(2, 1, 2)
    plt.imshow(z.T, interpolation='nearest')

    plt.show()
