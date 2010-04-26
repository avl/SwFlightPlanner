
<%inherit file="base.mako"/>

<script src="/MochiKit.js" type="text/javascript"></script>
<script src="/fpmain.js" type="text/javascript"></script>

<script type="text/javascript">
fpcolnum=${len(c.cols)};
fpcolshort=[];
fpcoldesc=[];
fpcolextra=[];
fpcolwidth=[];
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
	'${c.get(what['short'],c.waypoints[cnt-1],c.waypoints[cnt+1])}'${',' if whati!=len(c.cols)-1 else ''}\
	%endfor
	%endif
	];	
	fpaddwaypoint('${wp.pos}','${wp.waypoint}',rowdata);

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


<div style="height:100%;width:100%;overflow:auto;">

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
%for col in c.cols:
<td title="${col['desc']+' '+col['extra']}">${col['short']}</td>
%endfor 
</td>
</tr>
</table>
<button id="addbutton" onclick="fpaddwaypoint(null)">Add</button>
</form>



	        
</div>
	