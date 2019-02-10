
function view_transactions(index) {
    d3.csv('/get-transactions-data/').then(function(data){
        tabulate(data, data.columns);
        if (index !== undefined){
            var allRows = document.querySelectorAll('#textDisplayArea tr');
            var thisRow = allRows[index+1];

            var allTD = thisRow.querySelectorAll('td');
            var firstTD = allTD[0];
            firstTD.scrollIntoView({block: "end", behavior: "smooth"});
            d3.select(thisRow).style('background-color','white')
                .transition().delay(200)
                .duration(500)
                .style('background-color', 'rgb(255, 243, 212)')
                .transition()
                .duration(800)
                .style('background-color','white');
        }
    });
}

function add_transaction() {
    var dataIn= $('#addTransactionForm').serializeArray().reduce(function(obj, item) {
        obj[item.name] = item.value;
        return obj;
    }, {});
    $.post('/add-transaction/', dataIn, function(response) {
        var newIndex = parseInt(response);
        view_transactions(newIndex);
    });
}


function delete_transaction() {
    var dataIn= $('#removeTransactionForm').serializeArray().reduce(function(obj, item) {
        obj[item.name] = item.value;
        return obj;
    }, {});
    $.post('/delete-transaction/', dataIn, function(response) {
        var newIndex = parseInt(response);
        view_transactions();
    });
}


function toggle_position(name) {
    d3.csv('/get-overview-table/')
        .then(function(data){
            tabulate(data, data.columns);
            if (name !== undefined){
//                var allRows = document.querySelectorAll('#textDisplayArea tr');
                var thisRow = $("td").filter(function() {
                    return $(this).text() == name;
                }).closest("tr");
                console.log(thisRow)
                var allTD = thisRow.find('td');
                console.log(allTD)
                var firstTD = allTD[0];
                firstTD.scrollIntoView({block: "end", behavior: "smooth"});
                d3.select(thisRow[0]).style('background-color','white')
                    .transition().delay(200)
                    .duration(500)
                    .style('background-color', 'rgb(255, 243, 212)');
            }
        })

    $('#positionslabel').addClass('active');
    $('#transactionslabel').removeClass('active');
}

function generate_overview() {
    document.body.style.cursor = 'wait';
    d3.csv('/get-overview-table/')
    .then(function(data){
        tabulate(data, data.columns);

//make pie chart here:
        var totalPositions = d3.sum(data, function(d){
        return d["Current Value"];
        });

        var color = d3.scaleOrdinal(d3.schemeSet3);
        var width=350;
        var height=370;
        var r = 120;
        var tran = width/2, tran_y = height/2+40;

        var pie = d3.pie()
            .sort(null)
            .value(function(d){return d["Current Value"]})(data);

        var arc = d3.arc()
            .outerRadius(r)
            .innerRadius(0)
            .padAngle(.05)
            .padRadius(50);

        var labelArc = d3.arc()
            .outerRadius(r + 25)
            .innerRadius(r + 25);

        var labelArc2 = d3.arc()
            .outerRadius(r -40)
            .innerRadius(r -40);

        d3.select('#pieChart').html("");
        var svg = d3.select('#pieChart')
            .append('svg')
            .attr('width',width)
            .attr('height',height)
            .append('g')
            .attr("transform", "translate(" + tran + "," + tran_y + ")");

        var allArcs = svg.selectAll("arc")
            .data(pie)
            .enter()
            .append("g")
            .attr("class","arc")
            .on('click', function(d,i){
                var stockName = d.data["Stock Symbol"];
                toggle_position(stockName);
                loadDataAndGraph(stockName);return false
                });


        allArcs.append("path")
            .attr("d",arc)
            .style("fill",function(d,i){
            return color(i);});

        allArcs.append("text")
            .attr("transform", function(d) { return "translate(" + labelArc.centroid(d) + ")"; })
            .text(function(d) {return d.data["Stock Symbol"]})
            .attr("class","textLabels");

        allArcs.append("text")
            .attr("transform", function(d) { return "translate(" + labelArc2.centroid(d) + ")"; })
            .text(function(d) {return d.data["Current Value"]})
            .attr("class","textNumbers");

        svg.append("text")
            .attr("x", 0)
            .attr("y", -200)
            .attr("text-anchor", "middle")
            .style("font-size", "1.3rem")
            .text("Positions");

        svg.append("text")
            .attr("x", 0)
            .attr("y", -180)
            .attr("text-anchor", "middle")
            .style("font-size", ".9rem")
            .text("Total current value: $"+totalPositions.toFixed(2))
            .attr("class","pieTitle")

    });
    loadGainLossGraph();
    $('#positionslabel').addClass('active');
    $('#transactionslabel').removeClass('active');
}



function parseCSV(string) {
    var rows = string.split('\n');
    var headers = rows[0].split(',');
    var parsedCSV =[];
    for(var i = 1; i < rows.length-1; i++){
        var thisRow = rows[i].split(',');
        var rowObj = {};
        for(var j =0; j < thisRow.length; j++){
            rowObj[headers[j]] = thisRow[j];
        }
        parsedCSV.push(rowObj)
    }
    return parsedCSV
}
//
//function parseCSV2(string) {
//    var rows = string.split('\n');
//    var header = rows.splice(0).split(',');
//
//    return rows.map(function(row) {
//        var thisRow = row.split(',');
//        var rowObj = {};
//        for(var j =0; j < thisRow.length; j++){
//            rowObj[headers[j]] = thisRow[j];
//        }
//        return rowObj;
//    });
//}

function loadGainLossGraph() {
    var startDate = document.getElementById("startDateInputID").value;
    var endDate = document.getElementById("endDateInputID").value;
    $.get('/get-gain-loss-data/?start='+startDate +'&end=' + endDate, function(responseData){
        var gainLossData = parseCSV(responseData.gainLoss);
        var VTIData = parseCSV(responseData.VTI);
        drawGainLoss(gainLossData,VTIData);
        document.body.style.cursor = 'default';
    })
}

function drawGainLoss(series1, series2) {
    //first get the data
        var chart = new CanvasJS.Chart("lineGraph", {
            theme: "light2", // "light1", "light2", "dark1", "dark2"
            animationEnabled: true,
            zoomEnabled: true,
            title: {
                text: "Active Portfolio Gain/Loss vs Market Index"
            },
            axisX: {
                valueFormatString: "YYYY-MM-DD"
            },
            axisY: {
                title: "Relative Gain/Loss (%)",
                includeZero: false
            },
            toolTip: {
                shared: true
            },
            data: [
            {
                type: "line",
                name: "My Portfolio",
                color: '#CB654F',
                markerType: 'circle',
                markerSize: 5,
                showInLegend: true,
                dataPoints: []
            },
            {
                type: "line",
                name: "Market Index",
                color: '#8CBEA3',
                showInLegend: true,
                dataPoints: []
            }]
        });

        addDataPoints(series1,0,'Gain/Loss',"");
        addDataPoints(series2,1,'VTI',"")
        console.log(chart)

        chart.render();

        function addDataPoints(dataInput,lineID,yKey,labelKey) {
            var noOfDps = dataInput.length;
            for(var i = 0; i < noOfDps; i++) {
                var parts =dataInput[i].Date.split('-');
                // Please pay attention to the month (parts[1]); JavaScript counts months from 0:
                // January - 0, February - 1, etc.
                var mydate = new Date(parts[0], parts[1] - 1, parts[2]);
                xVal = mydate
                yVal = Number(dataInput[i][yKey])
                if (labelKey ==""){
                labelVal = ""} else {
                labelVal = dataInput[i][labelKey]
                };
                chart.options.data[lineID].dataPoints.push({x: xVal, y: yVal, label: labelVal});
            }
        }
}


function lookup_stock() {
    var stock = document.getElementById("stockLookup").value;
    loadDataAndGraph(stock);
}


function loadDataAndGraph(stock) {
    var startDate = document.getElementById("startDateInputID").value;
    var endDate = document.getElementById("endDateInputID").value;
    var trailingStopPercent = document.getElementById("trailingStopInput").value;

    $.get('/get-all-time-series-data/'+stock+'?start='+startDate +'&end=' + endDate +'&stop=' + trailingStopPercent, function(responseData){
        var data=parseCSV(responseData.priceData);
        var buyData = parseCSV(responseData.buyPoints);
        var sellData = parseCSV(responseData.sellPoints);
        var SMA20Data = parseCSV(responseData.SMA20);
        var SMA200Data = parseCSV(responseData.SMA200);
        var RMS20Data = parseCSV(responseData.RMS20);
        var trailingStopData = parseCSV(responseData.trailingStop)
        drawGraph(data,buyData,sellData,SMA20Data,SMA200Data,RMS20Data,trailingStopData,stock);
        document.getElementById("stockLookup").value = stock;
    })
}


function drawGraph(priceData,buyData,sellData,SMA20Data,SMA200Data,RMS20Data,trailingStopData,stock){
    var divEl = document.getElementById("lineGraph");
    divEl.innerHTML = "";
    var chart = new StockLineChart(stock);
    var parseTime = d3.timeParse("%Y-%m-%d");

    priceData.forEach(function(d) {
        d.date = parseTime(d.Date);
        d.close = +d[stock];
    });

    SMA20Data.forEach(function(d) {
        d.date = parseTime(d.Date);
        d.close = +d[stock];
    });

    SMA200Data.forEach(function(d) {
        d.date = parseTime(d.Date);
        d.close = +d[stock];
    });

    RMS20Data.forEach(function(d) {
        d.date = parseTime(d.Date);
        d.close = +d[stock];
    });

    trailingStopData.forEach(function(d) {
        d.date = parseTime(d.Date);
        d.close = +d[stock];
    });

    buyData.forEach(function(d) {
        d.date = parseTime(d.Date);
        d.close = +d['Price'];
        d.label = 'Quantity: '+ d['Quantity'] +' | Price: '+ d['Price'];
    });

    sellData.forEach(function(d) {
        d.date = parseTime(d.Date);
        d.close = +d['Price'];
        d.label = 'Quantity: '+ d['Quantity'] +' | Price: '+ d['Price'];
    });


    chart.addBand(SMA20Data.map((d,i) => {
        return {
            date: d.date,
            yMin: d.close - 2*RMS20Data[i].close,
            yMax: d.close + 2*RMS20Data[i].close
        }
    }), 'band', {
        mark: 'circle',
        markSize: 3
    });

    chart.addLine(priceData, 'Closing-Price', {
        mark: 'circle',
        markSize: 5,
        showValue: function(date, value) {
            return monthNames[date.getMonth()].substr(0,3) + ' ' + date.getDate() + ': $' + value;
        }
    });

    var monthNames = [
        "January", "February", "March",
        "April", "May", "June", "July",
        "August", "September", "October",
        "November", "December"
    ];

    chart.addLine(SMA20Data, 'SMA-20');
    chart.addLine(SMA200Data, 'SMA-200');
    chart.addLine(trailingStopData, 'Trailing-Stop');

    chart.addPoints(buyData, 'buy', 'triangle');
    chart.addPoints(sellData, 'sell', 'triangle');
}

//
//function drawGraph(priceData,buyData,sellData,SMA20Data,SMA200Data,RMS20Data,stock) {
//    //first get the data
//        var chart = new CanvasJS.Chart("lineGraph", {
//            theme: "light2", // "light1", "light2", "dark1", "dark2"
//            animationEnabled: true,
//            zoomEnabled: true,
//            title: {
//                text: stock
//            },
//            axisX: {
//                valueFormatString: "YYYY-MM-DD"
//            },
//            axisY: {
//                title: "Closing price ($)",
//                includeZero: false
//            },
//            toolTip: {
//                shared: false
//            },
//            data: [
//            {
//                type: "rangeArea",
//                name: "2-Sigma Volatility",
//                fillOpacity: .8,
//                lineThickness: 0,
//                color: '#D6DEE8',
//                dataPoints: []
//            },
//            {
//                type: "line",
//                name: "Price",
//                color: '#335B8E',
//                dataPoints: []
//            },
//            {   type: "scatter",
//                name: "Buy Points",
//                markerType: "triangle",
//                markerColor: "#8CBEA3",
//                markerSize: 15,
//                indexLabelFormatter: formatter,
//                indexLabelFontWeight: "bold",
//                indexLabelFontSize: 15,
//                toolTipContent: "Buy {label} at ${y}",
//                dataPoints: []
//            },
//            {   type: "scatter",
//                name: "Sell Points",
//                markerType: "cross",
//                markerColor: "#CB654F",
//                markerSize: 12,
//                indexLabelFormatter: formatter,
//                indexLabelFontWeight: "bold",
//                indexLabelFontSize: 15,
//                toolTipContent: "Sell {label} at ${y}",
//                dataPoints: []
//            },
//            {
//                type: "line",
//                name: "SMA 20",
//                lineDashType: "dot",
//                lineThickness: 1,
//                toolTipContent: null,
//                color: '##335B8E',
//                dataPoints: []
//            },
//            {
//                type: "line",
//                name: "SMA 200",
//                lineDashType: "dot",
//                lineThickness: 2,
//                toolTipContent: null,
//                color: '#B66E56',
//                dataPoints: []
//            }]
//        });
//
//        addRangePoints(SMA20Data,RMS20Data,0,stock)
//        addDataPoints(priceData,1,stock,"");
//        addDataPoints(buyData,2,'Price','Quantity')
//        addDataPoints(sellData,3,'Price','Quantity')
//        addDataPoints(SMA20Data,4,stock,'')
//        addDataPoints(SMA200Data,5,stock,'')
//
//        console.log(chart)
//
//        chart.render();
//
//        function addDataPoints(dataInput,lineID,yKey,labelKey) {
//            var noOfDps = dataInput.length;
//            for(var i = 0; i < noOfDps; i++) {
//                var parts =dataInput[i].Date.split('-');
//                // Please pay attention to the month (parts[1]); JavaScript counts months from 0:
//                // January - 0, February - 1, etc.
//                var mydate = new Date(parts[0], parts[1] - 1, parts[2]);
//                xVal = mydate
//                yVal = Number(dataInput[i][yKey])
//                if (labelKey ==""){
//                labelVal = ""} else {
//                labelVal = dataInput[i][labelKey]
//                };
//                chart.options.data[lineID].dataPoints.push({x: xVal, y: yVal, label: labelVal});
//            }
//        }
//
//        function addRangePoints(meanInput,stdInput,lineID,yKey) {
//            var noOfDps = meanInput.length;
//            for(var i = 0; i < noOfDps; i++) {
//                var parts =meanInput[i].Date.split('-');
//                // Please pay attention to the month (parts[1]); JavaScript counts months from 0:
//                // January - 0, February - 1, etc.
//                var mydate = new Date(parts[0], parts[1] - 1, parts[2]);
//                xVal = mydate
//                yValHigh = Number(meanInput[i][yKey])+2*Number(stdInput[i][yKey])
//                yValLow = Number(meanInput[i][yKey])-2*Number(stdInput[i][yKey])
//                chart.options.data[lineID].dataPoints.push({x: xVal, y: [yValLow, yValHigh]});
//            }
//        }
//
//        function formatter(e){
//            var quant = Number(e.dataPoint.label);
//            return quant.toFixed(0)
//        }
//}


function tabulate(data, columns) {
		var wrapper = d3.select("#textDisplayArea")
		    .html('');
		var table = wrapper.append('table')
		    .classed('table', true);
		var thead = table.append('thead')
		var	tbody = table.append('tbody');

		// append the header row
		thead.append('tr')
		  .selectAll('th')
		  .data(columns).enter()
		  .append('th')
		    .text(function (column) { return column; });

		// create a row for each object in the data
		var rows = tbody.selectAll('tr')
		  .data(data)
		  .enter()
		  .append('tr')
		  .on('click', function(d,i){
		    var stockName = d["Stock Symbol"];
            loadDataAndGraph(stockName);
            return false;
		    })
		   .on("mouseover", function(d) {
            d3.select(this).style("cursor", "pointer");
            d3.select(this).style("color","#ccc");
            })
            .on("mouseout", function(d) {
            d3.select(this).style("color","black");
            });

		// create a cell in each row for each column
		var cells = rows.selectAll('td')
		  .data(function (row) {
		    return columns.map(function (column) {
		      return {column: column, value: row[column]};
		    });
		  })
		  .enter()
		  .append('td')
		    .text(function (d) { return d.value; });

	  return table;
	}

function startUp() {
    view_transactions()
    var today = new Date();
    var dd = today.getDate();
    var mm = today.getMonth() + 1; //January is 0!
    var yyyy = today.getFullYear();

    if (dd < 10) {
      dd = '0' + dd;
    }

    if (mm < 10) {
      mm = '0' + mm;
    }

    today = yyyy + '-' + mm + '-' + dd ;
    document.getElementById("endDateInputID").value = today;

    generate_overview();
}


startUp()