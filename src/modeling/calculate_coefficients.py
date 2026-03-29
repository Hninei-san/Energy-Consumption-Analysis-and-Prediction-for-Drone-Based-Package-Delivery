# This module calls all other modules.

import pandas as pd
import LinearRegression as lr

def main():
    summary = pd.read_csv('/home/eisan/energy_consumption/energy_summary_model1.csv')
    pool = pd.read_csv('/home/eisan/energy_consumption/dataset/poll.csv')
    pool.columns = pool.columns.str.replace(r'^#\s*', '', regex=True)  # strip leading '# ' from header
    summary_pool = summary[summary.flight.isin(pool.flight)].copy()
    coeff = lr.linear_regression(summary_pool)
    coeff.to_csv('/home/eisan/energy_consumption/coefficients_model1.csv')


if __name__ == '__main__':
    main()
