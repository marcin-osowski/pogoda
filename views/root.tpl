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
    </table>
    <p>&nbsp;</p>
    <p>&nbsp;</p>
    % if data_age is not None:
        <p>Oldest data: {{ "%.0f" % data_age }} seconds ago.</p>
    % end
  </article>
</section>

%include footer
