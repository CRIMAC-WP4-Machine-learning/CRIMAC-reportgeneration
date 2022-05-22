
import os
import traceback
import sys
import shutil
import dask
from dask.distributed import Client
from Logger import Logger as Log
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
                Log().error('{} could not be found'.format(_dir))
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
            Log().error('DATA_INPUT_NAME no set')
            return False

        if self.pred_input_name is None:
            Log().error('PRED_INPUT_NAME no set')
            return False

        if self.output_name is None:
            Log().error('OUTPUT_NAME no set')
            return False

        if self.threshold is None:
            Log().error('THRESHOLD no set')
            return False

        if not isinstance(self.threshold, float):
            Log().error('THRESHOLD needs to be float, got {}'.format(type(self.threshold)))
            return False

        if self.threshold<0 or self.threshold>1:
            Log().error('THRESHOLD needs to be float [0,1], got {}'.format(self.threshold))
            return False

        valid_hitype = ['ping', 'time','nmi']
        if self.hitype is None or self.hitype not in ['ping', 'time','nmi']:
            Log().error(f'HOR_INTEGRATION_TYPE no set or incorrect')
            Log().info(f'Types set to {self.hitype}')
            Log().info(f'Valied types : {valid_hitype}')

            return False

        if self.histep is None or not isinstance(self.histep,(float, int)):
            Log().error('HOR_INTEGRATION_STEP no set correctly')
            Log().info(f'Types set to {self.histep}')
            Log().info('Type must be float or int')
            return False

        valied_vitypes = ['range', 'depth']
        if self.vitype is None or self.vitype not in valied_vitypes:
            Log().error(f'VERT_INTEGRATION_TYPE no set or incorrect')
            Log().info(f'Types set to {self.vitype}')
            Log().info(f'Valied types : {valied_vitypes}')
            return False

        if self.vistep is None or not isinstance(self.vistep, (float, int)):
            Log().error('VERT_INTEGRATION_STEP no set correctly set')
            Log().info(f'Types set to {self.vistep}')
            Log().info('Type mist be float or int')
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
            --env HOR_INTEGRATION_TYPE =  [ping | time | nmi]\n  \
            --env HOR_INTEGRATION_STEP = 100\n \
            --env VERT_INTEGRATION_TYPE=[range | nmi]\n \
            --env VERT_INTEGRATION_STEP=10\n \
            reportgenerator'

    def run(self):

        grid_file_name = '{}{}{}'.format(self.datain, os.sep, self.data_input_name)

        if self.bot_input_name is None:
            bot_file_name = None
        else:
            bot_file_name = '{}{}{}'.format(self.bottomin, os.sep, self.bot_input_name)

        pred_file_name = '{}{}{}'.format(self.predin, os.sep, self.pred_input_name)

        out_file_name = '{}{}{}'.format(self.dataout, os.sep, self.output_name)

        rg = Reportgenerator(
            grid_file_name,
            pred_file_name,
            bot_file_name,
            out_file_name,
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

        rg.cleanup()



if __name__ == '__main__':

    Log(loggerFileName = os.path.expanduser('/dataout'))

    if os.getenv('DEBUG', 'false') == 'true':
        Log().error('Press enter...')
        input()
        sys.exit(0)

    dm = DockerMain()

    if dm.goodtogo:

        # Setting dask
        tmp_dir = os.path.expanduser(dm.dataout + '/tmp')

        dask.config.set({'temporary_directory': tmp_dir})
        client = Client()
        Log().info(client)

        try:
            Log().info('1')
            dm.run()
            Log().info('2')
        except :
            Log().error(traceback.format_exc())

        client.close()
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)

    else :
        Log().error('Error occurred, exiting')
        Log().error('Usage :/n{}'.format(dm.usage()))

    sys.exit(0)
