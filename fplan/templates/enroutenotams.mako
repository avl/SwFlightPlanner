<%inherit file="base.mako"/>

<script type="text/javascript">
function navigate_to(where)
{
	window.location.href=where;
}
</script>

<div id="enroutenotams" style="height:100%;width:100%;overflow:auto;">

<div id="sub-nav">
	<dl>
		<dt id="nav-map"><a onclick="navigate_to('${h.url_for(controller="flightplan",action="index")}');return false;" href="#">Overview</a></dt>
		<dt id="nav-flightplan"><a onclick="navigate_to('${h.url_for(controller="flightplan",action="ats")}');return false;" href="#">ATS-flightplan</a></dt>
		<dt id="nav-aircraft"><a onclick="navigate_to('${h.url_for(controller="flightplan",action="fuel")}');return false;" href="#">Fuel-plan</a></dt>
		<dt id="nav-obstacles"><a onclick="navigate_to('${h.url_for(controller="flightplan",action="obstacles")}');return false;" href="#">Obstacles</a></dt>		
		<dt id="nav-enroutenotams"><a onclick="navigate_to('${h.url_for(controller="flightplan",action="enroutenotams")}');return false;" href="#"><b>Notams on Route</b></a></dt>		
	</dl>
</div>

<h1>Notams on Route ${c.route[0].a.waypoint} - ${c.route[-1].b.waypoint}</h1>
<h2>${c.route[0].a.waypoint}</h2>
%for rt in c.route:
<ul>
%for notam,val in rt.notampoints.items():
<li>
${notam}

<u>
<a href="${h.url_for(controller="notam",action="show_ctx",backlink=c.thislink,notam=val.get('notam_ordinal','none'),line=val.get('notam_line','none'))}#notam">Link</a>
</u>

</li>
%endfor
</ul>
<h2>${rt.b.waypoint}</h2>
%endfor

</div>

