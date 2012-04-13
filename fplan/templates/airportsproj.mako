
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

<h1>Airport Projections</h1>

%if c.flash:
<b>${c.flash}</b><br/>
%endif
<div style="height:100%;width:100%;overflow:auto;">
<table>
<tr>
<td>Airport</td><td>Last updated</td><td>Current</td><td>Marks</td>
</tr>
%for work in c.worklist:
<tr ${'style="background-color:#ffc0c0"' if work['needwork'] else ""|n}}>
<td><a href="${work['url']}">${work['airport']}</a></td><td>${work['updated']}</td><td>${work['current']}</td>
<td>${len(work['marks'])},${work['needwork']}</td>
</tr>
%endfor

</table>

</div>



