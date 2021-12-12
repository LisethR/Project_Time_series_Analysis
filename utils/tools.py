import yfinance as yf # data yahoo finance
import pandas as pd
import time
import requests
import pyodbc
import sqlalchemy as db
import numpy as np
from statsmodels.tsa.stattools import adfuller
from datetime import datetime, timedelta
import matplotlib.pyplot as plt # tipo grafica que utilizaremos para el estudio de la serie
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf # correlograma
import plotnine as p9 # grafico tipo ggplot
from statsmodels.tsa.arima_model import ARIMA 

# current of the cryptocurrency
def get_data_cryptocurrency(date_init , date_end ):
    '''
    Permite consultar en yahoo finance todas las cripto monedas disponibles
    es de contemplar que para la consulta se requiere y se obtiene lo siguiente:

    Vars:
    ---- 
    las variables de entra son:

    - date_init: en la fecha de inicio de consulta

    - date_end: fecha final de consulta

    result:
    ------
    se obtiene un df con la informacion de cada cripto moneda desde la 
    fecha date_init hasta la fecha date_end

    nota:
    ---- 
    es de destacar que cuando se quiere el periodo completo se coloca la funcion 
    de la se la siguiente manera get_data_cryptocurrency('','')

    '''

    # symbols
    crypto = "https://finance.yahoo.com/cryptocurrencies"
    symbols_charact = pd.read_html(requests.get(crypto).text)[0]
    only_symbols = symbols_charact.Symbol.to_list()

    serie_crypto_hist = pd.DataFrame()
    # data
    for symbol_i in only_symbols:
        
        if date_init == '' and date_end == '':
            # get historical market data
            hist = yf.Ticker(symbol_i).history(period="max")
            hist.reset_index(inplace = True)
            hist['symbol'] = symbol_i


        else:
            # get historical market data
            hist = yf.Ticker(symbol_i).history(start = date_init, end= date_end)
            hist.reset_index(inplace = True)
            hist['symbol'] = symbol_i

        # append data
        serie_crypto_hist = serie_crypto_hist.append(hist, ignore_index = True)
        time.sleep(1)
        print(f'import ready of symbol: {symbol_i}')

    # return dataframe with series of crypto
    return serie_crypto_hist.rename(columns={'Close':'close_', 'Open':'open_', 'High':'high', 'Low':'low', 'Stock Splits':'stock_split'})

# data consulting in sql server
def connection_db_sql(database: str, consult_sql_server: str):
    '''
    Permite consultar la informacion que se tiene sobre la base de datos
    SQL Server, cual depende de la siguiente informacion:

    Vars:
    ---- 
    las variables de entra son:

    - database: es la base de datos particular, la cual guarda las 
        tablas de interes en formato str.

    - consult_sql_server: los caracateristicas y formato 
        de la consulta en SQL Server.

    result:
    ------
    se obtiene un df con la informacion de la consulta con las caracteristicas de interes

    nota:
    ---- 
    la consulta es exactamente igual a la consulta en SQL Server

    '''

    # connection
    server = 'USER' 

    cnxn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};'
                            'SERVER='+server+';DATABASE='+database+';'
                            'TRUSTED_CONNECTION=yes')

    # consultar data ----
    data_from_sqlserver = pd.read_sql_query(consult_sql_server, 
                                                cnxn,
                                                index_col = ['Date'])

    data_from_sqlserver.index = pd.to_datetime(data_from_sqlserver.index)
    data_from_sqlserver.sort_index(inplace= True)

    # return dataframe with consulting
    return data_from_sqlserver

# calculo del dickey fuller
def test_dickey_fuller(data: pd.DataFrame, var: str):
    result = adfuller(data[var].values)
    print(f'stats:{result[0]} \np-value: {result[1]}')

def graf_correlograma(data: pd.DataFrame, var: str, color_line_str: str, title_graf: str):
    # configuracion general de los corrleogramas
    plt.rcParams.update({'figure.figsize':(20,3), 'figure.dpi':100})

    # graficas de correlograma
    fig, axes = plt.subplots(1, 2, sharex=False)

    plt.suptitle('CORRELOGRAMAS')
    plt.figtext(0.5, 0.91, title_graf, ha='center', va='center')
    # make acf plot
    plot_acf(data[var], lags = 20, ax = axes[0], color = color_line_str, vlines_kwargs={"colors": color_line_str})
    # make pacf plot
    plot_pacf(data[var], lags = 20, ax = axes[1], color = color_line_str, vlines_kwargs={"colors": color_line_str})

    plt.show()

def graf_diff(data: pd.DataFrame, var: str, color_line_str: str, title_graf: str):
    data.dropna(inplace=True)

    print(   p9.ggplot(data.reset_index()) +
        p9.geom_line(p9.aes('Date', var), color = color_line_str) +
        p9.theme(figure_size=(20, 5)) +
        p9.labs(title = f'Symbol: {np.unique(data.symbol)}: '+ title_graf) +
        p9.xlab('Date (Daily)'))

def the_best_models(p_range,i_range,q_range, data):
    order_aic_bic = []

    # Loop over i values from 0-2
    for i in range(i_range+1):
        # Loop over p values from 0-2
        for p in range(p_range+1):
            # Loop over q values from 0-2
            for q in range(q_range+1):

                    try:
                        # create and fit ARMA(p,q) model
                        model = ARIMA(data, order=(p,i,q))
                        results = model.fit()

                        p_values = results.pvalues
                        p_values = p_values[1:] > .05
                        np.sum(p_values) == 0 

                        params_values = results.params
                        params_values = (params_values[1:] < -1) | (params_values[1:] > 1)
                        eval_params = (np.sum(params_values) == 0) & (np.sum(p_values) == 0) 

                        # Append order and results tuple
                        order_aic_bic.append((p, i, q, round(results.aic, 2), round(results.bic, 2), eval_params))

                    except:
                        order_aic_bic.append((p,i,q, None, None))

    # Construct DataFrame from order_aic_bic
    order_df = pd.DataFrame(order_aic_bic, 
                            columns=['p', 'i','q', 'AIC','BIC', 'eval_params'])

    # Print order_df in order of increasing AIC
    compliance_params = order_df['eval_params'] == True 
    possible_models = order_df[compliance_params].sort_values('AIC')

    p_q = (possible_models['p'] != 0) | (possible_models['q'] != 0)
    possible_models['model'] = 'ARIMA('+possible_models.p.astype(str)+','+possible_models.i.astype(str)+','+possible_models.q.astype(str)+')'
    return possible_models[p_q].set_index('model')[['AIC','BIC']]

def current_forecast(data):
    # connection
    server = 'USER' 
    database = 'BASE' 

    driver = 'ODBC Driver 17 for SQL Server'
    engine = db.create_engine('mssql+pyodbc://@'+server+'/'+database+'?driver='+driver)
    data.to_sql('data_forecast', engine, if_exists='append') # replace solo porque es nuevo, sino seria append