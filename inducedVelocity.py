import warnings
# Silence the Axes3D import warning before importing matplotlib
warnings.filterwarnings("ignore", message="Unable to import Axes3D")

import numpy as np
import pandas as pd
import os
import progressbar
import matplotlib.pyplot as plt
import time


def vi(row):
    T = row['T']
    A = row['A']
    rho = row['density']
    Vbi = row['Vbi']
    Vbj = row['Vbj']
    Vbk = row['Vbk']
    v_i = 0.00001
    w = - v_i + T / (2 * rho * A * np.sqrt(Vbi ** 2 + Vbj ** 2 + (Vbk + v_i) ** 2))
    step = 5
    while abs(w) > 0.001:
        while w > 0:
            v_i += step
            w = - v_i + T / (2 * rho * A * np.sqrt(Vbi ** 2 + Vbj ** 2 + (Vbk + v_i) ** 2))
        while w < 0:
            step = step/2
            v_i -= 2*step
            w = - v_i + T / (2 * rho * A * np.sqrt(Vbi ** 2 + Vbj ** 2 + (Vbk + v_i) ** 2))
    return v_i


def CalculateVi(df, rho, A):
    start_time = time.time()
    
    # Ensure columns exist or are passed correctly
    # The original vi function expects 'T', 'A', 'density', 'Vbi', 'Vbj', 'Vbk' in the row
    # If they are not in the df, we should add them or adjust vi
    
    print('Calculating induced velocity...')
    
    total = len(df)
    bar = progressbar.ProgressBar(max_value=total, widgets=[
        progressbar.Bar('*', '[', ']'), ' ', progressbar.Percentage()
    ])
    
    v_i_list = []
    bar.start()
    for index, row in df.iterrows():
        # Add necessary parameters to row if they are not there
        row_dict = row.to_dict()
        if 'A' not in row_dict: row_dict['A'] = A
        if 'density' not in row_dict: row_dict['density'] = rho
        
        v_i_list.append(vi(row_dict))
        bar.update(len(v_i_list))
    bar.finish()
    
    df['v_i'] = v_i_list
    print("--- %.2f seconds ---" % float(time.time() - start_time))

    return df['v_i']






