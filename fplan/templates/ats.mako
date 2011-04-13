
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
		<dt id="nav-map"><a onclick="navigate_to('${h.url_for(controller="flightplan",action="index")}');return false;" href="#">Overview</a></dt>
		<dt id="nav-flightplan"><a onclick="navigate_to('${h.url_for(controller="flightplan",action="ats")}');return false;" href="#"><b>ATS-flightplan</b></a></dt>
		<dt id="nav-aircraft"><a onclick="navigate_to('${h.url_for(controller="flightplan",action="fuel")}');return false;" href="#">Fuel-plan</a></dt>
		<dt id="nav-obstacles"><a onclick="navigate_to('${h.url_for(controller="flightplan",action="obstacles")}');return false;" href="#">Obstacles</a></dt>		
		<dt id="nav-enroutenotams"><a onclick="navigate_to('${h.url_for(controller="flightplan",action="enroutenotams")}');return false;" href="#">Notams on Route</a></dt>		
	</dl>
</div>

<h1>${c.trip}</h1>

%for at in c.atstrips:
%if len(c.atstrips)>1:
<br/>
<h2>${at['wps'][0]['name']} - ${at['wps'][-1]['name']}</h2>
%endif
<br/>
<h2>Waypoints</h2>
%for w in at['wps']:

<p>
<b>${w['name']}</b>:${w['symbolicpos']} (exact: ${w['exactpos']}) 
</p>

%endfor
<br/>
<h2>ATS-format</h2>
<p>
(An entire ATS-flightplan. Select 'import' at www.aro.lfv.se, then paste this flightplan into the text-area.)
</p>
<div>
%if at['atsfplan']:
<hr/>
<pre>
${at['atsfplan']}
</pre>
<hr/>
%endif
</div>

<h2>Raw Coordinates</h2>
<p>
(Same coordinates as above, but in the format of LFV point sequences)
</p>
<div>
<span>	
${" - ".join([w['exactpos'] for w in at['wps']])}
</span
</div>


<h2>Summary of Airspaces flown</h2>
<p>Number of spaces: ${len(at['spacesummary'])}</p>
<table>
<tr>
<th>Name</th><th>Floor</th><th>Ceiling</th>
</tr>
%for name,floor,ceiling in sorted(at['spacesummary']):
<tr>
<td>${name}</td><td>${floor}</td><td>${ceiling}</td>
</tr>
%endfor
</table>

%endfor

</div>



