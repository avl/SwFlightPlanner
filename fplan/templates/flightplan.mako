
<%inherit file="base.mako"/>

<script src="/MochiKit.js" type="text/javascript"></script>

<script type="text/javascript">
function loadfplan()
{	
}
function navigate_to(where)
{
	function finish_nav()
	{
		location.replace=where;
	}
	finish_nav();
}
addLoadEvent(loadfplan);

</script>


<div>

<form id="flightplanform" method="POST" action="${h.url_for(controller="flightplan",action="save")}">
<table class="bordered" cellspacing="0" borders="0">
<tr>
<td>#</td>
<td title="Wind Direction (in degrees)">W</td>
<td title="Wind Velocity (in knots)">V</td>
<td title="Outside Air Temperature">T</td>
<td title="Altitude/Flight Level (Altitude above mean sea level/flight level, e.g 4500ft or FL045)">Alt</td>
<td title="True Air Speed (the speed of the aircraft in relation to the air around it)">TAS</td>
<td title="True Track (the true direction the aircraft is flying, relative to ground)">TT</td>
<td title="Wind correction angle (the compensation due to wind needed to stay on the True Track. Negative means you have to aim left, positive to aim right)">wca</td>
<td title="Variation (How much to the right of the true north pole, the compass is pointing. Negative numbers means the compass points to the left of the true north pole)">var</td>
<td title="Deviation (How much to the right of the magnetic north, the aircraft compass will be pointing, while travelling in the direction of the true track)">dev</td>
<td title="Compass Heading (The heading that should be flown on the airplane compass to end up at the right place)">CH</td> 
<td title="Distance (in nautical miles)">D</td> 
</td>
%for cnt,wp in h.izip(h.count(),sorted(c.waypoints,key=lambda x:x.ordinal)):
<tr>
<td>
#${cnt}
</td>
<td colspan="11">
${wp.waypoint}
</td>
</tr>
%if cnt!=len(c.waypoints)-1:
<tr>
<td></td>
<td><input size="3" title="Wind Direction" type="text" name="row${cnt}winddir" value="${c.get('winddir',c.waypoints[cnt],c.waypoints[cnt+1])}"/></td>
<td><input size="2" title="Wind Velocity" type="text" name="row${cnt}windvel" value="${c.get('windvel',c.waypoints[cnt],c.waypoints[cnt+1])}"/></td>
<td><input size="2" type="text" name="row${cnt}temp" value="${c.get('temp',c.waypoints[cnt],c.waypoints[cnt+1])}"/></td>
<td><input size="4" type="text" name="row${cnt}alt" value="${c.get('alt',c.waypoints[cnt],c.waypoints[cnt+1])}"/></td>
<td><input size="3" type="text" name="row${cnt}tas" value="${c.get('tas',c.waypoints[cnt],c.waypoints[cnt+1])}"/></td>
<td><input size="3" type="text" name="row${cnt}tt" value="${c.get('tt',c.waypoints[cnt],c.waypoints[cnt+1])}"/></td>
<td><input size="2" type="text" name="row${cnt}wca" value="${c.get('wca',c.waypoints[cnt],c.waypoints[cnt+1])}"/></td>
<td><input size="2" type="text" name="row${cnt}var" value="${c.get('var',c.waypoints[cnt],c.waypoints[cnt+1])}"/></td>
<td><input size="2" type="text" name="row${cnt}dev" value="${c.get('dev',c.waypoints[cnt],c.waypoints[cnt+1])}"/></td>
<td><input size="3" type="text" name="row${cnt}ch" value="${c.get('ch',c.waypoints[cnt],c.waypoints[cnt+1])}"/></td>
<td><input size="3" type="text" name="row${cnt}dist" value="${c.get('dist',c.waypoints[cnt],c.waypoints[cnt+1])}"/></td>
</tr>
%endif
%endfor
</table>
</form>
	        
</div>
	