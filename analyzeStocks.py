import fix_yahoo_finance as yf
import numpy as np
from datetime import *
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
import matplotlib.dates as mdates

pd.options.mode.chained_assignment = None

transactionsFileName = 'data.csv'
fileInPath = Path(transactionsFileName)
if fileInPath.exists():
    transactionsList = pd.read_csv('data.csv', sep='\t')
else:
    print("Nothing here!")


def lookupPriceRange(tickerSymbolList, startDate, endDate):
    data = yf.download(tickerSymbolList, start=startDate, end=endDate, as_panel=True)
    print('DATA LOADED')
    dataClose = data["Close"]  # get only closing value
    return dataClose  # in form of dataframe


def currentPrices(tickerSymbolList):
    today = date.today()
    aWeekAgo = today - timedelta(days=7)
    oneWeekData = lookupPriceRange(tickerSymbolList, aWeekAgo, today)
    lastData = oneWeekData.iloc[-1]
    return lastData


def getStocksList(dataFrame):
    stockNames = dataFrame['StockSymbol'].unique()
    stockNames.sort()
    return stockNames


def getAllTransactions(stockName):
    selectedRows = transactionsList.loc[transactionsList['StockSymbol'] == stockName]
    # selectedRows = selectedRows.set_index('Date')
    selectedRows['Date'] = pd.to_datetime(selectedRows['Date'])
    buyRows = selectedRows.loc[selectedRows['Type'] == 'buy']
    sellRows = selectedRows.loc[selectedRows['Type'] == 'sell']
    return {'sell': sellRows, 'buy': buyRows}


def getCurrentQuantities(stocksNameList):
    stockHoldings = []
    for stock in stocksNameList:
        transLines = getAllTransactions(stock)
        buyRows = transLines['buy']
        sellRows = transLines['sell']
        totalShares = buyRows['Quantity'].sum() - sellRows['Quantity'].sum()
        stockHoldings.append(totalShares)
    return stockHoldings


def getAmountSpent(stocksNameList):
    stockCost = []
    for stock in stocksNameList:
        transLines = getAllTransactions(stock)
        buyRows = transLines['buy']
        sellRows = transLines['sell']
        totalAmount = buyRows['Total Amount'].sum() - sellRows['Total Amount'].sum()
        stockCost.append(totalAmount)
    stockCost = np.array(stockCost)
    return stockCost


def getCurrentValue(stocksNameList, stockHoldings):
    stocksNameList = stocksNameList.tolist()
    pricesToday = currentPrices(stocksNameList)
    valueList = stockHoldings * pricesToday
    return valueList

# ------------------------------------------------------------------
# Overview Scripts


def makeSummaryDF():
    names = getStocksList(transactionsList)
    quantities = getCurrentQuantities(names)
    spent = np.round(getAmountSpent(names), 2)
    currentVal = round(getCurrentValue(names, quantities), 2)
    gainLoss = round((currentVal - spent) / spent, 2)
    df = pd.DataFrame(columns=['Stock Symbol', 'Quantity', 'Cost', 'Current Value', 'Gain/Loss'], index=currentVal.index.values)
    df['Stock Symbol'] = names
    df['Quantity'] = quantities
    df['Cost'] = spent
    df['Current Value'] = currentVal
    df['Gain/Loss'] = gainLoss

    nonZeroDF = df.loc[df['Quantity'] != 0]
    print(nonZeroDF)
    return nonZeroDF


def plotTotalHoldings(summaryDF):
    # Data to plot
    labels = summaryDF['Stock Symbol']
    sizes = summaryDF['Current Value']
    # explode = (0.1, 0, 0, 0)  # explode 1st slice
    # Plot
    plt.pie(sizes, labels=labels,
            autopct='%1.1f%%', shadow=False, startangle=140)
    plt.axis('equal')
    titleString = 'Total = ' + str(round(sum(sizes), 2))
    plt.title(titleString)
    plt.show()


def analyzePeriod(stock, startDate, endDate):
    dataFrame = lookupPriceRange(stock, startDate, endDate)
    transLines = getAllTransactions(stock)

    buyRows = transLines['buy']
    sellRows = transLines['sell']
    buyPoints = buyRows[(buyRows['Date'] > startDate) & (buyRows['Date'] <= endDate)]
    sellPoints = sellRows[(sellRows['Date'] > startDate) & (sellRows['Date'] <= endDate)]

    # Moving averages (10, 50, 200)
    SMA20 = nDayMovingAverage(dataFrame, 20)
    SMA50 = nDayMovingAverage(dataFrame, 50)
    SMA200 = nDayMovingAverage(dataFrame, 200)

    # 50-day RMS
    RMS50 = nDayMovingStd(dataFrame, 50)
    RMS20 = nDayMovingStd(dataFrame, 20)

    # fig, ax = plt.subplots()
    ax = plt
    ax.plot(dataFrame)
    ax.fill_between(dataFrame.index, SMA20 - 2*RMS20, SMA20 + 2*RMS20,
                    alpha=0.2, facecolor='#089FFF', antialiased=True, label='20-day moving RMS')

    if dataFrame.size > 20:
        ax.plot(SMA20, '--', linewidth=1, label='20-day SMA')
    if dataFrame.size > 50:
        ax.plot(SMA50, '--', linewidth=1, label='50-day SMA')
    if dataFrame.size > 200:
        ax.plot(SMA200, '--', linewidth=1, label='200-day SMA')

    ax.legend()

    plot1 = ax.plot(sellPoints['Date'], sellPoints['Price'], 'rv')
    plot2 = ax.plot(buyPoints['Date'], buyPoints['Price'], 'g^')
    for i, txt in enumerate(sellPoints['Quantity']):
        # ax.annotate(str(txt), (mdates.date2num(sellPoints['Date'].iloc[i]), sellPoints['Price'].iloc[i]*.96))
        ax.annotate(str(txt), (mdates.date2num(sellPoints['Date'].iloc[i]), sellPoints['Price'].iloc[i]),
                    textcoords='offset points', xytext=(-8, -15))
    for i, txt in enumerate(buyPoints['Quantity']):
        # ax.annotate(str(txt), (mdates.date2num(buyPoints['Date'].iloc[i]), buyPoints['Price'].iloc[i]*.96))
        ax.annotate(str(txt), (mdates.date2num(buyPoints['Date'].iloc[i]), buyPoints['Price'].iloc[i]),
                    textcoords='offset points', xytext=(-8, -15))
    plt.setp(plot1, markersize=10)
    plt.setp(plot2, markersize=10)

    titleStr = stock + ' Trades ( ' + startDate + ' to ' + endDate + ' )'
    plt.title(titleStr)
    plt.xlabel('Date')
    plt.ylabel('Share Price')
    plt.grid(True)
    # plt.show()


def nDayMovingAverage(series, n):
    if series.size > n:
        simpleMovingAvg = series.rolling(window=n, center=False).mean()
    else:
        print('Series too short!')
    return simpleMovingAvg


# def calcRMS(series, n):
#     if series.size > n:
#         RMS = np.std(series.tail(n))
#     else:
#         print('Not enough data!')
#     return RMS

def nDayMovingStd(series, n):
    if series.size > n:
        simpleMovingStd = series.rolling(window=n, center=False).std()
    else:
        print('Series too short!')
    return simpleMovingStd


def generateAllCharts():
    stringToday = str(date.today())
    startDate = '2017-01-01'
    stockNames = getStocksList(transactionsList)

    for i, stock in enumerate(stockNames):
        plt.figure(i)
        analyzePeriod(stock, startDate, stringToday)

    plt.show()

# generateAllCharts()


def generateChart(name, startDate):
    stringToday = str(date.today())
    # startDate = '2017-01-01'
    plt.figure(0)
    analyzePeriod(name, startDate, stringToday)
    plt.show()

DF = makeSummaryDF()
generateChart('COLM', '2016-08-01')
# generateAllCharts()


# plotTotalHoldings(DF)

