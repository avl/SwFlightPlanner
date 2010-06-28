
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
		<dt id="nav-flightplan"><a onclick="navigate_to('${h.url_for(controller="flightplan",action="ats")}')" href="#"><b>ATS-flightplan</b></a></dt>
		<dt id="nav-aircraft"><a onclick="navigate_to('${h.url_for(controller="flightplan",action="fuel")}')" href="#">Fuel-plan</a></dt>
	</dl>
</div>

<h1>${c.trip}</h1>

<br/>
<h2>Waypoints</h2>
%for w in c.waypoints:

<p>
<b>${w['name']}</b>:${w['pos']} (exact: ${w['exactpos']}) 
</p>

%endfor
<br/>
<h2>ATS-format</h2>
<p>
(Same coordinates as above, but in format suitable for copy-pasting into the
www.aro.lfv.se web-application.)
</p>
<br/>
<div>

%if len(c.waypoints):
<table>
<tr>
<td>
Departure</td><td> <span style="background:#d0d0d0;border: 1px #808080 solid">	
${c.waypoints[0]['pos']} ${c.waypoints[0]['name']}
</span></td></tr><tr><td>
Destination:</td><td> <span style="background:#d0d0d0;border: 1px #808080 solid">	
${c.waypoints[-1]['pos']} ${c.waypoints[-1]['name']}
</span></td>
</tr>
</table>
%endif
<br/>
<table>
<tr>
<td>Route</td> <td><span style="background:#d0d0d0;border: 1px #808080 solid">	
%for w in c.waypoints:
DCT ${w['pos']} \
%endfor
</td>
</tr>
</table>
<br/>
</span>
</div>

<br/>
<h2>More exact format</h2>
<p>
(Same coordinates as above, but in the format of LFV point sequences)
</p>
<div>
<span>	
${" - ".join([w['exactpos'] for w in c.waypoints])}
</span
</div>


</div>

