# This repository contain the code to generate the reports from preprocessed CRIMAC files

A docker image to regrid and generate reports from preprocessed CRIMAC files. The pre-processed data is stored as a  `zarr`/`netcdf` files on disk per survey,
and the energy is allocated to classes based on interpretation masks on the same grid. The interpretation masks per class is probaility, and typically generated  from softmax outputs but can also be other probabilities in the same range. The pixel are associated to a class based on a threshold (input) 
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
2. Processing and re-gridding the channels are done in parallel (using `Dask`’s delayed). Removed due to docker problems.
3. Automatic resuming from the last `ping_time` if the output file exists.
4. Batch processing is done by appending directly to the output file, should be memory efficient.
5. The image of this repository is available at Docker Hub (https://hub.docker.com/r/crimac/reportgeneration).

## Options to run

1. Four directories need to be mounted:

    1. `/datain` should be mounted to the data directory where the preprocessed data files are located (_sv and _bottom).
    2. `/predin` should be mounted to the directory where the zarr prediction masks are located.
    3. `/dataout` should be mounted to the directory where the reports are written.

2. Set the survey and file names

    ```bash
    --env SURVEY=S2019847_0511
    
    --env PREDICTIONFILE=S2019847_0511_labels.zarr

    --env REPORTFILE=S2019847_0511_predictions_1_report.zarr

    ```
 

2. Choose the integration threshold:

    ```bash
    --env THRESHOLD=-100

    --env CLASSTRHRESHOLD=0.8 (only necessary if predictions are not binary, not implemented)
    
    ```

3. Select the horizontal integration parameters:

    ```bash
    --env PING_AXIS_INTERVAL_TYPE=distance (pings, seconds,distance)

    --env PING_AXIS_INTERVAL_ORIGIN=start

    --env PING_AXIS_INTERVAL_UNIT=nmi

    --env PING_AXIS_INTERVAL=0.1
    
    ```

4. Select the vertical integration parameters:

    ```bash
    --env CHANNEL_THICKNESS=5
    
    --env CHANNEL_TYPE=depth (depth, range)
    
    --env CHANNEL_DEPTH_START=0
    
    --env CHANNEL_DEPTH_END=500

    ```

## Example

### Image

Build image from Dockerfile 

`docker build --tag reportgenerator .`

or pull from dockerhub

`docker pull crimac/reportgenerator`

### Run container

Example using default parameters

```bash
export DATAIN='/mnt/c/DATAscratch/crimac-scratch/2019/S2019847_0511/'
export DATAOUT='/mnt/c/DATAscratch/crimac-scratch/2019/S2019847_0511/'
export SURVEY='S2019847_0511' # Assumes that ${SURVEY}_sv.zarr file exists
export PREDICTIONFILE='${SURVEY}_labels.zarr'
export REPORTFILE='${SURVEY}_report_1.zarr'

docker run -rm -it --name reportgenerator \
-v "${DATAIN}/ACOUSTIC/GRIDDED":/datain \
-v "${DATAIN}/ACOUSTIC/PREDICTIONS":/predin \
-v "${DATAOUT}/ACOUSTIC/REPORTS"/:/dataout \
--security-opt label=disable \
--env SURVEY=$SURVEY \
--env PREDICTIONFILE=$PREDICTIONFILE \
--env REPORTFILE=$REPORTFILE \
reportgenerator
```