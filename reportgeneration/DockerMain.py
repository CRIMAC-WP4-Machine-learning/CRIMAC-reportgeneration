
import os
import xarray as xr
import sys
import shutil
import dask
from dask.distributed import Client
from reportgeneration.Reportgenerator import Reportgenerator


class DockerMain :

    def __init__(self):

        self.goodtogo = self.extractAndCheckInputParameters()


    def extractAndCheckInputParameters(self):

        self.bottomin = os.path.expanduser('/bottomin')

        mdirs = []
        for d in ['/datain', '/predin', '/dataout']:

            _dir = os.path.expanduser(d)
            if not os.path.exists(_dir):
                print('{} could not be found, exiting'.format(_dir))
                return False

            mdirs.append(_dir)

        self.datain, self.predin, self.dataout = mdirs

        self.output_type = os.getenv('OUTPUT_TYPE', 'zarr')
        self.main_freq = os.getenv('MAIN_FREQ', 38000)
        self.max_range = os.getenv('MAX_RANGE_SRC', 500)

        self.data_input_name = os.getenv('DATA_INPUT_NAME', None)
        self.pred_input_name = os.getenv('PRED_INPUT_NAME', None)
        self.bot_input_name = os.getenv('BOT_INPUT_NAME', None)
        self.output_name = os.getenv('OUTPUT_NAME', None)
        self.write_png = os.getenv('WRITE_PNG', None)
        self.threshold = os.getenv('THRESHOLD', None)
        self.hitype = os.getenv('HOR_INTEGRATION_TYPE', None)
        self.histep = os.getenv('HOR_INTEGRATION_STEP', None)
        self.vitype = os.getenv('VERT_INTEGRATION_TYPE', None)
        self.vistep = os.getenv('VERT_INTEGRATION_STEP', None)

        if self.data_input_name is None:
            print('DATA_INPUT_NAME no set, exiting')
            return False

        if self.pred_input_name is None:
            print('PRED_INPUT_NAME no set, exiting')
            return False

        if self.bot_input_name is None:
            # Optional
            pass

        if self.output_name is None:
            print('INPUT_NAME no set, exiting')
            return False

        if self.threshold is None:
            print('THRESHOLD no set, exiting')
            return False

        if not isinstance(self.threshold, float):
            print('THRESHOLD needs to be float [0,1],, exiting')
            return False

        if self.threshold<0 or self.threshold>1:
            print('THRESHOLD needs to be float [0,1], exiting')
            return False

        if self.hitype is None or self.hitype not in ['ping', 'time']:
            print('HOR_INTEGRATION_TYPE no set, valid values : ping | time, exiting')
            return False

        if self.histep is None or not isinstance(self.histep,(float, int)):
            print('HOR_INTEGRATION_STEP no set correctly, exiting')
            return False

        if self.vitype is None:
            print('VERT_INTEGRATION_TYPE no set, exiting')
            return False

        if self.vistep is None or not isinstance(self.histep, (float, int)):
            print('VERT_INTEGRATION_STEP no set correctly, exiting')
            return False

        return True


    def run(self):

        if self.goodtogo:

            zarr_gridd = xr.open_zarr('{}{}{}'.format(self.datain, os.sep, self.data_input_name), chunks={'frequency': 'auto', 'ping_time': 'auto', 'range': -1})
            zarr_pred = xr.open_zarr('{}{}{}'.format(self.predin, os.sep, self.pred_input_name))

            rg = Reportgenerator(
                zarr_gridd,
                zarr_pred,
                self.main_freq,
                self.threshold,
                self.vitype,
                self.vistep,
                self.hitype,
                self.histep,
                self.max_range
            )

            rg.save('{}{}{}'.format(self.dataout, os.sep, self.output_name))

            if self.write_png is not None:
                rg.save('{}{}{}'.format(self.dataout, os.sep, self.write_png))



if __name__ == '__main__':

    if os.getenv('DEBUG', 'false') == 'true':
        print('Press enter...')
        input()
        sys.exit(0)


    dm = DockerMain()

    if dm.goodtogo:

        # Setting dask
        tmp_dir = os.path.expanduser(dm.dataout + '/tmp')

        dask.config.set({'temporary_directory': tmp_dir})
        client = Client()
        print(client)

        dm.run()

        # Cleaning up
        client.close()
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)
