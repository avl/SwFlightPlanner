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
		<dt id="nav-map"><a onclick="navigate_to('${h.url_for(controller="flightplan",action="index")}');return false;" href="#">Overview</a></dt>
		<dt id="nav-flightplan"><a onclick="navigate_to('${h.url_for(controller="flightplan",action="ats")}');return false;" href="#">ATS-flightplan</a></dt>
		<dt id="nav-aircraft"><a onclick="navigate_to('${h.url_for(controller="flightplan",action="fuel")}');return false;" href="#">Fuel-plan</a></dt>
		<dt id="nav-obstacles"><a onclick="navigate_to('${h.url_for(controller="flightplan",action="obstacles")}');return false;" href="#"><b>Obstacles</b></a></dt>		
		<dt id="nav-enroutenotams"><a onclick="navigate_to('${h.url_for(controller="flightplan",action="enroutenotams")}');return false;" href="#">Notams on Route</a></dt>		
        <dt id="nav-minutemarkings"><a onclick="navigate_to('${h.url_for(controller="flightplan",action="minutemarkings")}');return false;" href="#">Map Preparation</a></dt>        
	</dl>
</div>

<h1>${c.trip}</h1>
%if len(c.items)>0:

<table>
<tr>
<td><b>Your position</b></td>
<td><b>Bearing to obst.</b></td>
<td><b>Warning</b></td>
<td><b>Obstacle/Terrain elevation</b></td>
<td><b>Planned flying altitude</b></td>
</tr>

%for waypoint,items in c.items:
%if False:
<tr><td>
<h2>${waypoint}</h2>
</td>
</tr>
%endif

%for item in items:
<tr
%if item['color']:
style="background-color:${item['color']}"
%endif
>
<td>
${item['routepointdescr']}
</td>
<td>
%if item['dist']<0.1:
Near flight path
%endif
%if not (item['dist']<0.1):
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
${"%.0f"%(item['closestalt'],) if item['closestalt']!=None else ''}
</td>
</tr>
%endfor
%endfor

</table>
%endif
%if len(c.items)==0:
There are no obstacles close to the flightpath (vertically and horizontally).
%endif
</div>


