
function view_transactions() {
    d3.csv('/get-transactions-data/').then(function(data){
    tabulate(data, data.columns);
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
        var width=420;
        var height=420;
        var r = 130;
        var tran = width/2, tran_y = tran+20;

        var pie = d3.pie()
            .sort(null)
            .value(function(d){return d["Current Value"]})(data);

        console.log(pie)

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
                    .attr("class","arc");

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
            .text("Total current value: $"+totalPositions)
            .attr("class","pieTitle")

    });
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