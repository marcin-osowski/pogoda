%include header

<section>
  <strong>Current&nbsp;readings</strong>
</section>

<section id="pageContent">
  <article>
    <p>Temperature: {{ temp }} °C </p>
    <p>&nbsp;</p>
    <p>Humidity: {{ hmdt }} % </p>
    <p>&nbsp;</p>
    <p>&nbsp;</p>
    <p>&nbsp;</p>
    <p>Data collected {{ "%.0f" % data_age }} seconds ago.</p>
  </article>
</section>

%include footer
