%include header

<script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
<script type="text/javascript">
  google.charts.load('current', {'packages':['corechart']});
  google.charts.setOnLoadCallback(drawCharts);

  function drawCharts() {
    // Temperature
    var temp_data = google.visualization.arrayToDataTable([
      ['Time', 'Temperature'],
      % for row in temp_history:
        ['{{ row[1] }}', {{ row[0] }}],
      % end
    ]);

    var temp_options = {
      title: 'Temperature',
      legend: { position: 'none' }
    };

    var temp_chart = new google.visualization.LineChart(document.getElementById('temp_chart'));
    temp_chart.draw(temp_data, temp_options);

    // Humidity
    var hmdt_data = google.visualization.arrayToDataTable([
      ['Time', 'Humidity'],
      % for row in hmdt_history:
        ['{{ row[1] }}', {{ row[0] }}],
      % end
    ]);

    var hmdt_options = {
      title: 'Humidity',
      legend: { position: 'none' }
    };

    var hmdt_chart = new google.visualization.LineChart(document.getElementById('hmdt_chart'));

    hmdt_chart.draw(hmdt_data, hmdt_options);
  }
</script>


<section>
  <strong>Charts</strong>
</section>

<section id="pageContent">
  <article>
    <div id="temp_chart" style="width: 900px; height: 500px"></div>
  </article>

  <article>
    <div id="hmdt_chart" style="width: 900px; height: 500px"></div>
  </article>
</section>

%include footer
