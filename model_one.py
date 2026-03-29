import warnings
# Silence the Axes3D import warning before importing anything that might use matplotlib
warnings.filterwarnings("ignore", message="Unable to import Axes3D")

import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import seaborn as sns
import FindingRegimeFilter
import scipy.integrate
import inflightcomponents as inflight
import matplotlib.ticker as mtick
import LinearRegression as lr

plt.rcParams["font.family"] = "Helvetica"
plt.rc('font',**{'family':'sans-serif','sans-serif':['Helvetica']})

def avg_power_summary(df):
    takeOff, landing, cruise, wholeflight = FindingRegimeFilter.FindRegime(df)
    time_cruise = cruise['time'].max() - cruise['time'].min()
    time_takeoff = takeOff['time'].max() - takeOff['time'].min()
    time_landing = landing['time'].max() - landing['time'].min()
    time_whole = wholeflight['time'].max() - wholeflight['time'].min()

    # Ensure Power column exists
    for regime in [cruise, takeOff, landing, wholeflight]:
        if 'Power' not in regime.columns:
            regime['Power'] = regime['battery_voltage'] * regime['battery_current']

    e_measured_cruise = scipy.integrate.simpson(cruise['Power'], x=cruise["time"]) / 3600
    e_measured_takeoff = scipy.integrate.simpson(takeOff['Power'], x=takeOff["time"]) / 3600
    e_measured_landing = scipy.integrate.simpson(landing['Power'], x=landing["time"]) / 3600
    e_measured_whole = scipy.integrate.simpson(wholeflight['Power'], x=wholeflight["time"]) / 3600
    return e_measured_takeoff, e_measured_cruise, e_measured_landing, e_measured_whole,\
           time_takeoff, time_cruise, time_landing, time_whole


def create_energy_summary(data):
    '''
    :param data: data frame with all flights
    :return: creates a csv with an energy summary
    '''

    energy_summary_list = []
    index = list(set(data['flight']))
    i = 1
    for flight in index:
        print('flight: %d progress = %d%%'%(flight, i*100/len(index)) , end='\r')
        df = data[data['flight'] == flight].copy()
        
        # Columns renaming for consistency
        if 'payload' not in df.columns and 'payload_[g]' in df.columns:
            df.rename(columns={'payload_[g]': 'payload'}, inplace=True)
            
        payload = df.payload.min()
        speed = df.speed.min()
        altitude = df.altitude.min()
        Pi_hover = inflight.hoverInducedPower(df)
        e_tk, e_cr, e_ld, e_wl, t_tk, t_cr, t_ld, t_wl = avg_power_summary(df)
        energy_flight = pd.DataFrame({'flight': [flight], 'payload': [payload], "altitude": [altitude],
                                      'speed': [speed], 'Energy_takeoff': e_tk, 'Energy_cruise': e_cr,
                                      'Energy_landing': e_ld, 'Energy_total': e_wl, 'time_takeoff': t_tk,
                                      'time_cruise':  t_cr, 'time_landing': t_ld, 'time_total': t_wl,
                                      'Power_takeoff': e_tk * 3600 / t_tk, 'Power_cruise': e_cr * 3600 / t_cr,
                                      'Power_landing': e_ld * 3600 / t_ld, "avg_power": e_wl*3600/t_wl,
                                      "Pi_hover": Pi_hover})
        energy_summary_list.append(energy_flight)
        i += 1
    
    if energy_summary_list:
        energy_summary = pd.concat(energy_summary_list, ignore_index=True)
        energy_summary.to_csv('energy_summary_model2.csv', index=False)
        print("\nEnergy Summary Created as energy_summary_model2.csv")

def test(df, coeff):
    b1_tk = coeff.loc['takeoff', 'b1']
    b0_tk = coeff.loc['takeoff', 'b0']
    b1_cr = coeff.loc['cruise', 'b1']
    b0_cr = coeff.loc['cruise', 'b0']
    b1_ld = coeff.loc['landing', 'b1']
    b0_ld = coeff.loc['landing', 'b0']
    Pi = df.Pi_hover
    t_tk = df.time_takeoff
    t_cr = df.time_cruise
    t_ld = df.time_landing

    return (t_tk*(b1_tk*Pi+b0_tk) + t_cr*(b1_cr*Pi+b0_cr) + t_ld*(b1_ld*Pi+b0_ld))/3600

def ARE(df):
    return np.fabs(df.Energy_total - df.energy_model)/df.Energy_total

def main():
    dataset_path = os.path.join(os.getcwd(), 'dataset', 'flights.csv')
    if not os.path.exists(dataset_path):
         dataset_path = 'flights.csv'
         
    data = pd.read_csv(dataset_path, low_memory=False)
    # Filter as per user logic
    if 'route' in data.columns:
        data = data[((data.route == 'R1')|(data.route == 'R2')|(data.route == 'R3')|(data.route == 'R4')|(data.route == 'R5'))&(
            data.payload < 750)]
            
    index = list(set(data['flight']))
    data['Power'] = data['battery_current']*data['battery_voltage']
    
    try:
        summary = pd.read_csv('energy_summary_model2.csv')
    except:
        create_energy_summary(data)
        summary = pd.read_csv('energy_summary_model2.csv')
        
    # Check if poll.csv exists, otherwise create a random one or use index
    if os.path.exists('poll.csv'):
        poll = pd.read_csv('poll.csv')
    else:
        poll = pd.DataFrame({"flight":np.random.choice(index, size=min(len(index), 120), replace=False)})
        poll.to_csv('poll.csv', index=False)

    summary.payload = summary.payload.astype(int)
    summary_poll = summary[summary.flight.isin(poll.flight)].copy()

    coeff = lr.linear_regression(summary_poll)
    test_sample = summary[~summary.flight.isin(poll.flight)].copy()
    test_sample['energy_model'] = test(test_sample, coeff)
    test_sample["ARE"] = ARE(test_sample)
    test_sample.to_csv('Test_model_1.csv', index=False)
    print("ARE: Average = %.4f; Median = %.4f"%(test_sample.ARE.mean(), test_sample.ARE.median()))

if __name__ == "__main__":
    main()