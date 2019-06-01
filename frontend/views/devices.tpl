%include header

<script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
<script type="text/javascript">
  google.charts.load('current', {'packages':['corechart']});
  google.charts.setOnLoadCallback(drawCharts);

  function drawCharts() {
    var data = google.visualization.arrayToDataTable([
      ['Time', 'Internet latency [ms]'],
      % for value, timestamp in ground_latency:
        [new Date('{{ timestamp.isoformat() }}'),
         {{ value * 1000.0 if value is not None else "null" }}],
      % end
    ]);

    var options = {
      title: 'Ground level weather sensor Internet connection latency [ms]',
      legend: { position: 'none' },
      chartArea: { width: '75%' },
      hAxis: {
        minValue: new Date('{{ time_from.isoformat() }}'),
        maxValue: new Date('{{ time_to.isoformat() }}'),
      },
    };

    var chart = new google.visualization.LineChart(
        document.getElementById('latency_chart'));
    chart.draw(data, options);
  }
</script>


<section>
  <strong>Sensor devices status</strong>
</section>

<section id="pageContent">

  <article>
    <div id="latency_chart" style="width: 100%; min-height: 450px"></div>
    <p>Gaps in the chart indicate temporary loss of Internet connection.</p>
  </article>

</section>

%include footer
