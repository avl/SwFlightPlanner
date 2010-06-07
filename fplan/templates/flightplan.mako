
<%inherit file="base.mako"/>

<script src="/MochiKit.js" type="text/javascript"></script>
<script src="/fpmain.js" type="text/javascript"></script>

<script type="text/javascript">

tripname='${c.tripname}';
searchairporturl='${h.url_for(controller="flightplan",action="search")}';
fetchweatherurl='${h.url_for(controller="flightplan",action="weather")}';
saveurl='${h.url_for(controller="flightplan",action="save")}';
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
	fpaddwaypoint('${wp.pos}','${wp.waypoint}',rowdata);

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

<form id="flightplanform" method="POST" action="${h.url_for(controller="flightplan",action="save")}">
<div class="bordered" id="nowaypointsyet"
%if len(c.waypoints)!=0:
	style="display:none"
%endif
>
You have no waypoints yet! Go to the map and click to add some!
</div>

<table id="flightplantable" class="bordered" cellspacing="0" borders="0">
<tr>
%for col in c.cols:
<td title="${col['desc']+' '+col['extra']}">${col['short']}</td>
%endfor 
</td>
</tr>
</table>
<p>
<button onclick="fetch_winds();return false;">Fetch Wind Information</button><br/>
Total distance: <input type="text" readonly="1" value="${"%.0f"%(c.totdist,)}" size="4"> NM.<br/>
Total time: <input id="tottime" type="text" readonly="1" value="" size="4">.<br/>
</p>
</form>


        
</div>
	
	
	
