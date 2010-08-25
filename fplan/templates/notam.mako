<%inherit file="base.mako"/>

<script src="/notam.js" type="text/javascript">
</script>
<script src="/MochiKit.js" type="text/javascript">
</script>
<script type="text/javascript">
marknotamurl='${h.url_for(controller="notam",action="mark")}';
function navigate_to(where)
{	
	window.location.href=where;
}
function onloadnotam()
{
    force_refresh_on_back_button('${h.url_for(controller="notam",action="index")}');
}
addLoadEvent(onloadnotam);
</script>

<div id="notamcontent" style="height:100%;width:100%;overflow:auto;">

<h1>Latest Notam Updates</h1>
<table>
<tr>
<td colspan="2" > 
<form action="${h.url_for(controller="notam",action="markall")}" method="post">
Click on items when you have read them.<br/>
<input style="font-size:10px" type="submit" value="I have read them all!"/>
</form>
<form action="${h.url_for(controller="notam",action="savefilter")}" method="post">
<button style="font-size:10px"  onclick="showhide_filter();return false;">Filtering</button>
<br/>
<div id="popup_category" style="font-size:11px;position:absolute;z-index:15;background-color:#ffffff;display:none;border: 1px #808080 solid;">
<input type="submit" style="font-size:13px" value="Apply Filter"/><br/>

<b>Show Obstacles and Broken Lights:</b><input type="checkbox" name="showobst" ${'checked="checked"' if c.showobst else ''|n} /> <br/>
<b>Filter Regions:</b><br/><input id="searchcat" onchange="filtercat()" onkeyup="filtercat()" type="text" name="searchcat"/>
<div style="height:300px;width:500px;overflow:auto">
<table border="0" id="filtercattable">
%for cat in c.categories:
<tr>
<td><input type="checkbox" name="category_${cat}" ${'checked="checked"' if cat in c.sel_cat else ''|n}/>${cat}</td>
</tr>
%endfor
</table>
</div>

</div>
</form>
</td>
</tr>
</table>
<table>
<tr style="font-size:12px"><td>Shown:</td><td>${c.show_cnt}</td>
<td>Filtered:</td><td>${c.hide_cnt}</td></tr>
</table>
<table id="notamtable">
%for notamupdate,acks,downloaded in c.shown:
<tr id="notamcolor_${notamupdate.appearnotam}_${notamupdate.appearline}" style="background:${'#b0ffb0' if acks else '#ffd0b0'}">
<td>
<input onchange="click_item(${notamupdate.appearnotam},${notamupdate.appearline},1);return true" type="checkbox" id="notam_${notamupdate.appearnotam}_${notamupdate.appearline}" 
${'checked="1"' if acks else ''|n}/>
</td>
<td>
<div style="font-size:10px">
<b>${notamupdate.category}</b> 
</div>
<div style="font-size:12px;cursor:pointer" onclick="click_item(${notamupdate.appearnotam},${notamupdate.appearline},0);return true" >
%for line in notamupdate.text.splitlines():
${line}<br/>
%endfor
</div>
<div style="font-size:10px">
Downloaded: <b>${downloaded.strftime("%Y%m%d %H%M")}</b> <b><u>
<a href="${h.url_for(controller="notam",action="show_ctx",notam=notamupdate.appearnotam,line=notamupdate.appearline)}#notam">
See original-&gt;
</a></u></b>
</div>
</div>
</td>
</tr>
%endfor
</table>
</div>


