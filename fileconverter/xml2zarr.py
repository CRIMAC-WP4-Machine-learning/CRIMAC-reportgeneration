import xarray as xr
import numpy as np
import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt


def report_xml2xarray(path_xml: str, frequency: int):
    '''
    Convert LSSS report file from xml to xarray for a specified frequency.

    :param path_xml: (str) path to xml file
    :param frequency: (int) selected frequency in Hz
    :return: (xrarray.Dataset) xarray dataset
    '''

    # Note:
    # Some xml files has specified URI namespaces, e.g. xmlns="http://www.imr.no/formats/nmdechosounder/v1".
    # This prepend all tags on parsing, e.g. from 'distance' to '{http://www.imr.no/formats/nmdechosounder/v1}distance'.
    # We therefore use {*}-expressions such as '{*}distance' in searching methods to ignore any specified URI namespaces.

    def get_distance_values(root: ET.Element, variable: str, is_attrib: bool, dtype: str):
        if is_attrib:
            x = [distance.attrib[variable] for distance in root.find('{*}distance_list').findall('{*}distance')]
        else:
            x = [distance.find('{*}'+variable).text for distance in root.find('{*}distance_list').findall('{*}distance')]
        return np.array(x, dtype=dtype)

    def get_distance_frequency_values(root: ET.Element, variable: str, dtype: str):
        x = [distance.find('{*}frequency[@freq=\"'+str(frequency)+'\"]').find('{*}'+variable).text for distance in
             root.find('{*}distance_list').findall('{*}distance')]
        return np.array(x, dtype=dtype)

    tree = ET.parse(path_xml)
    root = tree.getroot()

    # Get list of the acoustic categories
    category = sorted([int(acocat.attrib['acocat']) for acocat in root.find('{*}acocat_list').findall('{*}acocat')])

    # Get data per distance
    log_start = get_distance_values(root, 'log_start', True, 'float32')
    start_time = get_distance_values(root, 'start_time', True, 'datetime64[ns]')
    stop_time = get_distance_values(root, 'stop_time', False, 'datetime64[ns]')
    integrator_dist = get_distance_values(root, 'integrator_dist', False, 'float32')
    pel_ch_thickness = get_distance_values(root, 'pel_ch_thickness', False, 'float32')
    include_estimate = get_distance_values(root, 'include_estimate', False, 'bool')
    lat_start = get_distance_values(root, 'lat_start', False, 'float32')
    lat_stop = get_distance_values(root, 'lat_stop', False, 'float32')
    lon_start = get_distance_values(root, 'lon_start', False, 'float32')
    lon_stop = get_distance_values(root, 'lon_stop', False, 'float32')
    freq = np.float(frequency)
    threshold = get_distance_frequency_values(root, 'threshold', 'float32')
    num_pel_ch = get_distance_frequency_values(root, 'num_pel_ch', 'int')
    min_bot_depth = get_distance_frequency_values(root, 'min_bot_depth', 'float32')
    max_bot_depth = get_distance_frequency_values(root, 'max_bot_depth', 'float32')
    upper_interpret_depth = get_distance_frequency_values(root, 'upper_interpret_depth', 'float32')
    lower_interpret_depth = get_distance_frequency_values(root, 'lower_interpret_depth', 'float32')
    upper_integrator_depth = get_distance_frequency_values(root, 'upper_integrator_depth', 'float32')
    lower_integrator_depth = get_distance_frequency_values(root, 'lower_integrator_depth', 'float32')
    quality = get_distance_frequency_values(root, 'quality', 'int')
    bubble_corr = get_distance_frequency_values(root, 'bubble_corr', 'float32')

    # Get the full range of pelagic channel numbers (lowest to highest record)
    all_pel_ch = list()
    for distance in root.find('{*}distance_list').findall('{*}distance'):
        ch_type_p = distance.find('{*}frequency[@freq=\"'+str(frequency)+'\"]').find('{*}ch_type[@type="P"]')
        if ch_type_p is not None:
            for sa_by_acocat in ch_type_p.findall('{*}sa_by_acocat'):
                for sa in sa_by_acocat.findall('{*}sa'):
                    all_pel_ch.append(sa.attrib['ch'])
    all_pel_ch = [int(ch) for ch in set(all_pel_ch)]
    assert len(all_pel_ch) > 0
    range_pel_ch = np.arange(np.min(all_pel_ch), np.max(all_pel_ch) + 1)

    # Get the sa values per (distance, category, pelagic channel) - only use P (peleagic) values, discard B (bottom) values.
    sa_values = []
    for distance in root.find('{*}distance_list').findall('{*}distance'):
        tmp = {cat: {ch: 0.0 for ch in range_pel_ch} for cat in category}
        ch_type_p = distance.find('{*}frequency[@freq=\"'+str(frequency)+'\"]').find('{*}ch_type[@type="P"]')
        if ch_type_p is not None:
            # Todo: Should SaCategory be NaN or 0.0 if there is no record of <ch_type type="P"> in xml file?
            # Todo (cont.): As per now: 0.0. I think this is right, because the xml file never report the zero-values.
            for sa_by_acocat in ch_type_p.findall('{*}sa_by_acocat'):
                for sa in sa_by_acocat.findall('{*}sa'):
                    cat = int(sa_by_acocat.attrib['acocat'])
                    ch = int(sa.attrib['ch'])
                    tmp[cat][ch] = sa.text
        # Convert tmp from dict to list (to avoid potential sorting issues)
        tmp = [[tmp[cat][ch] for ch in range_pel_ch] for cat in category]
        sa_values.append(tmp)
    sa_values = np.array(sa_values, dtype='float32')

    # We check that pelagic channel thickness is constant. If not, the code breaks and must be written differently.
    assert np.max(pel_ch_thickness) == np.min(pel_ch_thickness)
    channel_depth_lower = range_pel_ch * np.max(pel_ch_thickness)
    channel_depth_upper = channel_depth_lower - np.max(pel_ch_thickness)
    # Todo: Need to add transducer depth to get the correct channel depths?

    coords = dict(
        SaCategory=('SaCategory', category),
        Time=('Time', start_time),
        stop_time=('Time', stop_time),
        ChannelDepthUpper=('ChannelDepthUpper', channel_depth_upper),
        ChannelDepthLower=('ChannelDepthUpper', channel_depth_lower),
        Distance=('Time', log_start),
        integrator_dist=('Time', integrator_dist),
        pel_ch_thickness=('Time', pel_ch_thickness),
        include_estimate=('Time', include_estimate),
        Latitude=('Time', lat_start),
        Latitude2=('Time', lat_stop),
        Longitude=('Time', lon_start),
        Longitude2=('Time', lon_stop),
        frequency=freq
    )

    data_vars = dict(
        value=(('Time', 'SaCategory', 'ChannelDepthUpper'), sa_values),
        threshold=('Time', threshold),
        num_pel_ch=('Time', num_pel_ch),
        min_bot_depth=('Time', min_bot_depth),
        max_bot_depth=('Time', max_bot_depth),
        upper_interpret_depth=('Time', upper_interpret_depth),
        lower_interpret_depth=('Time', lower_interpret_depth),
        upper_integrator_depth=('Time', upper_integrator_depth),
        lower_integrator_depth=('Time', lower_integrator_depth),
        quality=('Time', quality),
        bubble_corr=('Time', bubble_corr)
    )
    return xr.Dataset(data_vars=data_vars, coords=coords)


if __name__ == '__main__':

    # test data
    xmlfile = '/mnt/c/DATAscratch/crimac-scratch/2019/S2019842/ACOUSTIC/LSSS/REPORTS/echosounder_cruiseNumber_2019842_Vendla_2021-02-05T00.01.00.835Z.xml'
    zarrfile = 'S2018823_report_0.zarr'  # Naming convetion for files converted from standard estimates
    frequency = 38000
    ds = report_xml2xarray(xmlfile, frequency=frequency)
    # For comparisons
    reportfile = '/mnt/c/DATAscratch/crimac-scratch/2019/S2019847_0511/ACOUSTIC/REPORTS/S2019847_0511_report_1_start.zarr'
    ds0 = xr.open_zarr(reportfile)

    # Do the comparisons
    print('Keys from converted xml file:')
    print(list(ds.keys()))
    print('Keys from Integrator:')
    print(list(ds0.keys()))
    print('\n')
    print('Coordinates from converted xml file:')
    print(list(ds.coords))
    print('Coordinates from Integrator:')
    print(list(ds0.coords))
   
    plt.figure()
    plt.subplot(2, 1, 1)
    plt.title(' ')
    plt.imshow(10 * np.log10(ds0.sel(SaCategory=27)['value'].T + 10e-20))
    plt.axis('auto')

    plt.subplot(2, 1, 2)
    plt.title(' ')
    plt.imshow(10 * np.log10(ds.sel(SaCategory=27)['value'].T + 10e-20))
    plt.axis('auto')
    plt.show()
