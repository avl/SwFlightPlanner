
<%inherit file="base.mako"/>

<script src="/MochiKit.js" type="text/javascript"></script>
<script src="/fpmain.js" type="text/javascript"></script>
<script src="/lib.js" type="text/javascript"></script>

<script type="text/javascript">

tripname='${h.jsescape(c.tripname)|n}';
searchairporturl='${h.url_for(controller="flightplan",action="search")}';
fetchweatherurl='${h.url_for(controller="flightplan",action="weather")}';
saveurl='${h.url_for(controller="flightplan",action="save")}';
fetchacurl='${h.url_for(controller="flightplan",action="fetchac")}';
fpcolnum=${len(c.cols)};
fpcolshort=[];
fpcoldesc=[];
fpcolextra=[];
fpcolwidth=[];
num_rows=${len(c.waypoints)};
function loadfplan()
{
%for col in c.cols:
	fpcolshort.push('${col["short"]}');
	fpcoldesc.push('${col["desc"]}');
	fpcolextra.push('${col["extra"]}');
	fpcolwidth.push('${col["width"]}');
%endfor
	
%for cnt,wp in h.izip(h.count(),sorted(c.waypoints,key=lambda x:x.ordinal)):

	var rowdata=[
	%if cnt!=len(c.waypoints)-1:
	%for whati,what in h.izip(h.count(),c.cols):
	'${c.get(what['short'],c.waypoints[cnt],c.waypoints[cnt+1])}'${',' if whati!=len(c.cols)-1 else ''}\
	%endfor
	%endif
	];	
	fpaddwaypoint('${h.jsescape(wp.pos)|n}','${h.jsescape(wp.waypoint)|n}',rowdata);

%endfor

	fpmain_init();
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
		<dt id="nav-map"><a onclick="navigate_to('${h.url_for(controller="flightplan",action="index")}')" href="#"><b>Overview</b></a></dt>
		<dt id="nav-flightplan"><a onclick="navigate_to('${h.url_for(controller="flightplan",action="ats")}')" href="#">ATS-flightplan</a></dt>
		<dt id="nav-aircraft"><a onclick="navigate_to('${h.url_for(controller="flightplan",action="fuel")}')" href="#">Fuel-plan</a></dt>
	</dl>
</div>

<h1>
${c.tripname}
</h1>

%if len(c.waypoints)==0:
<div class="bordered">
You have no waypoints yet! Go to the <a href="${h.url_for(controller="mapview",action="index")}"><u>map</u></a> and click the 'Add' button in the upper right part of the screen. Then click in the map to add waypoints.
</div>
%endif
%if len(c.waypoints)!=0:
<form id="flightplanform" method="POST" action="${h.url_for(controller="flightplan",action="save")}">
%if False:
%if len(c.all_aircraft):
Aircraft: <select id="curaircraft" name="aircraft">
%for ac in c.all_aircraft:
<option ${'selected="1"' if ac.aircraft==c.acname else ''|n}>
${ac.aircraft}
</option>
%endfor
</select><br/>
%endif
%endif

<table id="flightplantable" class="bordered" cellspacing="0" borders="0">
<tr>
%for col in c.cols:
<td title="${col['desc']+' '+col['extra']}">${col['short']}</td>
%endfor 
</td>
</tr>
</table>
<button onclick="fetch_winds();return false;">Fetch Wind Information</button>

%if False and len(c.all_aircraft):
<button onclick="fetch_acparams();return false;">Fetch Values from Aircraft</button>
%endif
<br/>
Total distance: <input type="text" readonly="1" value="${"%.0f"%(c.totdist,)}" size="4"> NM.<br/>
Total time: <input id="tottime" type="text" readonly="1" value="" size="4"> (not counting time for climb).<br/>
%if False and len(c.all_aircraft)==0:
<a href="#" onclick="navigate_to('${h.url_for(controller="aircraft",action="index")}')" ><u>Add</u> an aircraft to use on this trip.</a><br/>
%endif
</form>
%endif


        
</div>
	
	
	
