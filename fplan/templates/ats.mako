
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

<h1>${c.trip}</h1>
<br/>
<h2>Waypoints</h2>
%for w in c.waypoints:

<p>
<b>${w['name']}</b>:${w['pos']} 
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
<span style="background:#d0d0d0;border: 1px #808080 solid">	
%for w in c.waypoints:
DCT ${w['pos']} \
%endfor
<br/>
</span>
<div>
Back to regular <u><a href="${h.url_for(controller="flightplan",action="index")}">flightplan</a></u>.
</div>
</div>
