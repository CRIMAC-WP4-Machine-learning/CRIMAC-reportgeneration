
import os
import traceback
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
                print('{} could not be found'.format(_dir))
                return False

            mdirs.append(_dir)

        self.datain, self.predin, self.dataout = mdirs

        self.output_type = os.getenv('OUTPUT_TYPE', 'zarr')
        self.main_freq = float(os.getenv('MAIN_FREQ', 38000))
        self.max_range = float(os.getenv('MAX_RANGE_SRC', 500))

        self.data_input_name = os.getenv('DATA_INPUT_NAME', None)
        self.pred_input_name = os.getenv('PRED_INPUT_NAME', None)
        self.bot_input_name = os.getenv('BOT_INPUT_NAME', None)
        self.output_name = os.getenv('OUTPUT_NAME', None)
        self.write_png = os.getenv('WRITE_PNG', None)
        self.threshold = float(os.getenv('THRESHOLD', None))
        self.hitype = os.getenv('HOR_INTEGRATION_TYPE', None)
        self.histep = float(os.getenv('HOR_INTEGRATION_STEP', None))
        self.vitype = os.getenv('VERT_INTEGRATION_TYPE', None)
        self.vistep = float(os.getenv('VERT_INTEGRATION_STEP', None))

        if self.data_input_name is None:
            print('DATA_INPUT_NAME no set')
            return False

        if self.pred_input_name is None:
            print('PRED_INPUT_NAME no set')
            return False

        if self.bot_input_name is not None:
            print('BOT_INPUT_NAME. Masking with bottom data not implemented. Continu without bottom data')

        if self.output_name is None:
            print('OUTPUT_NAME no set')
            return False

        if self.threshold is None:
            print('THRESHOLD no set')
            return False

        if not isinstance(self.threshold, float):
            print('THRESHOLD needs to be float, got {}'.format(type(self.threshold)))
            return False

        if self.threshold<0 or self.threshold>1:
            print('THRESHOLD needs to be float [0,1], got {}'.format(self.threshold))
            return False

        if self.hitype is None or self.hitype not in ['ping', 'time']:
            print('HOR_INTEGRATION_TYPE no set, valid values : ping | time')
            return False

        if self.histep is None or not isinstance(self.histep,(float, int)):
            print('HOR_INTEGRATION_STEP no set correctly')
            return False

        if self.vitype is None:
            print('VERT_INTEGRATION_TYPE no set')
            return False

        if self.vistep is None or not isinstance(self.histep, (float, int)):
            print('VERT_INTEGRATION_STEP no set correctly set')
            return False

        return True

    def usage(self):
        return \
            'docker run -it --name reportgenerator\n \
            -v /data/cruise_data/2020/S2020842_PHELMERHANSSEN_1173/ACOUSTIC/PREPROCESSED:/datain\n \
            -v /data/cruise_data/2020/S2020842_PHELMERHANSSEN_1173/ACOUSTIC/PRDICTIONS:/predin\n \
            -v /data/cruise_data/2020/S2020842_PHELMERHANSSEN_1173/ACOUSTIC/BOTTOM:/botin (optional)\n \
            -v /data/cruise_data/2020/S2020842_PHELMERHANSSEN_1173/ACOUSTIC/OUT:/dataout\n \
            --security-opt label=disable\n \
            --env DATA_INPUT_NAME=input_filename.zarr\n \
            --env PRED_INPUT_NAME=prediction_filename.zarr\n \
            --env BOT_INPUT_NAME=bottom_filename.zarr (optional)\n\
            --env OUTPUT_NAME=result.zarr\n\
            --env WRITE_PNG=result.png\n \
            --env THRESHOLD=0.8\n \
            --env MAIN_FREQ = 38000\n \
            --env MAX_RANGE_SRC = 500\n \
            --env HOR_INTEGRATION_TYPE = ping [ping | time | nmi]\n  \
            --env HOR_INTEGRATION_STEP = 100\n \
            --env VERT_INTEGRATION_TYPE=range\n \
            --env VERT_INTEGRATION_STEP=10\n \
            reportgenerator'

    def run(self):

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

        try:
            dm.run()
        except :
            traceback.print_exc()

        client.close()
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)

    else :
        print('Error occurred, exiting')
        print('Usage :/n{}'.format(dm.usage()))

    sys.exit(0)