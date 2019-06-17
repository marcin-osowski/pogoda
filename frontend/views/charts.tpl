%include header

<script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
<script type="text/javascript">
  google.charts.load('current', {'packages':['corechart']});
  google.charts.setOnLoadCallback(drawCharts);

  function drawCharts() {
    % for chart_data in chart_datas:
    {
        var data = google.visualization.arrayToDataTable([
          ['Time', '{{ chart_data.description }}'],
          % for row in chart_data.history:
            [new Date('{{ row[1].isoformat() }}'),
             {{ row[0] if row[0] is not None else "null" }}],
          % end
        ]);

        var options = {
          title: '{{ chart_data.description }}',
          legend: { position: 'none' },
          chartArea: { width: '75%' },
          hAxis: {
            minValue: new Date('{{ time_from.isoformat() }}'),
            maxValue: new Date('{{ time_to.isoformat() }}'),
          },
        };

        var chart = new google.visualization.{{ chart_data.chart_type }}(
            document.getElementById('{{ "%s_chart" % chart_data.name }}'));
        chart.draw(data, options);
    }
    % end
  }
</script>


<section>
  <strong>Charts (smoothed)</strong>
</section>

<section id="pageContent">

  % for chart_data in chart_datas:
    <article>
      <div id="{{ "%s_chart" % chart_data.name}}"
           style="width: 100%; min-height: 450px"></div>
    </article>
  % end

</section>

%include footer
