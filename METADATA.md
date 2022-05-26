# Meta data requirements


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

sub group

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
 3+|{attr}:long_name = "Range axis interval for regridding the data" 
 
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
  | Data | LogDistance | Traveled distance of integrator cell from start of cruise in nautical miles | 
  | Data | LogTime | Time of the first ping in the integrator cell in ISO 8601 | 
  | Data | LogLatitude | Latitude position in decimal degrees of the first ping in integrator cell |
  | Data | LogLongitude | Longitude position in decimall degrees of the first ping in integrator cell | 
  | Data | LogOrigin | use "start" to indicate LogLatitude and LogLongitude is the first ping | 
  | Data | LogLatitude2 | Latitude position in decimal degrees of the last ping in integrator cell |
  | Data | LogLongitude2 | Longitude position in decimall degrees of the last ping in integrator cell | 
  | Data | LogOrigin2 | use "start" to indicate LogLatitude and LogLongitude is the last ping | 
  | Data | SampleChannelDepthUpper | Upper depth of the integrator cell in meters relative surface | 
  | Data | SampleChannelDepthLower | Lower depth of the integrator cell in meters relative surface | 
  | Data | PingAxisInterval | Value of the horizontal size of the integrator | 
  | Data | PingAxisIntervalType | Indicating the unit of the PingAxisInterval, i.e. distance(nmi), ping, or time (seconds) | 
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

