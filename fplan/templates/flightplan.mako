
<%inherit file="base.mako"/>

<script src="/MochiKit.js" type="text/javascript"></script>
<script src="/fpmain.js" type="text/javascript"></script>

<script type="text/javascript">

tripname='${h.jsescape(c.tripname)|n}';
searchairporturl='${h.url_for(controller="flightplan",action="search")}';
fetchweatherurl='${h.url_for(controller="flightplan",action="weather")}';
optimizeurl='${h.url_for(controller="flightplan",action="optimize")}';
saveurl='${h.url_for(controller="flightplan",action="save")}';
fetchacurl='${h.url_for(controller="flightplan",action="fetchac")}';
printableurl='${h.url_for(controller="flightplan",action="printable",trip=c.tripname)}';
fpcolnum=${str(len(c.cols))};
fpcolshort=[];
fpcoldesc=[];
fpcolextra=[];
fpcolwidth=[];
advanced_model=${1 if c.advanced_model else 0};
%if c.stay:
firstwaypointid=${str(c.stay.waypoint_id)};
%endif
%if not c.stay:
firstwaypointid=null;
%endif

fpid=[];
num_rows=${str(len(c.waypoints))};
function loadfplan()
{
    force_refresh_on_back_button('${h.url_for(controller="flightplan",action="index")}');

%for col in c.cols:
	fpcolshort.push('${col["short"]}');
	fpcoldesc.push('${col["desc"]}');
	fpcolextra.push('${col["extra"]}');
	fpcolwidth.push('${col["width"]}');
%endfor
	
%for cnt,wp in h.izip(h.count(),sorted(c.waypoints,key=lambda x:x.ordering)):
    fpid.push(${wp.id});
	var rowdata=[

	%if cnt!=len(c.waypoints)-1:
	%for whati,what in enumerate(c.cols):
	'${c.get(what['short'],c.waypoints[cnt],c.waypoints[cnt+1])}'${',' if whati!=len(c.cols)-1 else ''}\
	%endfor
	%endif
	];	
	var stay=[];

	%if wp.stay:
	stay=[
	    '${h.jsescape(wp.stay.date_of_flight)|n}','${h.jsescape(wp.stay.departure_time)|n}',
	    '${wp.stay.fuelstr()}',
	    '${str(int(wp.stay.nr_persons)) if wp.stay.nr_persons else ""|n}'
	];
	%endif
	
	fpaddwaypoint(${cnt},'${h.jsescape(wp.pos)|n}','${h.jsescape(wp.waypoint)|n}',rowdata,'${h.jsescape(wp.altitude)|n}',stay);

%endfor

	fpmain_init();
    var der='${h.jsescape(c.derived_data)|n}';

    update_fields(evalJSON(der));

}

function navigate_to(where)
{	
	function finish_nav()
	{					    
		window.location.href=where;
	}
	save_data(finish_nav);
}

addLoadEvent(loadfplan);

</script>

<div style="height:100%;width:100%;overflow:auto;">


<div id="sub-nav">
	<dl>
		<dt id="nav-map"><a onclick="navigate_to('${h.url_for(controller="flightplan",action="index")}');return false;" href="#"><b>Overview</b></a></dt>
		<dt id="nav-flightplan"><a onclick="navigate_to('${h.url_for(controller="flightplan",action="ats")}');return false;" href="#">ATS-flightplan</a></dt>
		<dt id="nav-aircraft"><a onclick="navigate_to('${h.url_for(controller="flightplan",action="fuel")}');return false;" href="#">Fuel-plan</a></dt>
		<dt id="nav-obstacles"><a onclick="navigate_to('${h.url_for(controller="flightplan",action="obstacles")}');return false;" href="#">Obstacles</a></dt>		
		<dt id="nav-enroutenotams"><a onclick="navigate_to('${h.url_for(controller="flightplan",action="enroutenotams")}');return false;" href="#">Notams on Route</a></dt>		
        <dt id="nav-minutemarkings"><a onclick="navigate_to('${h.url_for(controller="flightplan",action="minutemarkings")}');return false;" href="#">Map Preparation</a></dt>        
	</dl>
</div>


<div id="progmessage" class="progress-popup">
</div>

<h1>
${c.tripname}
</h1>

%if c.flash:
<div style="background:#ffb0b0">
<b>${c.flash}</b><br/>
</div>
%endif


%if not c.sharing:
%if len(c.all_aircraft)==0:
<a onclick="navigate_to('${h.url_for(controller="aircraft",action="index")}')" href="#"><b>Click here to add an aircraft!</b></a>
%endif
%if len(c.all_aircraft)>0:
<form action="${h.url_for(controller="flightplan",action="select_aircraft")}" method="POST" id="chooseaircraftform">
<select name="change_aircraft" id="change_aircraft">
<option>--------
</option>
%for ac in c.all_aircraft:
<option ${'selected="1"' if c.ac and ac.aircraft==c.ac.aircraft else ''|n}>
${ac.aircraft}
</option>
%endfor
</select>
<input type="hidden" name="prevaction" value="index"/>
<input type="submit" onclick="choose_aircraft();return false;" name="save" value="Choose aircraft" title="Select an aircraft using the dropdown-box just to the left of this button!"/>

</form>
<br/>
%endif
%endif


%if len(c.waypoints)==0:
<div class="bordered">
You have no waypoints yet! Go to the <a href="${h.url_for(controller="mapview",action="index")}"><u>map</u></a> and click the 'Add' button in the upper right part of the screen. Then click in the map to add waypoints.
</div>
%endif
%if len(c.waypoints)!=0:
<form id="flightplanform" method="POST" action="${h.url_for(controller="flightplan",action="save")}">

%if c.stay:
<table>
<tr><td>Date of Flight: </td><td><input size="10" type="text" onchange="on_update_all();" 
    name="date_of_flight_${c.stay.waypoint_id}" id="date_of_flight_${c.stay.waypoint_id}" value="${c.stay.date_of_flight}"/>(YYYY-MM-DD)</td></tr>
<tr><td>Estimated Start Time (UTC): </td><td><input size="5" type="text" onchange="on_update_all();" 
    name="departure_time_${c.stay.waypoint_id}" id="departure_time_${c.stay.waypoint_id}" value="${c.stay.departure_time}"/>(HH:MM)</td></tr>
<tr><td>Fuel at takeoff: </td><td><input size="4" type="text" onchange="on_update_all();" 
    name="fuel_${c.stay.waypoint_id}" id="fuel_${c.stay.waypoint_id}" value="${c.stay.fuelstr()}"/>(L)</td></tr>
<tr><td>Number of persons on board: </td><td><input size="4" type="text" onchange="makedirty();" 
    name="persons_${c.stay.waypoint_id}" id="persons_${c.stay.waypoint_id}" value="${c.stay.nr_persons}"/></td></tr>
<tr><td>Name of Commander: </td><td><input size="10" type="text" onchange="on_update_all();" 
    name="realname" id="realname" value="${c.realname}"/></td></tr>
</table>
%endif
<br/>

<table id="flightplantable" class="bordered" cellspacing="0" borders="0">
<tr>
%for col in c.cols:
<td title="${col['desc']+' '+col['extra']}">${col['short']}</td>
%endfor 
</td>
</tr>
</table>
<button title="Fetch wind-information from the low-level forecast provided by LFV" onclick="fetch_winds();return false;">Fetch Wind Information</button>
<button title="Reset wind-information - set all wind to 0." onclick="reset_winds();return false;">Reset Wind</button>
<button title="Calculate optimal altitudes from a fuel point of view." onclick="optimize_alts();return false;">Optimize</button>

%if False and len(c.all_aircraft):
<button onclick="fetch_acparams();return false;">Fetch Values from Aircraft</button>
%endif
<br/>
Total distance: <input type="text" readonly="1" value="${"%.0f"%(c.totdist,)}" size="4"> NM.<br/>
Total time (enroute): <input id="tottime" type="text" readonly="1" value="" size="4"> (including time for climb/descent).<br/>
Total fuel consumption: <input id="totfuel" type="text" readonly="1" value="" size="4">L (including fuel for climb/descent).<br/>
</form>
%endif
<br/>
<h2>Printable version</h2>
<span id="printablelink">
<a href="${h.url_for(controller="flightplan",action="printable",trip=c.tripname)}"><u>Printable</u></a><br/>
</span>
<h2>Download to GPS:</h2>
Garmin <a href="${h.url_for(controller='flightplan',action='gpx',tripname=c.tripname)}"><u>GPX Format</u></a>.<br/>
<!--TomTom <a href="${h.url_for(controller='flightplan',action='itn',tripname=c.tripname)}">ITN Format</a>.<br/>-->

</div>
	
	
	
