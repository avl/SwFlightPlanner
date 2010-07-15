<%inherit file="base.mako"/>
<script type="text/javascript">
function navigate_to(where)
{	
	window.location.href=where;
}
</script>

<div id="obstaclecontent" style="height:100%;width:100%;overflow:auto;">

<div id="sub-nav">
	<dl>
		<dt id="nav-map"><a onclick="navigate_to('${h.url_for(controller="flightplan",action="index")}')" href="#">Overview</a></dt>
		<dt id="nav-flightplan"><a onclick="navigate_to('${h.url_for(controller="flightplan",action="ats")}')" href="#">ATS-flightplan</a></dt>
		<dt id="nav-aircraft"><a onclick="navigate_to('${h.url_for(controller="flightplan",action="fuel")}')" href="#">Fuel-plan</a></dt>
		<dt id="nav-aircraft"><a onclick="navigate_to('${h.url_for(controller="flightplan",action="obstacles")}')" href="#"><b>Obstacles</b></a></dt>		
	</dl>
</div>

<h1>${c.trip}</h1>

%for waypoint,items in c.items:

${waypoint}<br/>

<table>
<tr>
<td>Where</td>
<td>Direction</td>
<td>Warning</td>
<td>Obstacle/Terrain elevation</td>
<td>Planned flying altitude</td>
</tr>
%for item in items:
<tr
%if item['color']:
style="background-color:${item['color']}"
%endif
>
<td>
${"%.0f"%(item['along_nm'],)}nm from ${waypoint}
</td>
<td>
%if item['dist']<0.01:
Under flight path
%endif
%if item['dist']>=0.01:
${"%.1f"%(item['dist'],)}nm ${"%03.0f"%(item['bearing'],)} deg
%endif
</td>
<td>
${item['name']}
</td>
<td>
${"%s"%(item['elev'],)}
</td>
<td>
${"%.0f"%(item['closestalt'],)}
</td>
</tr>
%endfor
</table>
%endfor

%if c.endwaypoint:
${c.endwaypoint}<br/>
%endif
%if c.endwaypoint==None:
There are no obstacles close to the flightpath (vertically and horizontally).
%endif
</div>


