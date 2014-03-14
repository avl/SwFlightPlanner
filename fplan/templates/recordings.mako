
<%inherit file="base.mako"/>

<script src="/MochiKit.js" type="text/javascript"></script>

<script type="text/javascript">

function loadrecordings()
{
}
function navigate_to(where)
{
	window.location.href=where;	
}

addLoadEvent(loadrecordings);

</script>

<div style="height:100%;width:100%;overflow:auto;">
<h1>
Recordings
</h1>

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
Download
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
<td><a href="${h.url_for(controller='recordings',action='kml',starttime=str(h.utcdatetime2stamp(trip.start)))}"><u>KML</u></a></td>
<td><input type="submit" value="View" name="view_${h.utcdatetime2stamp(trip.start)}"/></td>
</tr>
%endfor
</table>
</form>
</div>
	

