%include header

<script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
<script type="text/javascript">
  google.charts.load('current', {'packages':['corechart']});
  google.charts.setOnLoadCallback(drawCharts);

  function drawCharts() {
    // Temperature
    var temp_data = google.visualization.arrayToDataTable([
      ['Time', 'Temperature [°C]'],
      % for row in temp_history:
        [new Date('{{ row[1].isoformat() }}'), {{ row[0] }}],
      % end
    ]);

    var temp_options = {
      title: 'Temperature [°C]',
      legend: { position: 'none' },
      chartArea: { width: '75%' },
    };

    var temp_chart = new google.visualization.LineChart(
        document.getElementById('temp_chart'));
    temp_chart.draw(temp_data, temp_options);

    // Humidity
    var hmdt_data = google.visualization.arrayToDataTable([
      ['Time', 'Humidity [%]'],
      % for row in hmdt_history:
        [new Date('{{ row[1].isoformat() }}'), {{ row[0] }}],
      % end
    ]);

    var hmdt_options = {
      title: 'Humidity [%]',
      legend: { position: 'none' },
      chartArea: { width: '75%' },
    };

    var hmdt_chart = new google.visualization.LineChart(
        document.getElementById('hmdt_chart'));
    hmdt_chart.draw(hmdt_data, hmdt_options);

    // Vapor pressure
    var vapor_pres_data = google.visualization.arrayToDataTable([
      ['Time', 'Vapor pressure [hPa]'],
      % for row in vapor_pres_history:
        [new Date('{{ row[1].isoformat() }}'), {{ row[0] }}],
      % end
    ]);

    var vapor_pres_options = {
      title: 'Vapor pressure [hPa]',
      legend: { position: 'none' },
      chartArea: { width: '75%' },
    };

    var vapor_pres_chart = new google.visualization.LineChart(
        document.getElementById('vapor_pres_chart'));
    vapor_pres_chart.draw(vapor_pres_data, vapor_pres_options);

    // Dew point
    var dew_point_data = google.visualization.arrayToDataTable([
      ['Time', 'Dew point [°C]'],
      % for row in dew_point_history:
        [new Date('{{ row[1].isoformat() }}'), {{ row[0] }}],
      % end
    ]);

    var dew_point_options = {
      title: 'Dew point [°C]',
      legend: { position: 'none' },
      chartArea: { width: '75%' },
    };

    var dew_point_chart = new google.visualization.LineChart(
        document.getElementById('dew_point_chart'));
    dew_point_chart.draw(dew_point_data, dew_point_options);

    // Pressure
    var pres_data = google.visualization.arrayToDataTable([
      ['Time', 'Pressure [hPa]'],
      % for row in pres_history:
        [new Date('{{ row[1].isoformat() }}'), {{ row[0] }}],
      % end
    ]);

    var pres_options = {
      title: 'Pressure [hPa]',
      legend: { position: 'none' },
      chartArea: { width: '75%' },
    };

    var pres_chart = new google.visualization.LineChart(
        document.getElementById('pres_chart'));
    pres_chart.draw(pres_data, pres_options);
  }
</script>


<section>
  <strong>Charts (smoothed)</strong>
</section>

<section id="pageContent">

  <article>
    <div id="temp_chart" style="width: 100%; min-height: 450px"></div>
  </article>

  <article>
    <div id="hmdt_chart" style="width: 100%; min-height: 450px"></div>
  </article>

  <article>
    <div id="vapor_pres_chart" style="width: 100%; min-height: 450px"></div>
  </article>

  <article>
    <div id="dew_point_chart" style="width: 100%; min-height: 450px"></div>
  </article>

  <article>
    <div id="pres_chart" style="width: 100%; min-height: 450px"></div>
  </article>

</section>

%include footer
