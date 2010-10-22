
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
		<dt id="nav-map"><a onclick="navigate_to('${h.url_for(controller="flightplan",action="index")}');return false;" href="#">Overview</a></dt>
		<dt id="nav-flightplan"><a onclick="navigate_to('${h.url_for(controller="flightplan",action="ats")}');return false;" href="#">ATS-flightplan</a></dt>
		<dt id="nav-aircraft"><a onclick="navigate_to('${h.url_for(controller="flightplan",action="fuel")}');return false;" href="#"><b>Fuel-plan</b></a></dt>
		<dt id="nav-obstacles"><a onclick="navigate_to('${h.url_for(controller="flightplan",action="obstacles")}');return false;" href="#">Obstacles</a></dt>		
		<dt id="nav-enroutenotams"><a onclick="navigate_to('${h.url_for(controller="flightplan",action="enroutenotams")}');return false;" href="#">Notams on Route</a></dt>		
	</dl>
</div>

<h1>${c.trip}</h1>
%for close in c.closetoroute:
${close} <br/>
%endfor
%if c.sharing:
The owner of the trip must select an aircraft before fuel calcuations can be made.
%endif
%if not c.sharing:
%if len(c.all_aircraft)==0:
<a onclick="navigate_to('${h.url_for(controller="aircraft",action="index")}')" href="#"><b>You need to add an aircraft!</b></a>
%endif
%if len(c.all_aircraft)>0:
%if c.acwarn:
You must select an aircraft in order to calculate trip details!
%endif
<form action="${h.url_for(controller="flightplan",action="select_aircraft")}" method="POST">
<select name="change_aircraft">
<option>--------
</option>
%for ac in c.all_aircraft:
<option ${'selected="1"' if c.ac and ac.aircraft==c.ac.aircraft else ''|n}>
${ac.aircraft}
</option>
%endfor
</select>
<input type="hidden" name="prevaction" value="fuel"/>
<input type="submit" name="save" value="Choose aircraft" title="Select an aircraft using the dropdown-box just to the left of this button!"/>
</form>
%endif
%endif


%if not c.acwarn:
<br/>

<h2>Legs</h2>
<table>
<tr>
<td>From</td><td>To</td><td>Seg</td><td>Distance</td><td>Tot. Dist.</td>
<td>GS</td><td>Time(min)</td><td>Tot. Time(min)</td>
<td>Fuel(L)</td>
<td>Total Fuel(L)</td>
<td>Start Alt</td><td>End Alt</td><td>Rate</td>
</tr>
%for route in c.routes:

%if route.performance=="ok":
<tr>
%endif
%if route.performance!="ok":
<tr style="background:#ffe0e0">
%endif

<td>
${route.a.waypoint}</td><td> ${route.b.waypoint}
<td>${route.what}</td>
<td>${"%.1f"%(route.d,)}</td>
<td>${"%.1f"%(route.total_d,)}</td>
<td>${"%.0f"%(route.gs,)}</td>
<td>${h.timefmt(route.time)}</td>
<td>${h.timefmt(route.accum_time)}</td>
<td>${"%.1f"%(route.fuel_burn,)}</td>
<td>${"%.1f"%(route.accum_fuel_burn,)}</td>
<td>${"%.0f"%(route.startalt+0.01,)}</td>
<td>${"%.0f"%(route.endalt+0.01,)}</td>
<td>${"%.0f"%(route.altrate+0.01,)}fpm</td>
</td>

</tr>
%endfor
</table>

<br/>

%if c.performance=="notok":
<span style="background:#ffe0e0">
The cruise climb/cruise descent values entered for the aircraft are not enough to reach the desired altitude in the legs colored light-red/pink above.
</span>
%endif

%endif
<div>
<br/>
%if not c.acwarn:

<b>Fuel analysis</b><br/>
<table>
<tr><td>Start:</td><td>${"%.1f"%(c.startfuel,)}L</td></tr>
<tr 
%if c.endfuel<0:
style="background-color:#ff8080"
%endif
><td>End:</td><td>${"%.1f"%(c.endfuel,)}L</td></tr>
</table>

WARNING! This information may only be used for quickly checking possible flights for plausibility.<br/>
<b>BEFORE FLYING, YOU MUST DO YOUR OWN CALCULATIONS!</b>
%endif
</div>
</div>

