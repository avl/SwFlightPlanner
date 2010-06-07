
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
		<dt id="nav-map"><a onclick="navigate_to('${h.url_for(controller="flightplan",action="index")}')" href="#">Overview</a></dt>
		<dt id="nav-flightplan"><a onclick="navigate_to('${h.url_for(controller="flightplan",action="ats")}')" href="#">ATS-flightplan</a></dt>
		<dt id="nav-aircraft"><a onclick="navigate_to('${h.url_for(controller="flightplan",action="fuel")}')" href="#"><b>Fuel-plan</b></a></dt>
	</dl>
</div>

<h1>${c.trip}</h1>

<br/>
<h2>Legs</h2>
<table>
%for route in c.routes:
<tr>
<td>
${route.start_name} - ${route.end_name}
</td>
</tr>
%endfor
</table>

</div>

