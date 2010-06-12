
<%inherit file="base.mako"/>

<script src="/MochiKit.js" type="text/javascript"></script>
<script src="/aircraft.js" type="text/javascript"></script>

<script type="text/javascript">

function loadaircraft()
{
}

function navigate_to(where)
{	
    var nav=document.getElementById('navigate_to');
    nav.value=where;
    var acf=document.getElementById('acform');
    acf.submit();
}
function onchange_aircraft()
{
    var acf=document.getElementById('acform');
    acf.submit();
}

addLoadEvent(loadaircraft);

</script>

<div style="height:100%;width:100%;overflow:auto;">
<h1>
Aircraft
</h1>
<form id="acform" action="${h.url_for(controller="aircraft",action="save")}" method="POST">
%if len(c.all_aircraft):
<select onchange="onchange_aircraft()" name="change_aircraft">
%for ac in c.all_aircraft:
<option ${'selected="1"' if ac.aircraft==c.ac.aircraft else ''|n}>
${ac.aircraft}
</option>
%endfor
</select>
%endif
<input type="submit" name="add_button" value="Add aircraft"/>
%if c.ac:
<input type="submit" name="del_button" value="Delete aircraft"/>
<table>
<tr>
<td>Registration/name:</td><td><input type="hidden" name="orig_aircraft" value="${c.ac.aircraft}" />
<input type="text" name="aircraft" value="${c.ac.aircraft}" /></td>
</tr>
<tr>
<td>Cruise speed:</td><td><input type="text" name="cruise_speed" value="${c.ac.cruise_speed}" />kt</td>
</tr>
<tr>
<td>Cruise fuel burn:</td><td><input type="text" name="cruise_burn" value="${c.ac.cruise_burn}" />L/h</td>
</tr>
<tr>
<td>Cruise climb speed:</td><td><input type="text" name="climb_speed" value="${c.ac.climb_speed}" />kt</td>
</tr>
<tr>
<td>Cruise climb rate:</td><td><input type="text" name="climb_rate" value="${c.ac.climb_rate}" />feet/min</td>
</tr>
<tr>
<td>Cruise climb fuel burn:</td><td><input type="text" name="climb_burn" value="${c.ac.climb_burn}" />L/h</td>
</tr>
<tr>
<td>Descent speed:</td><td><input type="text" name="descent_speed" value="${c.ac.descent_speed}" />kt</td>
</tr>
<tr>
<td>Descent rate:</td><td><input type="text" name="descent_rate" value="${c.ac.descent_rate}" />feet/min</td>
</tr>
<tr>
<td>Descent fuel burn:</td><td><input type="text" name="descent_burn" value="${c.ac.descent_burn}" />L/h</td>
</tr>

</table>
%endif        
<input type="hidden" id="navigate_to" name="navigate_to" value="" />
%if len(c.all_aircraft):
<input type="submit" name="save_button" value="Save"/>
%endif

</form>
</div>
	

