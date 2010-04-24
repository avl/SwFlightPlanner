
<%inherit file="base.mako"/>

<script src="/MochiKit.js" type="text/javascript"></script>

<script type="text/javascript">
function loadfplan()
{	
}

addLoadEvent(loadmap);

</script>


<div>

<table class="bordered">
<tr>
<td>#</td>
<td title="Wind Direction/Wind Velocity (in degrees and knots, respectively)">W/V</td>
<td title="Outside Air Temperature">T</td>
<td title="Altitude/Flight Level (Altitude above mean sea level/flight level, e.g 4500ft or FL045)">Alt</td>
<td title="True Air Speed (the speed of the aircraft in relation to the air around it)">TAS</td>
<td title="True Track (the true direction the aircraft is flying, relative to ground)">TT</td>
<td title="Wind correction angle (the compensation due to wind needed to stay on the True Track. Negative means you have to aim left, positive to aim right)">wca</td>
<td title="Variation (How much to the right of the true north pole, the compass is pointing. Negative numbers means the compass points to the left of the true north pole)">var</td>
<td title="Deviation (How much to the right of the magnetic north, the aircraft compass will be pointing, while travelling in the direction of the true track)">dev</td>
<td title="Compass Heading (The heading that should be flown on the airplane compass to end up at the right place)">CH</td> 
</td>
%for cnt,wp in h.izip(h.count(),sorted(c.waypoints,key=lambda x:x.ordinal)):
<tr>
<td>
#${cnt}
</td>
<td colspan="9">
${wp.waypoint}
</td>
</tr>
%endfor
</table>	        
</div>
	