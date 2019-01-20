from flask import Flask, render_template, send_from_directory, request
from editTransactions import *
from analyzeStocks import *

app = Flask(__name__)


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

    addNewTransactionNoPrompt(buySellFlag, dateInput, stockInput, quantityInput, priceInput)
    return render_template('index.html')


@app.route('/get-transactions-data/')
def view_transactions():
    transactionsList = viewTransactions()
    csvData = transactionsList.to_csv()
    return csvData


@app.route('/get-overview-table/')
def overview_table():
    dataFrame = makeSummaryDF()
    csvData = dataFrame.to_csv()
    return csvData


@app.route('/files/<path:path>')
def send_js(path):
    return send_from_directory('templates', path)


if __name__ == '__main__':
  app.run(debug=True)