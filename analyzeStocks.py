import fix_yahoo_finance as yf
import numpy as np
from datetime import *
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
import matplotlib.dates as mdates
import time


pd.options.mode.chained_assignment = None
pd.set_option('display.max_columns', None)


def getStocksList(dataFrame):
    stockNames = dataFrame['Stock Symbol'].unique()
    stockNames.sort()
    return stockNames


def lookupPriceRange(tickerSymbolList, startDate, endDate):
    attempts = 0
    while attempts < 3:
        try:
            data = yf.download(tickerSymbolList, start=startDate, end=endDate, as_panel=True)
            dataClose = data["Close"]
            print('DATA LOADED')
            break
        except ValueError:
            print("Did not succesfully load data")
            attempts += 1
            time.sleep(1)

    return dataClose  # in form of dataframe


def startUp():
    transactionsFileName = 'data.csv'
    fileInPath = Path(transactionsFileName)
    if fileInPath.exists():
        transactionsListLocal = pd.read_csv('data.csv', sep='\t')
    else:
        print("Nothing here!")
    globalStocksList = getStocksList(transactionsListLocal).tolist()
    todayDate = date.today()
    fiveYearsAgo = todayDate - timedelta(days=5*365)
    firstDateTransactions = pd.to_datetime(transactionsListLocal['Date']).min()
    firstDate = min([firstDateTransactions.date(), fiveYearsAgo])
    firstDateStr = firstDate.strftime('%Y-%m-%d')

    todayStr = todayDate.strftime('%Y-%m-%d')
    globalLookupDFLocal = lookupPriceRange(globalStocksList, firstDateStr, todayStr)
    return transactionsListLocal, globalLookupDFLocal


transactionsList, globalLookupDF = startUp()


def lookupPriceFromTable(tickerSymbolList, startDate, endDate):
    startDate = pd.to_datetime(startDate)
    endDate = pd.to_datetime(endDate)
    # df1 = globalLookupDF[tickerSymbolList]
    # df = df1[(df1.index >= startDate) & (df1.index <= endDate)]
    # if stock is in the database look it up in database otherwise look it up online
    dfKeys = globalLookupDF.keys().tolist()

    if isinstance(tickerSymbolList, str):
        condition = tickerSymbolList in dfKeys
    else:
        condition = all(elem in dfKeys for elem in tickerSymbolList)

    todayDate = date.today()
    fiveYearsAgo = todayDate - timedelta(days=5*365)
    startDateObj = pd.to_datetime(startDate).date()

    inDBRange = startDateObj > fiveYearsAgo

    if condition and inDBRange:
        df1 = globalLookupDF[tickerSymbolList]
        df = df1[(df1.index >= startDate) & (df1.index <= endDate)]
    else:
        df1 = lookupPriceRange(tickerSymbolList, startDate, endDate)
        df1.name = tickerSymbolList
        df = df1

    df_nonan = df.dropna()
    return df_nonan


def currentPrices(tickerSymbolList, thisDay):
    # today = date.today()
    aWeekAgo = pd.to_datetime(thisDay) - timedelta(days=4)
    oneWeekData = lookupPriceFromTable(tickerSymbolList, aWeekAgo, thisDay)
    lastData = oneWeekData.iloc[-1]
    return lastData


def filterTransactions(startDate, endDate):
    startDate = pd.to_datetime(startDate)
    endDate = pd.to_datetime(endDate)
    transactionsList['Date'] = pd.to_datetime(transactionsList['Date'])
    filteredTransactions = transactionsList.loc[(startDate <= transactionsList['Date']) & (transactionsList['Date'] <= endDate)]
    return filteredTransactions


def getAllTransactions(stockName, dataFrame):
    selectedRows = dataFrame.loc[dataFrame['Stock Symbol'] == stockName]
    # selectedRows = selectedRows.set_index('Date')
    selectedRows['Date'] = pd.to_datetime(selectedRows['Date'])
    buyRows = selectedRows.loc[selectedRows['Type'] == 'buy']
    sellRows = selectedRows.loc[selectedRows['Type'] == 'sell']
    return {'sell': sellRows, 'buy': buyRows}


def getQuantityBought(stocksNameList, dataFrame):
    stockHoldings = []
    for stock in stocksNameList:
        transLines = getAllTransactions(stock, dataFrame)
        buyRows = transLines['buy']
        totalShares = buyRows['Quantity'].sum()
        stockHoldings.append(totalShares)
    return stockHoldings


def getQuantitySold(stocksNameList, dataFrame):
    stockHoldings = []
    for stock in stocksNameList:
        transLines = getAllTransactions(stock, dataFrame)
        sellRows = transLines['sell']
        totalShares = sellRows['Quantity'].sum()
        stockHoldings.append(totalShares)
    return stockHoldings


def getCurrentQuantities(stocksNameList, dataFrame):
    stockHoldings = np.array(getQuantityBought(stocksNameList, dataFrame))-np.array(getQuantitySold(stocksNameList, dataFrame))
    return stockHoldings


def getAmountSpent(stocksNameList, dataFrame):
    stockCost = []
    for stock in stocksNameList:
        transLines = getAllTransactions(stock, dataFrame)
        buyRows = transLines['buy']
        totalAmount = buyRows['Total Amount'].sum()
        stockCost.append(totalAmount)
    stockCost = np.array(stockCost)
    return stockCost


def getAmountEarned(stocksNameList, dataFrame):
    stockEarnings = []
    for stock in stocksNameList:
        transLines = getAllTransactions(stock, dataFrame)
        sellRows = transLines['sell']
        totalAmount = sellRows['Total Amount'].sum()
        stockEarnings.append(totalAmount)
    stockEarnings = np.array(stockEarnings)
    return stockEarnings


def getCurrentValue(stocksNameList, stockHoldings, thisDay):
    stocksNameList = stocksNameList.tolist()
    pricesToday = currentPrices(stocksNameList, thisDay)
    valueList = stockHoldings * pricesToday
    return valueList

# ------------------------------------------------------------------
# Overview Scripts


def makeSummaryDF(thisDay):
    transactions = filterTransactions('2000-01-01', thisDay)
    names = getStocksList(transactions)
    quantities = getCurrentQuantities(names, transactions)
    spentOnly = np.round(getAmountSpent(names, transactions), 2)
    earnedOnly = np.round(getAmountEarned(names, transactions), 2)
    boughtQuant = getQuantityBought(names, transactions)
    soldQuant = getQuantitySold(names, transactions)
    pricesToday = currentPrices(names, thisDay)

    avgBuyPrice = spentOnly/boughtQuant

    currentVal = np.round(getCurrentValue(names, quantities, thisDay), 2)
    spentOnPosition = avgBuyPrice*quantities
    gainLossCumulative = np.round(currentVal - spentOnly + earnedOnly, 2)
    gainLossPercent = np.round((currentVal-spentOnPosition)/spentOnPosition*100,1)

    df = pd.DataFrame(columns=['Stock Symbol', 'Quantity', 'Current Price', 'Current Value', 'Current Gain/Loss %',
                               'Cumulative Gain/Loss $'],
                      index=currentVal.index.values)
    df['Stock Symbol'] = names
    df['Quantity'] = quantities
    # df['Cost'] = np.round(avgBuyPrice*quantities,2)
    df['Current Price'] = np.round(pricesToday, 2)
    df['Current Value'] = currentVal
    df['Current Gain/Loss %'] = gainLossPercent
    df['Cumulative Gain/Loss $'] = gainLossCumulative
    return df


def calcTotalGainLoss(df):
    totalGainLoss = np.round(df['Cumulative Gain/Loss $'].sum(), 2)
    print(totalGainLoss)
    return totalGainLoss


def plotTotalHoldings(summaryDF):
    # Data to plot
    nonZeroDF = summaryDF.loc[summaryDF['Quantity'] != 0]
    print(nonZeroDF)

    labels = nonZeroDF['Stock Symbol']
    sizes = nonZeroDF['Current Value']
    # explode = (0.1, 0, 0, 0)  # explode 1st slice
    # Plot
    plt.pie(sizes, labels=labels,
            autopct='%1.1f%%', shadow=False, startangle=140)
    plt.axis('equal')
    titleString = 'Total = ' + str(round(sum(sizes), 2))
    plt.title(titleString)
    plt.show()

    # def onpick(event):
    #     thisline = event.artist
    #     xdata = thisline.get_xdata()
    #     ydata = thisline.get_ydata()
    #     ind = event.ind
    #     points = tuple(zip(xdata[ind], ydata[ind]))
    #     print('onpick points:', points)
    #
    # plt.canvas.mpl_connect('pick_event', onpick)


def getBuySellPoints(stock, typeBS, df):
    transLines = getAllTransactions(stock, df)
    buySellRows = transLines[typeBS]
    return buySellRows


def analyzePeriod(stock, startDate, endDate):
    dataFrame = lookupPriceFromTable(stock, startDate, endDate)
    filteredDF = filterTransactions(startDate, endDate)

    buyPoints = getBuySellPoints(stock, 'buy', filteredDF)
    sellPoints = getBuySellPoints(stock, 'sell', filteredDF)

    # Moving averages (10, 50, 200)
    SMA20 = nDayMovingAverage(dataFrame, 20)
    SMA50 = nDayMovingAverage(dataFrame, 50)
    SMA200 = nDayMovingAverage(dataFrame, 200)

    # 50-day RMS

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
        simpleMovingAvg = simpleMovingAvg[~np.isnan(simpleMovingAvg)]
    else:
        print('Series too short!')
    return simpleMovingAvg


def calcTrailingStopSegment(series, percent, startDate):
    startDate = pd.to_datetime(startDate)
    seriesFiltered = series.loc[series.index > startDate]
    stopSeries = (1-percent/100)*seriesFiltered
    stopLine = []
    maxVal = 0
    for i, elem in enumerate(stopSeries):
        if elem >= maxVal:
            maxVal = elem
            stopLine.append(maxVal)
        else:
            stopLine.append(maxVal)
        if maxVal >= seriesFiltered[i]:
            break
    nElements = len(stopLine)
    stopLineSeries = pd.Series(data=stopLine, index=stopSeries.index[:nElements], name=stopSeries.name)
    # stopLineTruncated = stopLineSeries[stopLineSeries <= seriesFiltered]
    return stopLineSeries


def calcTrailingStop(series, percent, startDate):
    startDateOverall = pd.to_datetime(startDate)
    endDateOverall = series.tail(1).index[0]
    stopLineOut = pd.Series(name=series.name)
    startDate = startDateOverall

    while startDate < endDateOverall:
        startDateStr = startDate.strftime('%Y-%m-%d')
        stopLineSegment = calcTrailingStopSegment(series, percent, startDateStr)
        stopLineOut = stopLineOut.append(stopLineSegment)
        startDate = stopLineSegment.tail(1).index[0] + pd.Timedelta(1, unit="d")

    stopLineOut.index.name = 'Date'

    return stopLineOut


# dataSeries = lookupPriceFromTable('GE', '2017-01-01', '2018-02-04')
# calcTrailingStop(dataSeries, 10, '2017-04-01')

# def calcRMS(series, n):
#     if series.size > n:
#         RMS = np.std(series.tail(n))
#     else:
#         print('Not enough data!')
#     return RMS


def nDayMovingStd(series, n):
    if series.size > n:
        simpleMovingStd = series.rolling(window=n, center=False).std()
        simpleMovingStd = simpleMovingStd[~np.isnan(simpleMovingStd)]
    else:
        print('Series too short!')
    return simpleMovingStd


def generateAllCharts(startDate):
    stringToday = str(date.today())
    dataFrame = makeSummaryDF(stringToday)
    stockNames = dataFrame['Stock Symbol']
    for i, stock in enumerate(stockNames):
        plt.figure(i)
        analyzePeriod(stock, startDate, stringToday)

    plt.show()
    return dataFrame


def generateChart(name, startDate):
    stringToday = str(date.today())
    # startDate = '2017-01-01'
    plt.figure(0)
    analyzePeriod(name, startDate, stringToday)
    plt.show()


def generateGainLossOverTime(startDate, endDate):
    # stringToday = str(date.today())
    # startDate = '2017-02-01'
    startDateObj = pd.to_datetime(startDate)
    endDateObj = pd.to_datetime(endDate)
    diffDays = pd.Timedelta(endDateObj-startDateObj).days
    print(diffDays)

    nPoints = 50
    frequency = max(round(diffDays/nPoints), 1)
    freqString = str(frequency)+'D'
    print(freqString)

    rangeDate = pd.date_range(start=startDate, end=endDate, freq=freqString)
    datesPy = rangeDate.to_pydatetime()

    VTICompare = lookupPriceFromTable('VTI', startDate, endDate)
    gainLoss = []
    totalValue = []
    for i, eachDate in enumerate(datesPy):
        stringDate = eachDate.strftime('%Y-%m-%d')
        print(stringDate)
        dataFrame = makeSummaryDF(stringDate)
        gainLossDay = calcTotalGainLoss(dataFrame)
        totalValueDay = dataFrame['Current Value'].sum()
        totalValue.append(totalValueDay)
        gainLoss.append(gainLossDay)

    meanValue = np.mean(totalValue)
    gainLossPercent = ((gainLoss-gainLoss[0])/meanValue)*100
    VTICompare = ((VTICompare - VTICompare[0])/VTICompare[0])*100

    gainLossSeries = pd.Series(data=gainLossPercent, index=rangeDate, name='Gain/Loss')
    gainLossSeries.index.name = 'Date'
    return gainLossSeries, VTICompare


def plotGainLoss(startDate):
    gainLossSeries, VTICompare = generateGainLossOverTime(startDate)
    plt.plot(gainLossSeries, label='My Portfolio')
    plt.plot(VTICompare, label='VTI Index')
    plt.title('Gain/Loss Since ' + startDate)
    plt.xlabel('Date')
    plt.ylabel('Change in Value of Investments (% Mean Investment)')
    plt.legend()
    plt.show()

# generateChart('COST', '2017-01-01')
# DF = generateAllCharts('2017-01-01')

#
# stringToday = str(date.today())
# DF = makeSummaryDF(stringToday)
# plotGainLoss('2017-01-01')
# plotTotalHoldings(DF)

