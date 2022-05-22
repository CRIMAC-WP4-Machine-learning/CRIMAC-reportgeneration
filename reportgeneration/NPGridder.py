from enum import Enum, auto
import numpy as np


class GridType(Enum):
    OneDimension = auto()
    TwoDimension = auto()

"""
    Lossless griding on numpy arrays
    Based on : https://github.com/CRIMAC-WP4-Machine-learning/CRIMAC-preprocessing/blob/master/CRIMAC_preprocess.py
"""

class NPGridder:
    # target_v_bins, source_v_bins, target_h_bins, source_h_bins
    def __init__(self, target_v_bins=None, source_v_bins=None, target_h_bins=None, source_h_bins=None):

        self.source_v_bins = source_v_bins
        self.source_h_bins = source_h_bins
        self.target_v_bins = target_v_bins
        self.target_h_bins = target_h_bins

        if source_h_bins is None or target_h_bins is None:
            self.griddType = GridType.OneDimension
        else:
            self.griddType = GridType.TwoDimension

    def _resampleWeight(self, r_t, r_s):
        """
        Input :
            r_t - Target (Sample vector)
            r_s - Source range vector - Binning we end up with

        The regridding is a linear combination of the inputs based
        on the fraction of the source bins to the range bins.
        See the different cases below
        """

        # Create target bins from target range
        bin_r_t = np.append(r_t[0] - (r_t[1] - r_t[0]) / 2, (r_t[0:-1] + r_t[1:]) / 2)
        bin_r_t = np.append(bin_r_t, r_t[-1] + (r_t[-1] - r_t[-2]) / 2)

        # Create source bins from source range
        bin_r_s = np.append(r_s[0] - (r_s[1] - r_s[0]) / 2, (r_s[0:-1] + r_s[1:]) / 2)
        bin_r_s = np.append(bin_r_s, r_s[-1] + (r_s[-1] - r_s[-2]) / 2)

        # Initialize W matrix (sparse)

        W = np.zeros([len(r_t), len(r_s) + 1])
        # NB: + 1 length for space to NaNs in edge case

        # Loop over the target bins
        for i, rt in enumerate(r_t):

            # Check that this is not an edge case
            if bin_r_t[i] > bin_r_s[0] and bin_r_t[i + 1] < bin_r_s[-1]:
                # The size of the target bin
                # example target bin:  --[---[---[---[-
                drt = bin_r_t[i + 1] - bin_r_t[i]  # From example: drt = 4
                #drt=1
                # find the indices in source
                j0 = np.searchsorted(bin_r_s, bin_r_t[i], side='right') - 1
                j1 = np.searchsorted(bin_r_s, bin_r_t[i + 1], side='right')

                # CASE 1: Target higher resolution, overlapping 1 source bin
                # target idx     i    i+1
                # target    -----[-----[-----
                # source    --[-----------[--
                # source idx  j0          j1

                if j1 - j0 == 1:
                    W[i, j0] = 1

                # CASE 2: Target higher resolution, overlapping 1 source bin
                # target idx      i   i+1
                # target    --[---[---[---[-
                # source    -[------[------[-
                # source idx j0            j1

                elif j1 - j0 == 2:
                    W[i, j0] = (bin_r_s[j0 + 1] - bin_r_t[i]) / drt
                    W[i, j1 - 1] = (bin_r_t[i + 1] - bin_r_s[j1 - 1]) / drt

                # CASE 3: Target lower resolution
                # target idx    i       i+1
                # target    ----[-------[----
                # source    --[---[---[---[--
                # source idx  j0          j1

                elif j1 - j0 > 2:
                    for j in range(j0, j1):
                        if j == j0:
                            W[i, j] = (bin_r_s[j + 1] - bin_r_t[i]) / drt
                        elif j == j1 - 1:
                            W[i, j] = (bin_r_t[i + 1] - bin_r_s[j]) / drt
                        else:
                            W[i, j] = (bin_r_s[j + 1] - bin_r_s[j]) / drt

            #  Edge case 1
            # target idx    i       i+1
            # target    ----[-------[----
            # source        #end# [---[---[
            # source idx          j0  j1

            #  Edge case 2
            # target idx    i       i+1
            # target    ----[-------[----
            # source    --[---[ #end#
            # source idx  j0  j1
            else:
                # Edge case (NaN must be in W, not in sv_s.
                # Or else np.dot failed)
                W[i, -1] = np.nan
        return W


    def _regrid(self, W, data):
        # Regridd
        data_mod = np.vstack((data, np.zeros(data.shape[1])))
        return np.dot(W, data_mod)

    def regrid(self, data):

        if self.griddType == GridType.OneDimension:
            W = self._resampleWeight(self.target_v_bins, self.source_v_bins)
            data = self._regrid(W, data.T).T

            return data

        elif self.griddType == GridType.TwoDimension:
            W = self._resampleWeight(self.target_v_bins, self.source_v_bins)
            data = self._regrid(W, data.T).T

            W = self._resampleWeight(self.target_h_bins, self.source_h_bins)
            data = self._regrid(W, data)

            return data


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
        print(i)

        # generate data
        sampleRange = np.arange(0, maxRange, 0.18)
        samplePings = np.arange(0, n_pings, 1)
        sv_s = (np.random.random((n_pings, len(sampleRange))) * 100000).astype(float)
        downSampleRange = np.arange(0, maxRange, rangeStep)
        downSamplePing = np.arange(0, n_pings, pingStep)

        gridder = NPGridder(downSampleRange, sampleRange, downSamplePing, samplePings)

        regrid_sv_s_pings = gridder.regrid(sv_s)
        # Project result to old gridd
        f = interpolate.interp2d(downSampleRange,downSamplePing, regrid_sv_s_pings, kind='linear')

        idxp = np.where((samplePings >= downSamplePing[2]) & (samplePings <= downSamplePing[-2]))
        samplePings = samplePings[idxp]
        idxr = np.where((sampleRange >= downSampleRange[2]) & (sampleRange <= downSampleRange[-2]))
        sampleRange = sampleRange[idxr]
        z = f(sampleRange,samplePings)
        sv_s = sv_s[idxp, :].squeeze()[:, idxr].squeeze()

        sumGridd = z.sum()
        sumRaw = sv_s.sum()

        ratio.append(sumGridd/sumRaw)

    print('sumGridd {}'.format(sumGridd))
    print('sumRaw   {}'.format(sumRaw))
    print('diff   {}'.format(sumGridd - sumRaw))
    print('ratio   {}'.format(sumGridd/sumRaw))


    plt.figure()
    plt.hist(ratio,bins=200)
    plt.title('N={}'.format(len(ratio)))
    plt.xlabel('Ratio')
    plt.ylabel('Count')

    plt.figure()
    plt.subplot(2, 1, 1)
    plt.imshow(sv_s.T)
    plt.subplot(2, 1, 2)
    plt.imshow(z.T, interpolation='nearest')

    plt.show()
