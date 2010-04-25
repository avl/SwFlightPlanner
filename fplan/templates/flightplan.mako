
<%inherit file="base.mako"/>

<script src="/MochiKit.js" type="text/javascript"></script>
<script src="/fpmain.js" type="text/javascript"></script>

<script type="text/javascript">
fpcolnum=${len(c.cols)};
fpcolshort=[];
fpcolname=[];
fpcoldesc=[];
fpcolwidth=[];
function loadfplan()
{
%for col in c.cols:
	fpcolshort.push('${col["short"}');
	fpcoldesc.push('${col["desc"}');
	fpcolhuman.push('${col["name"}');
	fpcolwidth.push('${col["width"}');
%endfor
	
%for cnt,wp in h.izip(h.count(),sorted(c.waypoints,key=lambda x:x.ordinal)):

	var rowdata=[
	%for what in c.cols:
	'${c.get(what['short'],c.waypoints[cnt],c.waypoints[cnt+1])}',
	%endfor
	''];
	fpaddwaypoint(rowdata);

%endfor

}

function navigate_to(where)
{	
	function finish_nav()
	{				
		window.location.href=where;
	}
	finish_nav();
}

addLoadEvent(loadfplan);

</script>


<div>

<form id="flightplanform" method="POST" action="${h.url_for(controller="flightplan",action="save")}">
<div class="bordered" id="nowaypointsyet"
%if len(c.waypoints)!=0:
	style="display:none"
%endif
>
You have no waypoints yet! Go to the map and click to add some, or click the "add" button below!
</div>

<table id="flightplantable" class="bordered" cellspacing="0" borders="0">
<tr>
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
</tr>
</table>
<button id="addbutton" onclick="fpaddwaypoint(null)">Add</button>
</form>



	        
</div>
	