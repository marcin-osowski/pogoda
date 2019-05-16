   <footer>
     2019, Katarzyna Osowska, Marcin Osowski
     % if defined('latency'):
         <br> Backend latency: {{ '%.2f' % latency.total_seconds() }}s
     % end
   </footer>

</body>
</html>
