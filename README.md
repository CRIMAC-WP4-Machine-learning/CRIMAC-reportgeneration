# This repository contain the code to generate the reports from preprocessed CRIMAC files

A docker image to regrid and generate reports from preprocessed CRIMAC files. The pre-processed data is stored as a  `zarr`/`netcdf` files on disk per survey,
and the energy is allocated to classes based on interpretation masks on the same grid. The interpretation masks per class has a probability 
from 0-1, typically from softmax outputs but can also be other probabilities in the same range. The pixel are associated to a class based on a threshold (input) 
on the probability.

The ouput is the standard ICES data format used in the ICES acoustic database and is a standard input to the StoX index cacluation program. The XSD schema for 
the format is found here:

Other resources :
Here are some example data of the LUF25/ICES acoustic format:
https://github.com/StoXProject/RstoxData/blob/master/inst/testresources/ICES_Acoustic_1.xml
https://github.com/StoXProject/RstoxData/blob/master/inst/testresources/ICES_Acoustic_2.xml

and their format description:
https://www.ices.dk/data/Documents/Acoustic/ICES_Acoustic_data_format_description.zip

## Features

1. Can integrate/regrid onto a new time/distance and depth/range grid by acoustic class
2. Processing and re-gridding the channels are done in parallel (using `Dask`’s delayed).
3. Automatic resuming from the last `ping_time` if the output file exists.
4. Batch processing is done by appending directly to the output file, should be memory efficient.
5. The image of this repository is available at Docker Hub (https://hub.docker.com/r/crimac/reportgeneration).

## Options to run

1. Four directories need to be mounted:

    1. `/datain` should be mounted to the data directory where the preprocessed data files are located.
    2. `/dataout` should be mounted to the directory where the reports are written.
    3. `/predin` should be mounted to the directory where the zarr prediction masks are located.
    4. `/bottomin` should be mounted to the directory where the zarr bottom detection data is located (_optional_).

2. Choose the threshold for the classes: 

    ```bash
    --env THRESHOLD=0.8
    ```

4. Select the horizontal integration type:

    ```bash
    --env HOR_INTEGRATION_TYPE=ping

    --env HOR_INTEGRATION_TYPE=time
    
    --env HOR_INTEGRATION_TYPE=nmi (Not implemented)

    ```

5. Select the vertical integration type:

    ```bash
    --env VERT_INTEGRATION_TYPE=range

    --env VERT_INTEGRATION_TYPE=depth # Not implemented in version 1

    ```

6. Choose the vertical integration grid in depth (VERT_INTEGRATION_TYPE=range) or range (VERT_INTEGRATION_TYPE=depth) and the 
horizontal integration grid in nautical miles (INTEGRATION_TYPE=distance) or seconds (INTEGRATION_TYPE=time): 

    ```bash
    --env HOR_INTEGRATION_STEP=10 # (pings, seconds,nautical miles )
    
    --env VERT_INTEGRATION_STEP=1 # (meters)

    ```
7. Chose the integrator
    only conservative

8. Select file name output (optional, only .zarr)

    ```bash
    --env OUTPUT_NAME=S2020842.zarr
    ```

9. Set if we want a visual overview of the integrated grid (in a PNG format image).

    ```bash
    --env WRITE_PNG=overview.png # No file is generated if left out
    ```

## Example

```bash
docker pull crimac/reportgeneration
docker run -it --name reportgenerator
-v /data/cruise_data/2020/S2020842_PHELMERHANSSEN_1173/ACOUSTIC/PREPROCESSED:/datain
-v /data/cruise_data/2020/S2020842_PHELMERHANSSEN_1173/ACOUSTIC/PRDICTIONS:/predin
-v /data/cruise_data/2020/S2020842_PHELMERHANSSEN_1173/ACOUSTIC/BOTTOM:/botin
-v /data/cruise_data/2020/S2020842_PHELMERHANSSEN_1173/ACOUSTIC/OUT:/dataout
--security-opt label=disable
--env DATA_INPUT_NAME=input_filename.zarr
--env PRED_INPUT_NAME=prediction_filename.zarr
--env BOT_INPUT_NAME=bottom_filename.zarr
--env OUTPUT_NAME=result.zarr
--env WRITE_PNG=result.png
--env THRESHOLD=0.8
--env MAIN_FREQ=38000
--env MAX_RANGE_SRC=500
--env HOR_INTEGRATION_TYPE=ping
--env HOR_INTEGRATION_STEP=100
--env VERT_INTEGRATION_TYPE=range
--env VERT_INTEGRATION_STEP=10
reportgenerator

```
