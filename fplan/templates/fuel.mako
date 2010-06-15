
<%inherit file="base.mako"/>

<script type="text/javascript">
function navigate_to(where)
{	
	function finish_nav()
	{				
		window.location.href=where;
	}
	finish_nav();
}
</script>
<div style="height:100%;width:100%;overflow:auto;">

<div id="sub-nav">
	<dl>
		<dt id="nav-map"><a onclick="navigate_to('${h.url_for(controller="flightplan",action="index")}')" href="#">Overview</a></dt>
		<dt id="nav-flightplan"><a onclick="navigate_to('${h.url_for(controller="flightplan",action="ats")}')" href="#">ATS-flightplan</a></dt>
		<dt id="nav-aircraft"><a onclick="navigate_to('${h.url_for(controller="flightplan",action="fuel")}')" href="#"><b>Fuel-plan</b></a></dt>
	</dl>
</div>

<h1>${c.trip}</h1>

%if len(c.all_aircraft)==0:
<a onclick="navigate_to('${h.url_for(controller="aircraft",action="index")}')" href="#"><b>You need to add an aircraft!</b></a>
%endif
%if len(c.all_aircraft)>0:
<form action="${h.url_for(controller="flightplan",action="select_aircraft")}" method="POST">
<select onchange="onchange_aircraft()" name="change_aircraft">
%for ac in c.all_aircraft:
<option ${'selected="1"' if c.ac and ac.aircraft==c.ac.aircraft else ''|n}>
${ac.aircraft}
</option>
%endfor
</select>
<input type="submit" name="save" value="Choose aircraft"/>
</form>
%endif

%if not c.acwarn:
<br/>
<h2>Legs</h2>
<table>
<tr>
<td>From</td><td>To</td><td>Seg</td><td>Distance</td><td>Time(min)</td><td>Total Time(min)</td>
<td>Fuel(L)</td>
<td>Total Fuel(L)</td>
</tr>
%for route in c.routes:
<tr>
<td>
${route.a.waypoint}</td><td> ${route.b.waypoint}
<td>${route.what}</td>
<td>${"%.1f"%(route.d,)}</td>
<td>${route.time}</td>
<td>${route.accum_time}</td>
<td>${"%.1f"%(route.fuel_burn,)}</td>
<td>${"%.1f"%(route.accum_fuel_burn,)}</td>
</td>

</tr>
%endfor
</table>
%endif

</div>

