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
        <dt id="nav-obstacles"><a onclick="navigate_to('${h.url_for(controller="flightplan",action="obstacles")}');return false;" href="#">Obstacles</a></dt>        
        <dt id="nav-enroutenotams"><a onclick="navigate_to('${h.url_for(controller="flightplan",action="enroutenotams")}');return false;" href="#">Notams on Route</a></dt>        
        <dt id="nav-minutemarkings"><a onclick="navigate_to('${h.url_for(controller="flightplan",action="minutemarkings")}');return false;" href="#"><b>Map Preparation</b></a></dt>        
    </dl>
</div>

<h1>${c.trip}</h1>
This screen helps you prepare your maps with marks for each minute, for exact navigation. ("Minutstreck", in Swedish) 
<table border="1" cellspacing="0" cellpadding="1">
<tr>
<th colspan="4"></th><th colspan="1">cm/minute</th><th></th>
</tr>
<tr>
<th>From</th><th></th><th>To</th><th>cruise GS (kt)</th><th>1:250000</th><th>Start time</th><th>marks</th>
</tr>
%for rt in c.route:
<tr>
<td><b>${rt.a.waypoint}</b></td><td>-</td><td><b>${rt.b.waypoint}</b></td><td>${"%.0f"%(rt.gs,) if rt.gs else "-"}</td>
<td>${h.minutemarking(rt.gs,250000)}</td>
<td>${"%02d:%02d:%02d"%(rt.depart_dt.hour,rt.depart_dt.minute,rt.depart_dt.second) if rt.depart_dt else "-"}</td>
<td>${rt.marks}</td>
</tr>
%endfor



</table>
