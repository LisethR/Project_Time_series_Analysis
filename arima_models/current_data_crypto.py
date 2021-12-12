from Project_Time_series_Analysis.utils.tools import * # function own
# current data crypto

'''
    Permite actualizar la data de las criptomonedas, dependiente de la las caracteristicas
    consultadas sobre la funcion get_data_cryptocurrency, en este caso es una funcion vacia:

    Vars:
    ---- 
    las variables de entra son:

    - end: es la fecha actual con un dia de rezago, esto porque la data obtenida por medio de la
    funcion get_data_cryptocurrency es la serie en dias.

    - start: se consulta la fecha mas reeciente de data que se tiene sobre la base de datos, que
    para este caso es solo sobre la tabla data_crypto.

    result:
    ------
    se obtiene un df con la informacion de las cryptomonedas, la cual se sube a la base datos sobre 
    data_crypto

'''

end = pd.to_datetime(datetime.now() - timedelta(days = 1)).\
strftime("%Y-%m-%d")

# fecha de inicio
start = connection_db_sql('crypto_series',
                    "SELECT TOP 1 Date FROM data_crypto ORDER BY Date desc")

start = pd.to_datetime(start.reset_index().iloc[0,0]+ timedelta(days = 1)).strftime("%Y-%m-%d")

# data mas actual de las cripto monedas
data_current = get_data_cryptocurrency(start, end)
data_current.set_index('Date',inplace=True)
data_current.reset_index(inplace=True)
data_current['Date'] = pd.to_datetime(data_current['Date'])
data_current['Date'] = data_current['Date'].dt.strftime("%Y-%m-%d")

server = 'USER' 
database = 'BASE' 

cnxn = pyodbc.connect('DRIVER={SQL Server};SERVER='+server+';DATABASE='+database)
cursor = cnxn.cursor()

for index,row in data_current.iterrows():
    cursor.execute('INSERT INTO dbo.data_crypto([Date], \
                    [Open], [High], [Low], [Close], [Volume], \
                    [Dividends], [Stock Splits], [symbol]) VALUES (?,?,?,?,?,?,?,?,?)', 
                    row['Date'], 
                    row['open_'], 
                    row['high'],
                    row['low'],
                    row['close_'],
                    row['Volume'],
                    row['Dividends'], 
                    row['stock_split'],
                    row['symbol'])
    cnxn.commit()