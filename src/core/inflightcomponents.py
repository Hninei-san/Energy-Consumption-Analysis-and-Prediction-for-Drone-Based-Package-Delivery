import warnings
# Silence the Axes3D import warning before importing matplotlib
warnings.filterwarnings("ignore", message="Unable to import Axes3D")

import pandas as pd
import numpy as np
import src.core.power_functions as pwf
import os
import matplotlib.pyplot as plt
#import fixColumn as fix
import src.core.airdensity as airdensity
import src.processing.FindingRegimeFilter as FindingRegimeFilter
import src.core.inducedVelocity as inducedVelocity
import scipy.integrate
import time
from geopy.distance import geodesic

def hoverInducedPower(df):
    gravity = 9.81
    R = 0.15
    A = 4 * np.pi * R ** 2
    payload = df.payload.min()
    m = payload / 1000 + 3.08 + 0.635
    rho = airdensity.AirDensity(df)
    return ((m*gravity)**(3/2))/np.sqrt(2*rho*A)


def energyMeasured(df):
    df['Power']= df['battery_current']*df['battery_voltage']
    takeOff, landing, cruise, wholeflight = FindingRegime.FindRegime(df)
    df_cruise = cruise
    df_takeOff = takeOff
    df_landing = landing
    time_cruise = df_cruise['time'].max() - df_cruise['time'].min()
    time_takeoff = df_takeOff['time'].max() - df_takeOff['time'].min()
    time_landing = df_landing['time'].max() - df_landing['time'].min()

    energy_measured_cruise = scipy.integrate.simpson(df_cruise['Power'], x=df_cruise["time"]) / 3600
    energy_measured_takeoff = scipy.integrate.simpson(df_takeOff['Power'], x=df_takeOff["time"]) / 3600
    energy_measured_landing = scipy.integrate.simpson(df_landing['Power'], x=df_landing["time"]) / 3600

    energy_measured_total = energy_measured_takeoff + energy_measured_cruise + energy_measured_landing

    return time_takeoff, time_cruise, time_landing, energy_measured_total


def total_distance(df):
    distance = 0
    lat_N = df['x'][df.index.values[0]]
    lon_W = df['y'][df.index.values[0]]
    coord1 = (lat_N, lon_W)
    for record in df.index.values:
        coord2 = (df['x'][record], df['y'][record])
        distance += geodesic(coord1,coord2).km
        coord1 = coord2
    return distance

def energy_measured_regime(df):
    df['Power'] = df['battery_current'] * df['battery_voltage']
    takeOff, landing, cruise, wholeflight = FindingRegimeFilter.FindRegime(df)
    df_cruise = cruise
    df_takeOff = takeOff
    df_landing = landing
    t_cruise = df_cruise['time'].max() - df_cruise['time'].min()
    t_takeoff = df_takeOff['time'].max() - df_takeOff['time'].min()
    t_landing = df_landing['time'].max() - df_landing['time'].min()
    distance = total_distance(df_cruise)

    altitude_takeoff = df_takeOff['z'].max() - df_takeOff['z'].min()
    altitude_landing = df_landing['z'].max() - df_landing['z'].min()
    e_measured_cruise = scipy.integrate.simpson(df_cruise['Power'], x=df_cruise["time"]) / 3600
    e_measured_takeoff = scipy.integrate.simpson(df_takeOff['Power'], x=df_takeOff["time"]) / 3600
    e_measured_landing = scipy.integrate.simpson(df_landing['Power'], x=df_landing["time"]) / 3600

    energy_measured_total = e_measured_takeoff + e_measured_cruise + e_measured_landing

    return t_takeoff, t_cruise, t_landing, e_measured_takeoff, e_measured_cruise, e_measured_landing, distance, \
           altitude_takeoff, altitude_landing




def generateInflightComponents(df_log,flight):
    DataDirectory = os.path.join(os.getcwd(), 'dataset')

    gravity = 9.81
    R = 0.15
    A = 4 * np.pi * R ** 2
    payload = df_log['payload_[g]'][flight]
    m = payload / 1000 + 3.08 + 0.635
    rho = airdensity.AirDensity(df_log, flight)
    start_time = time.time()
    print("flight :", flight)

    flightfolder = DataDirectory + "/" + str(flight)
    os.chdir(flightfolder)
    df = pd.read_csv('combined.csv')

    takeOff, landing, cruise, wholeflight = FindingRegimeFilter.FindRegime(df)
    df = wholeflight
    df['phi'], df['theta'], df['psi'] = pwf.quaternion_to_euler(df)
    df['Power'] = df['battery_voltage'] * df['battery_current']
    df['T'] = pwf.Thrust(m, gravity, df['phi'], df['theta'])
    df['Vbi'], df['Vbj'], df['Vbk'] = pwf.VairBody(df)
    df['v_i'] = inducedVelocity.CalculateVi(df, rho, A)
    df['alpha'] = 90 - df['theta']
    df['beta'] = df['phi']
    df['Pi_Estimated'] = pwf.InducedPower(df)

    df_copy = df.copy()
    df_copy['phi'], df_copy['theta'] = df['phi'] * 0, df['theta'] * 0
    df_copy['T'] = pwf.Thrust(m, gravity, df_copy['phi'], df_copy['theta'])
    df_copy['Vbi'], df_copy['Vbj'], df_copy['Vbk'] = df['Vbi'] * 0, df['Vbj'] * 0, df['Vbk'] * 0
    df_copy['alpha'] = df_copy['theta'] * 0 + np.pi / 2
    df_copy['beta'] = df['beta'] * 0
    df_copy['v_i'] = inducedVelocity.CalculateVi(df_copy, rho, A)
    df['Pi_hover'] = pwf.InducedPower(df_copy)

    os.chdir(mainpath)
    df.to_csv('results/tables/%d.csv' % (flight))
    print("--- flight %d: %.2f seconds ---" % (flight, float(time.time() - start_time)))
    return(df)


def main():
    '''
    This script adds the euler angles, power, air speed velocities (no wind condition), thrust, alpha and beta angles,
    induced velocity, induced power and theoretical induced hover power.
    :return: a dataframe for each flight with all the components described above.
    '''
    mainpath = os.getcwd()
    # Path to the dataset
    dataset_path = os.path.join(mainpath, 'dataset', 'flights.csv')
    
    # Load data - removing fix.FixColumns call
    df_log = pd.read_csv(dataset_path, low_memory=False)

    # Use actual column names from flights.csv
    # The dataset has 'flight', 'payload', 'speed', 'altitude'
    
    gravity = 9.81
    R = 0.15
    A = 4 * np.pi * R ** 2
    
    # Process only flight 201 for demonstration/testing as before
    processed_flights = [201] # or list(set(df_log.flight))
    
    for flight in processed_flights:
        # Filter for the specific flight
        df_flight_row = df_log[df_log.flight == flight].iloc[0]
        
        payload = df_flight_row['payload']
        m = payload/1000 + 3.08 + 0.635
        speed = df_flight_row['speed']
        altitude = df_flight_row['altitude']
        
        print("Processing flight:", flight)
        
        # Calculate air density for this flight
        rho = airdensity.AirDensity(df_log, flight)
        start_time = time.time()

        # In this project, 'combined.csv' seems to be the flight data, but for this demo 
        # we'll use the same df_log filtered for the flight if it contains the telemetry.
        # However, generateInflightComponents logic suggests a separate file.
        # Since we only have flights.csv, we treat it as the telemetry source.
        
        df = df_log[df_log.flight == flight].copy()

        takeOff, landing, cruise, wholeflight = FindingRegimeFilter.FindRegime(df)
        df = wholeflight
        df['phi'], df['theta'], df['psi'] = pwf.quaternion_to_euler(df)
        df['Power'] = df['battery_voltage'] * df['battery_current']
        df['T'] = pwf.Thrust(m, gravity, df['phi'], df['theta'])
        df['Vbi'], df['Vbj'], df['Vbk'] = pwf.VairBody(df)
        df['v_i'] = inducedVelocity.CalculateVi(df, rho, A)
        df['alpha'] = 90 - df['theta']
        df['beta'] = df['phi']
        df['Pi_Estimated'] = pwf.InducedPower(df)

        df_copy = df.copy()
        df_copy['phi'], df_copy['theta'] = df['phi']*0, df['theta']*0
        df_copy['T'] = pwf.Thrust(m, gravity, df_copy['phi'], df_copy['theta'])
        df_copy['Vbi'], df_copy['Vbj'], df_copy['Vbk'] = df['Vbi']*0, df['Vbj']*0, df['Vbk']*0
        df_copy['alpha'] = df_copy['theta'] * 0 + np.pi / 2
        df_copy['beta'] = df['beta']*0
        df_copy['v_i'] = inducedVelocity.CalculateVi(df_copy, rho, A)
        df['Pi_hover'] = pwf.InducedPower(df_copy)

        # Output to current directory
        df.to_csv('results/tables/%d_inflight.csv'%(flight))
        print("--- flight %d: %.2f seconds ---" % (flight, float(time.time() - start_time)))


if __name__ == '__main__':
    main()