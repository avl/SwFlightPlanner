
<%inherit file="base.mako"/>

<script src="/MochiKit.js" type="text/javascript"></script>

<script type="text/javascript">

function loadrecordings()
{
}

addLoadEvent(loadrecordings);

</script>

<div style="height:100%;width:100%;overflow:auto;">
<h1>
Recordings
</h1>

%if c.flash:
<p><span style="background-color:#80ff80;font-size:14px">
${c.flash}
</span></p><br/>
%endif

<form action="${h.url_for(controller="recordings",action="load")}" method="POST">

<table border="1">
<tr>
<td>
From
</td>
<td>
To
</td>
<td>
Distance (NM)
</td>
<td>
Time
</td>
<td>
Start (Z)
</td>
<td>
End (Z)
</td>
<td>
</td>
</tr>
%for trip in c.trips:
<tr>
<td>${trip.depdescr}</td>
<td>${trip.destdescr}</td>
<td>${"%.1f"%(trip.distance,)}</td>
<td>${h.timefmt(trip.duration/1000.0/3600.0)}</td>
<td>${trip.start.strftime("%Y-%m-%d %H:%MZ")}</td>
<td>${trip.end.strftime("%Y-%m-%d %H:%MZ")}</td>
<td>
<input type="submit" name="view_${h.utcdatetime2stamp(trip.start)}"/>	
</td>
</tr>
%endfor
</table>
</form>
</div>
	

