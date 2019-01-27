from flask import Flask, render_template, send_from_directory, request, Response
from editTransactions import *
from analyzeStocks import *
import json

app = Flask(__name__)
stringToday = str(date.today())


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/add-transaction/', methods=['post', 'get'])
def add_transaction():
    buySellFlag = request.form['buySell']
    dateInput = request.form['dateInput']
    stockInput = request.form['stockInput']
    quantityInput = request.form['quantityInput']
    priceInput = request.form['priceInput']
    newIndex = addNewTransactionNoPrompt(buySellFlag, dateInput, stockInput, quantityInput, priceInput)
    return str(newIndex)


@app.route('/get-transactions-data/')
def view_transactions():
    transactionsListLocal = viewTransactions()
    csvData = transactionsListLocal.to_csv()
    return csvData


@app.route('/get-overview-table/')
def overview_table():
    dataFrame = makeSummaryDF(stringToday)
    nonZeroDF = dataFrame.loc[dataFrame['Quantity'] != 0]
    # columnsDF = nonZeroDF.columns
    # noStockDF = dataFrame[columnsDF[1:]]
    csvData = nonZeroDF.to_csv(index=False)
    return csvData


@app.route('/get-all-time-series-data/<stockName>')
def get_all_time_series(stockName):
    startDate = "2017-01-01"
    dataSeries = lookupPriceFromTable(stockName, startDate, stringToday)
    priceData = dataSeries.to_csv(header=True)

    # buyPoints = getBuySellPoints(stockName, 'buy', startDate, stringToday)
    # csvBuy = buyPoints.to_csv(header=True)
    # sellPoints = getBuySellPoints(stockName, 'sell', startDate, stringToday)
    # csvSell = sellPoints.to_csv(header=True)
    return Response(json.dumps({'priceData': priceData}), mimetype='application/json')


@app.route('/get-time-series-data/<stockName>')
def get_time_series(stockName):
    startDate = "2017-01-01"
    dataSeries = lookupPriceFromTable(stockName, startDate, stringToday)
    csvData = dataSeries.to_csv(header=True)
    return csvData


@app.route('/files/<path:path>')
def send_js(path):
    return send_from_directory('templates', path)


if __name__ == '__main__':
  app.run(debug=False)