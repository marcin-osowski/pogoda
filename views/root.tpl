%include header

<section>
  <strong>Current&nbsp;readings</strong>
</section>

<section id="pageContent">
  <article>
    <table>
      <tr><td>Temperature:</td><td>{{ temp }} °C</td></tr>
      <tr><td>Humidity:</td><td>{{ hmdt }} %</td></tr>
    </table>
    <p>&nbsp;</p>
    <p>&nbsp;</p>
    <p>Oldest data: {{ "%.0f" % data_age }} seconds ago.</p>
  </article>
</section>

%include footer
