
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

function generate_overview() {
    document.body.style.cursor = 'wait';
    d3.csv('/get-overview-table/')
    .then(function(data){
        document.body.style.cursor = 'default';
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
                drawGraph(stockName);return false
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
}

//function loadData() {
//    $.get('/get-all-data').then(function(data) {
//        var graph1Data = data.graph1Data;
//        var graph2Data = data.graph2Data;
//        var graph3Data = data.graph3Data;
//
//    });
//    d3.csv('/get-time-series-data/'+stock).then(function(data1) {
//        d3.csv('..').then(function(data2)) {
//
//        });
//    })
//}

function parseCSV(string) {
    var rows = string.split('\n');
    var headers = rows[0].split(',');
    var parsedCSV =[];
    for(var i = 1; i < rows.length; i++){
        var thisRow = rows[i].split(',');
        var rowObj = {};
        for(var j =0; j < thisRow.length; j++){
            rowObj[headers[j]] = thisRow[j];
        }
        parsedCSV.push(rowObj)
    }
    return parsedCSV
}


function drawGraph(stock) {
    //first get the data
    $.get('/get-all-time-series-data/'+stock, function(responseData){

        data=parseCSV(responseData.priceData);
        console.log(data);
        var chart = new CanvasJS.Chart("lineGraph", {
            theme: "light2", // "light1", "light2", "dark1", "dark2"
            animationEnabled: true,
            zoomEnabled: true,
            title: {
                text: stock
            },
            axisX: {
                valueFormatString: "YYYY-MM-DD"
            },
            axisY: {
                title: "Closing price ($)",
                includeZero: false
            },
            data: [{
                type: "line",
                name: "Price",
                dataPoints: []
            },
            { type: "scatter",
                name: "Buy Points",
                dataPoints: []
            },
            {type: "scatter",
                name: "Sell Points",
                dataPoints: []
            }]
        });

        addDataPoints(data,0);
        chart.render();

        function addDataPoints(dataInput,lineID) {
            var noOfDps = dataInput.length;
            for(var i = 0; i < noOfDps; i++) {
                var parts =data[i].Date.split('-');
                // Please pay attention to the month (parts[1]); JavaScript counts months from 0:
                // January - 0, February - 1, etc.
                var mydate = new Date(parts[0], parts[1] - 1, parts[2]);
                xVal = mydate
                yVal = Number(data[i][stock])
                chart.options.data[lineID].dataPoints.push({x: xVal, y: yVal});
            }
        }
    })
}


function tabulate(data, columns) {
		var wrapper = d3.select("#textDisplayArea")
		    .html('');
		var table = wrapper.append('table')
		    .classed('table', true);
		console.log(table);
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
		  .append('tr');

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

view_transactions()
