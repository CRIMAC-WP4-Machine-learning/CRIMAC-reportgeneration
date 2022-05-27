# Meta data requirements

# Meta data from the CONAR-netCDF convention
This is subset from the convention based on what we, more or less, have in our data models.

## Root level

Attributes

:Conventions = "CF-1.7, SONAR-netCDF4-2.0, ACDD-1.3"

:date_created = Timestamp of file creation in ISO8601:2004  (e.g. 2017-05-06T20:21:35Z)

:keywords = EK60 or EK80
 
:sonar_convention_authority = "ICES"

:sonar_convention_name = "SONAR-netCDF4"

:sonar_convention_version = "2.0"

:summary = IMR cruise series

:title = IMR cruise number
 
## Provenance group

Attributes:

:conversion_software_name = "CRIMAC reportgenerator, CRIMAC preprocessor, pyecholab"

:conversion_software_version = "??, CRIMAC preprocessor 0.2, conda_version_20220419"

:history =  "2019-09-07T15:50+00Z File conversion by CRIMAC preprocessor
	         2019-09-07T15:50+00Z File conversion by CRIMAC reportgenerator"


## Sonar group

Attributes:

:sonar_type = "Echosounder"

Types:

byte enum beam_stabilisation_t = 0 {not_stabilised = 0, stabilised = 1}

byte enum beam_t = 4  {single = 0, split_aperture_angles = 1, split_aperture_4_subbeams = 2, split_aperture_3_subbeams = 3, split_aperture_3_1_subbeams = 4}

byte enum transmit_t = 0 {CW = 0, LFM = 1, HFM = 2}

sub group:

Grid_group1

### Grid_group1

Attributes:

beam_mode: vertical

conversion_equation_type : 5

Types:

byte enum backscatter_type_t = 1 {Sv = 0, Sa = 1} 

byte enum range_axis_interval_type_t = 0 {Range = 0, Depth = 1 } : should be set from the parameters

byte enum ping_axis_interval_type_t {Time_seconds = 0, Distance_nautical_miles = 1, Distance_meters = 2, Number_of_ping = 3} : should be set from the parameters

Dimensions:

beam = No of frequencies in our data set

tx_beam = No of frequencies in our data set (for CW data)

frequency = No of frequencies in our data set

ping_axis = ping_time in our data set

range_axis = No depth bins in our data set


Variables:

string beam(beam) : channel_id in our data set
:long_name = "Beam name" 

float frequency(frequency) 
:long_name = "Frequency of the receive echo from spectral analysis of the FM pulse or frequency of the CW pulse." 
:units = "Hz" 
:valid_min = 0.0 
 
string beam_reference(frequency) = channel ID from our data set
:long_name = "Reference to the beam for a given frequency" 
 
backscatter_type(frequency) = 1
:long_name = "Backscatter type for gridded data" 
 
ping_axis_interval_type = 1
:long_name = "Interval type for regridding the data in ping axis" 
 
float ping_axis_interval_value = vertical integration value
:long_name = "Ping axis interval for regridding the data" 
 
range_axis_interval_type = 1 for depth
:long_name = "Interval type for regridding the data in range axis" 
 
float range_axis_interval_value = horizontal integration value
:long_name = "Range axis interval for regridding the data" 
 
uint64 cell_ping_time(ping_axis, tx_beam) |M |Mean timestamp of the pings contributing to the cell.
:axis = "T" 
:calendar = "gregorian" 
:long_name = "Mean time-stamp of each cell" 
:standard_name = "time" 
:units = "nanoseconds since 1970-01-01 00:00:00Z" or "nanoseconds since 1601-01-01 00:00:00Z" 
:coordinates = "ping_axis platform_latitude platform_longitude" 
 
float integrated_backscatter(ping_axis, range_axis, frequency) |M |Integrated backscatter measurement.
:long_name = "Integrated backscatter of the raw backscatter measurements sampled in this cell for each frequency." 
:units = "as appropriate" |Use units appropriate for the data.

# Requirements from ICES acoustic db format

| Level | Variable | zarr-variable | Comment | 
| -| -| -| -|
  | Data | LogDistance | Traveled distance of integrator cell from start of cruise in nautical miles | Not in SONAR-nerCDF4
  | Data | LogTime | Time of the first ping in the integrator cell in ISO 8601 | SONAR-netCDF4 has mean time in grid
  | Data | LogLatitude | Latitude position in decimal degrees of the first ping in integrator cell | Not directly supoprte in SONAR-netCDF4
  | Data | LogLongitude | Longitude position in decimall degrees of the first ping in integrator cell | Not directly supoprte in SONAR-netCDF4
  | Data | LogOrigin | use "start" to indicate LogLatitude and LogLongitude is the first ping | Not supported in SONAR-netCDF4
  | Data | LogLatitude2 | Latitude position in decimal degrees of the last ping in integrator cell | Not directly supported  in SONAR-netCDF4
  | Data | LogLongitude2 | Longitude position in decimall degrees of the last ping in integrator cell | Not directly supported  in SONAR-netCDF4
  | Data | LogOrigin2 | use "start" to indicate LogLatitude and LogLongitude is the last ping | should this be "end"?
  | Data | SampleChannelDepthUpper | Upper depth of the integrator cell in meters relative surface | SONAR-NetCDF4 assumes start at 0 m
  | Data | SampleChannelDepthLower | Lower depth of the integrator cell in meters relative surface | SONAR-NetCDF4 assumes start at 0 m
  | Data | PingAxisInterval | Value of the horizontal size of the integrator | ok
  | Data | PingAxisIntervalType | Indicating the unit of the PingAxisInterval, i.e. distance(nmi), ping, or time (seconds) | ok
  | Data | SampleSvThreshold | The lowest Sv threshold used when integrating | 
  | Data | DataSaCategory | Indicating the acoustic cathegory, i.e. HER for Herring | 
  | Data | DataUnit | Indicating the unit of the integrated value in the cell, i.e. m2nmi-2 (sA) | 
  | Data | DataValue | The acoustic value from the integration of a cell | 

# Minimun requirements for StoX
The minimum data/metadata for the to be accepted by, e.g., StoX are:

| Level | Variable | zarr-variable | Comment | 
| -| -| -| -|
| distance | log_start | distance |  |
| distance | start_time | ping_time |  |
| distance | stop_time | ping_time |  |
| distance | integrator_dist |  | Settiing in the integrator  |
| distance | pel_ch_thickness |  | Settiing in the integrator  |
| distance | lat_start | latitude |  |
| distance | lat_stop | latitude |  |
| distance | lon_start | longitude |  |
| distance | lon_stop | longitude |  |
| frequency | freq | frequency |  |
| frequency | transceiver | frequency | 1 : number of frequencies |
| frequency | upper_integrator_depth | heave + transducer_draft | Check with LSSS |
| ch_type | type | "P" |  |
| sa_by_acocat | acocat | category |  |
| sa | ch | channel_id |  |
| sa | ca | sv | Integrated |

# Refactoring

We will refactor our code to provide these attributes, types, dimensions and variable names:

## Global attributes

:Conventions = "CF-1.7, SONAR-netCDF4-2.0, ACDD-1.3"
:date_created = Timestamp of file creation in ISO8601:2004  (e.g. 2017-05-06T20:21:35Z)
:keywords = "EK60" or "EK80"
:sonar_convention_authority = "ICES"
:sonar_convention_name = "SONAR-netCDF4"
:sonar_convention_version = "2.0"
:summary = IMR cruise series
:title = IMR cruise number
:conversion_software_name = "CRIMAC reportgenerator, CRIMAC preprocessor, pyecholab"
:conversion_software_version = "??, CRIMAC preprocessor 0.2, conda_version_20220419"
:history =  "2019-09-07T15:50+00Z File conversion by CRIMAC preprocessor
	         2019-09-07T15:50+00Z File conversion by CRIMAC reportgenerator"

## Dimensions
(frequency, beam, category, range_axis, ping_axis)

category: The number of acoustic categories in this data set

beam: The number of receive beams in this grid group.

frequency: The number of frequencies in this grid group (only one in our case since we integrate one freq only).

ping_axis: Number of cells in ping dimension.

range_axis : Number of cells in range dimension.

## Variables and associated attributes

channel_id -> string beam(beam)
:long_name = "Beam name" 

main_frequency -> float frequency(frequency) 
:long_name = "Frequency of the receive echo from spectral analysis of the FM pulse or frequency of the CW pulse." 
:units = "Hz" 

category -> int category(category)
:long_name = "Acoustic category"

hitype -> ping_axis_interval_type = 1  {Time_seconds = 0, Distance_nautical_miles = 1, Distance_meters = 2, Number_of_ping = 3}
:long_name = "Interval type for regridding the data in ping axis" 

histep -> float ping_axis_interval_value
:long_name = "Ping axis interval for regridding the data" 

vitype -> range_axis_interval_type = 1 for depth {Range = 0, Depth = 1}
:long_name = "Interval type for regridding the data in range axis" 

vistep -> float range_axis_interval_value
:long_name = "Range axis interval for regridding the data" 


lat_start
lat_stop

lon_start
lon_stop

range 

distance

range

uint64 cell_ping_time_start(ping_axis, tx_beam) |M |Timestamp at start of the pings contributing to the cell. NB: Need to propose change to SONAR-netcdf4
:axis = "T" 
:calendar = "gregorian" 
:long_name = "Mean time-stamp of each cell" 
:standard_name = "time" 
:units = "nanoseconds since 1970-01-01 00:00:00Z" or "nanoseconds since 1601-01-01 00:00:00Z" 
:coordinates = "ping_axis platform_latitude platform_longitude" 

uint64 cell_ping_time_stop(ping_axis, tx_beam) |M |Timestamp at end of the pings contributing to the cell. NB: Need to propose change to SONAR-netcdf4
:axis = "T" 
:calendar = "gregorian" 
:long_name = "Mean time-stamp of each cell" 
:standard_name = "time" 
:units = "nanoseconds since 1970-01-01 00:00:00Z" or "nanoseconds since 1601-01-01 00:00:00Z" 
:coordinates = "ping_axis platform_latitude platform_longitude" 


backscatter_type(frequency) = 1 {Sv = 0, Sa = 1}
:long_name = "Backscatter type for gridded data" 

sv -> float integrated_backscatter(ping_axis, range_axis, frequency) |M |Integrated backscatter measurement.
:long_name = "Integrated backscatter of the raw backscatter measurements sampled in this cell for each frequency." 
:units = "as appropriate" |Use units appropriate for the data.
