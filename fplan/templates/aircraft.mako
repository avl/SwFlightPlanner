
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

%if c.flash:
<p><span style="background-color:#80ff80;font-size:14px">
${c.flash}
</span></p><br/>
%endif

<form id="acform" action="${h.url_for(controller="aircraft",action="save")}" method="POST">
%if not c.newly_added:
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
%endif

%if c.ac:
%if not c.newly_added:
<input type="submit" name="del_button" value="Delete aircraft"/>
%endif

<table>

<tr>
<td>Registration:</td><td><input type="hidden" name="orig_aircraft" value="${c.orig_aircraft}" />
<input type="text" name="aircraft" value="${c.ac.aircraft}" />(Example: SE-ABC)</td>
</tr>

<tr>
<td>Aircraft Type :</td><td>
    <input type="text" name="atstype" value="${c.ac.atstype}" />(Type-designator as used in ATS-flight plans)</td>
</tr>
</tr>
<tr>
<td>Cruise speed:</td><td><input ${c.fmterror('cruise_speed')|n} type="text" name="cruise_speed" value="${c.ac.cruise_speed}" />kt ${c.msgerror('cruise_speed')}</td>
</tr>
<tr>
<td>Cruise fuel burn:</td><td><input ${c.fmterror('cruise_burn')|n} type="text" name="cruise_burn" value="${c.ac.cruise_burn}" />L/h ${c.msgerror('cruise_burn')}</td>
</tr>
<tr>
<td>Cruise climb speed:</td><td><input ${c.fmterror('climb_speed')|n} type="text" name="climb_speed" value="${c.ac.climb_speed}" />kt ${c.msgerror('climb_speed')}</td>
</tr>
<tr>
<td>Cruise climb rate:</td><td><input ${c.fmterror('climb_rate')|n} type="text" name="climb_rate" value="${c.ac.climb_rate}" />feet/min ${c.msgerror('climb_rate')}</td>
</tr>
<tr>
<td>Cruise climb fuel burn:</td><td><input ${c.fmterror('climb_burn')|n} type="text" name="climb_burn" value="${c.ac.climb_burn}" />L/h ${c.msgerror('climb_burn')}</td>
</tr>
<tr>
<td>Descent speed:</td><td><input ${c.fmterror('descent_speed')|n} type="text" name="descent_speed" value="${c.ac.descent_speed}" />kt ${c.msgerror('descent_speed')}</td>
</tr>
<tr>
<td>Descent rate:</td><td><input ${c.fmterror('descent_rate')|n} type="text" name="descent_rate" value="${c.ac.descent_rate}" />feet/min ${c.msgerror('descent_rate')}</td>
</tr>
<tr>
<td>Descent fuel burn:</td><td><input ${c.fmterror('descent_burn')|n} type="text" name="descent_burn" value="${c.ac.descent_burn}" />L/h ${c.msgerror('descent_burn')}</td>
</tr>

<tr>
<td>Aircraft Color and Markings :</td><td>
    <input type="text" name="markings" value="${c.ac.markings}" />(Aircraft Colour and Markings for use in ATS-flight plan)</td>
</tr>
<td colspan="2" style="font-size:10px">
The following abbreviations are allowed: 
 B = Blue , G = Green , R = Red , W = White , Y = Yellow. Other colours should be written in plain text, like: ORANGE.
</td>

<tr>

</table>
%endif        
<input type="hidden" id="navigate_to" name="navigate_to" value="" />
%if len(c.all_aircraft):
<input type="submit" name="save_button" value="Save"/>
%endif


</form>
</div>
	

