import pandas as pd
import numpy as np
from Project_Time_series_Analysis.utils.tools import * # function own

import plotnine as p9 # ggplot
import matplotlib.pyplot as plt

from statsmodels.tsa.arima_model import ARIMA
import statsmodels.api as sm

import sqlalchemy as db

# variables y funciones globales
plt.rcParams.update({'figure.figsize':(20,10), 'figure.dpi':100})
plt.style.use('ggplot')
color_line = '#D302AA'

# data --
data_btc = connection_db_sql(database = 'crypto_series',
                                consult_sql_server = "SELECT * FROM data_crypto WHERE symbol = 'BTC-USD'")

data_btc_filter = data_btc.loc['2021']

# test Dickey Fuller --
test_dickey_fuller(data_btc_filter, 'Close')

# test, but with the diff --
data_btc_filter['diff1'] =  data_btc_filter.Close.diff()
data_btc_filter['diff2'] = data_btc_filter['diff1'].diff()

# diff first
test_dickey_fuller(data_btc_filter, 'diff1')

# diff second
test_dickey_fuller(data_btc_filter, 'diff2')

# prove the best model
the_best_models(2,2,3, data_btc_filter['Close'])

# the best
model_1 = ARIMA(data_btc_filter.Close.values, order=(2, 2, 3))
model_1_fit1 = model_1.fit(disp=0)
print(model_1_fit1.summary())

# eval test
sm.stats.acorr_ljungbox(model_1_fit1.resid, lags=[10], return_df=True)

# residuals
residuales = pd.DataFrame(model_1_fit1.resid)
fig, ax = plt.subplots(1,2)
residuales.plot(title = 'residuales', ax = ax[0], color =  color_line, lw = .9)
residuales.plot(kind = 'kde', title = 'Densidad', ax = ax[1], color = color_line, lw =.9)
plt.show()