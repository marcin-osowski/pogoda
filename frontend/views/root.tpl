%include header

<section>
  <strong>Current&nbsp;readings</strong>
</section>

<section id="pageContent">
  <article>
    <table>
      % if temp is not None:
          <tr><td>Temperature:</td><td>{{ temp }} °C</td></tr>
      % end
      % if hmdt is not None:
          <tr><td>Humidity:</td><td>{{ hmdt }} %</td></tr>
      % end
      % if vapor_pres is not None:
          <tr><td>Vapor pressure:</td><td>{{ "%.1f" % vapor_pres }} hPa</td></tr>
      % end
      % if pres is not None:
          <tr><td>Pressure:</td><td>{{ pres }} hPa</td></tr>
      % end
    </table>
    <p>&nbsp;</p>
    <p>&nbsp;</p>
    <p>Oldest data:
    {{ "%.0f seconds ago." % data_age if data_age is not None else "unknown." }}
    </p>
  </article>
</section>

%include footer
