# This module reads the csv and calculates power for all flights

import pandas as pd
import os


def read():
    '''
    This function reads the csv with all flights and calculates power as the multiplication of current and voltage.
    :return: dataFrame with all flights
    '''
    print('Reading data')
    data = pd.read_csv('/home/eisan/energy_consumption/dataset/flights.csv', low_memory=False)
    data = data[((data.route == 'R1')|(data.route == 'R2')|(data.route == 'R3')|(data.route == 'R4')|(data.route == 'R5'))&(
        data.payload < 750)]
    index = list(set(data['flight']))
    data['Power'] = data['battery_current']*data['battery_voltage']
    return data
