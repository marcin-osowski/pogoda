%include header

<script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
<script type="text/javascript">
  google.charts.load('current', {'packages':['corechart']});
  google.charts.setOnLoadCallback(drawCharts);

  function drawCharts() {
    % for chart in charts:
    {
        var data = google.visualization.arrayToDataTable([
          [
            'Time',
            % for description, _ in chart.series:
              '{{ description }}',
            % end
          ],
          % num_series = len(chart.series)
          % for i, (_, series) in enumerate(chart.series):
              % for row in series:
                [
                  new Date('{{ row[1].isoformat() }}'),
                  % for j in range(num_series):
                    % if j == i:
                      {{ row[0] if row[0] is not None else "null" }},
                    % else:
                      null,
                    % end
                  % end
                ],
              % end
          % end
        ]);

        var options = {
          title: '{{ chart.description }}',
          legend: { position: 'none' },
          chartArea: { width: '75%' },
          hAxis: {
            minValue: new Date('{{ time_from.isoformat() }}'),
            maxValue: new Date('{{ time_to.isoformat() }}'),
          },
          vAxis: {
            minValue: 0,
          }
        };

        var chart = new google.visualization.{{ chart.chart_type }}(
            document.getElementById('{{ "%s_chart" % chart.name }}'));
        chart.draw(data, options);
    }
    % end
  }
</script>


<section>
  <strong>Sensor devices status</strong>
</section>

<section id="pageContent">

    % for chart in charts:
      <article>
        <div id="{{ "%s_chart" % chart.name}}"
             style="width: 100%; min-height: 450px"></div>
      </article>
    % end
  <p>Gaps in the charts indicate temporary loss of Internet connection.</p>

</section>

%include footer
