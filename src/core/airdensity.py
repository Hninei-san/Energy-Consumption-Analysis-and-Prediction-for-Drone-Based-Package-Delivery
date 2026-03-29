import warnings
# Silence the Axes3D import warning before importing matplotlib
warnings.filterwarnings("ignore", message="Unable to import Axes3D")

import pandas as pd
import datetime
import src.utils.METAR_KAGC as METAR_KAGC
import numpy as np
import os
   

def CreateCsv(df):
    '''
    this function creates a csv file with the number of the flight and the estimated air density.
    This process takes a few seconds perf flight, so it is better to do it only once and then use the results from the csv
    for one flight use the function AirDensity
    :param df: [DataFrame] data frame with all the flights 'FlightSheet.csv'
    :param mainpath: [str] where the csv file will be created
    :return: csv file with the number of the flight and the estimated air density
    '''
    df['date'] = df['date'] + ' '
    df['time_day'] = df['time_day'] + ':00.0'
    df['date'] = df['date'].astype(str)
    df['time_day']= df['time_day'].astype(str)
    df['time'] = df[['date','time_day']].apply(lambda x: ''.join(x), axis=1)

    print('colecting airdensity values')

    rho = []
    wind = []
    flights = list(set(df.flight))
    for flight in flights:
        print(flight)
        sub_df = df[df.flight == flight]
        date_time_obj = datetime.datetime.strptime(sub_df.time.max(),'%Y-%m-%d %H:%M:%S.%f')
        rho_flight = METAR_KAGC.calculate_density(date_time_obj)
        print(rho_flight)
        wind_max = METAR_KAGC.calculate_wind_speed(date_time_obj)

        rho.append(rho_flight)
        wind.append(wind_max)
        print("flight: %d, rho: %f kg/m3, wind: %.2f knots"%(flight, rho_flight, wind_max))
    print(rho)

    airdensity = pd.DataFrame({"flight":flights, 'rho':rho, "wind":wind})
    airdensity.to_csv("results/tables/airdensity.csv")



def AirDensity(df_log, flight=None):
    '''
    This function returns the air density for a particular flight
    :param df_log: [DataFrame] data frame with all the flights
    :param flight: [int] flight number (optional)
    :return: [float] air density in [kg/m^3]
    '''
    df = df_log.copy()
    if flight is not None:
        df = df[df.flight == flight]
    
    # Ensure date and time are clean and combined correctly
    df['full_time'] = df['date'].astype(str) + ' ' + df['time_day'].astype(str)
    
    # Use the first timestamp found
    try:
        sample_time = df['full_time'].iloc[0]
        # Handle formats like '2019-04-07 10:13' or '2019-04-07 10:13:00'
        if len(sample_time) > 16:
            date_time_obj = datetime.datetime.strptime(sample_time, '%Y-%m-%d %H:%M:%S')
        else:
            date_time_obj = datetime.datetime.strptime(sample_time, '%Y-%m-%d %H:%M')
    except Exception as e:
        print(f"Error parsing date/time: {e}. Trying generic parser.")
        # Fallback to a simpler format or just take it as is if it matches calculate_density's expectations
        date_time_obj = pd.to_datetime(df['full_time'].iloc[0]).to_pydatetime()

    rho = METAR_KAGC.calculate_density(date_time_obj)
    return rho

def AirDensityForIndex(df_log):
    '''
    This function returns the air density for a list of flights
    :param df: [DataFrame] data frame with all the flights 'FlightSheet.csv'
    :param flight: [int] flight number
    :return: [series] air density in [kg/m^3]
    '''
    df = df_log.copy()
    df['date_[yyyy-mm-dd]'] = df['date_[yyyy-mm-dd]'] + ' '
    df['time_[hh:mm]'] = df['time_[hh:mm]'] + ':00.0'
    df['date_[yyyy-mm-dd]'] = df['date_[yyyy-mm-dd]'].astype(str)
    df['time_[hh:mm]']= df['time_[hh:mm]'].astype(str)
    df['time'] = df[['date_[yyyy-mm-dd]','time_[hh:mm]']].apply(lambda x: ''.join(x), axis=1)

    rho = []
    print('colecting airdensity values')
    for flight in list(df.index.values):
        print('flight:', flight)
        date_time_obj = datetime.datetime.strptime(df['time'][flight],'%Y-%m-%d %H:%M:%S.%f')
        rho.append(METAR_KAGC.calculate_density(date_time_obj))
    return rho

def main():
    data = pd.read_csv("dataset/flights.csv")
    CreateCsv(data)


if __name__ == "__main__":
    main()