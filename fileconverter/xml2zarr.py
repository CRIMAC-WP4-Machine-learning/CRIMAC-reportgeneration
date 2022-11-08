import xarray as xr
import numpy as np
import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt


def report_xml2xarray(path_xml):
    '''
    Convert LSSS report file from xml to xarray
    :param path_xml: (str) path to xml file
    :return: (xarray.Dataset) xarray dataset
    '''

    def get_distance_values(root, variable: str, is_attrib: bool, dtype: str):
        if is_attrib:
            x = [distance.attrib[variable] for distance in root.find('distance_list').findall('distance')]
        else:
            x = [distance.find(variable).text for distance in root.find('distance_list').findall('distance')]
        return np.array(x, dtype=dtype)

    def get_distance_frequency_values(root, variable: str, is_attrib: bool, dtype: str):
        if is_attrib:
            x = [distance.find('frequency').attrib[variable] for distance in root.find('distance_list').findall('distance')]
        else:
            x = [distance.find('frequency').find(variable).text for distance in root.find('distance_list').findall('distance')]
        return np.array(x, dtype=dtype)

    tree = ET.parse(path_xml)
    root = tree.getroot()

    # Get list of the acoustic categories
    category = sorted([int(acocat.attrib['acocat']) for acocat in root.find('acocat_list').findall('acocat')])

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
    # Assuming only one freq and transceiver per distance
    assert all([len(distance.findall('frequency')) == 1 for distance in root.find('distance_list').findall('distance')])
    freq = get_distance_frequency_values(root, 'freq', True, 'int')
    transceiver = get_distance_frequency_values(root, 'transceiver', True, 'int')
    threshold = get_distance_frequency_values(root, 'threshold', False, 'float32')
    num_pel_ch = get_distance_frequency_values(root, 'num_pel_ch', False, 'int')
    min_bot_depth = get_distance_frequency_values(root, 'min_bot_depth', False, 'float32')
    max_bot_depth = get_distance_frequency_values(root, 'max_bot_depth', False, 'float32')
    upper_interpret_depth = get_distance_frequency_values(root, 'upper_interpret_depth', False, 'float32')
    lower_interpret_depth = get_distance_frequency_values(root, 'lower_interpret_depth', False, 'float32')
    upper_integrator_depth = get_distance_frequency_values(root, 'upper_integrator_depth', False, 'float32')
    lower_integrator_depth = get_distance_frequency_values(root, 'lower_integrator_depth', False, 'float32')
    quality = get_distance_frequency_values(root, 'quality', False, 'int')
    bubble_corr = get_distance_frequency_values(root, 'bubble_corr', False, 'float32')

    # Get the full range of existing pelagic channels
    all_pel_ch = list()
    for distance in root.find('distance_list').findall('distance'):
        for ch_type in distance.find('frequency').findall('ch_type'):
            if ch_type.attrib['type'] != 'P':
                continue
            for sa_by_acocat in ch_type.findall('sa_by_acocat'):
                for sa in sa_by_acocat.findall('sa'):
                    all_pel_ch.append(sa.attrib['ch'])
    all_pel_ch = [int(ch) for ch in set(all_pel_ch)]
    min_pel_ch = np.min(all_pel_ch)
    max_pel_ch = np.max(all_pel_ch)
    range_pel_ch = np.arange(min_pel_ch, max_pel_ch + 1)

    # Get the sa values per (distance, category, pelagic channel) - only use P (peleagic) values, discard B (bottom) values.
    sa_values = []
    for distance in root.find('distance_list').findall('distance'):
        tmp = {cat: {ch: 0.0 for ch in range_pel_ch} for cat in category}
        for ch_type in distance.find('frequency').findall('ch_type'):
            if ch_type.attrib['type'] != 'P':
                continue
            for sa_by_acocat in ch_type.findall('sa_by_acocat'):
                for sa in sa_by_acocat.findall('sa'):
                    cat = int(sa_by_acocat.attrib['acocat'])
                    ch = int(sa.attrib['ch'])
                    tmp[cat][ch] = sa.text
        # Convert tmp from dict to list (to avoid potential sorting issues)
        tmp = [[tmp[cat][ch] for ch in range_pel_ch] for cat in category]
        sa_values.append(tmp)
    sa_values = np.array(sa_values, dtype='float32')

    assert np.max(pel_ch_thickness) == np.min(pel_ch_thickness)
    channel_depth_upper = range_pel_ch * np.max(pel_ch_thickness)
    channel_depth_lower = channel_depth_upper + np.max(pel_ch_thickness)

    coords = dict(
        category=('category', category),
        start_time=('start_time', start_time),
        stop_time=('start_time', stop_time),
        channel_depth_upper=('channel_depth_upper', channel_depth_upper),
        channel_depth_lower=('channel_depth_upper', channel_depth_lower),
        log_start=('start_time', log_start),
        integrator_dist=('start_time', integrator_dist),
        pel_ch_thickness=('start_time', pel_ch_thickness),
        include_estimate=('start_time', include_estimate),
        lat_start=('start_time', lat_start),
        lat_stop=('start_time', lat_stop),
        lon_start=('start_time', lon_start),
        lon_stop=('start_time', lon_stop),
        freq=('start_time', freq),
        transceiver=('start_time', transceiver),
    )

    data_vars = dict(
        sa_values=(('start_time', 'category', 'channel_depth_upper'), sa_values),
        threshold=('start_time', threshold),
        num_pel_ch=('start_time', num_pel_ch),
        min_bot_depth=('start_time', min_bot_depth),
        max_bot_depth=('start_time', max_bot_depth),
        upper_interpret_depth=('start_time', upper_interpret_depth),
        lower_interpret_depth=('start_time', lower_interpret_depth),
        upper_integrator_depth=('start_time', upper_integrator_depth),
        lower_integrator_depth=('start_time', lower_integrator_depth),
        quality=('start_time', quality),
        bubble_corr=('start_time', bubble_corr)
    )

    return xr.Dataset(data_vars=data_vars, coords=coords)


if __name__ == '__main__':

    # test data
    rawdir = '/mnt/c/DATAscratch/crimac-scratch/2018/S2018823/ACOUSTIC/REPORTS/'
    xmlfile = 'echosounder_cruiseNumber_2018823_Eros_2021-02-05T00.06.32.305Z.xml'  # Official data
    zarrfile = 'S2018823_report_0.zarr'  # Naming convetion for files converted from standard estimates

    path_xml = '' # rawdir + xmlfile ?
    ds = report_xml2xarray(path_xml)
    xr.set_options(display_max_rows=50)
    print(ds)