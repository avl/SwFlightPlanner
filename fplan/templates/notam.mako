<%inherit file="base.mako"/>

<script src="/notam.js" type="text/javascript"></script>

<div id="" style="height:100%;width:100%;overflow:auto;">

<table>
<tr>
<td>Read</td><td>Notam <button style="font-size:10px">Mark all read</button></td>
</tr>
%for notamupdate in c.notamupdates:
<tr style="cursor:pointer">
<td>
<input onchange="click_item(${notamupdate.appearnotam},${notamupdate.appearline},1);return true" type="checkbox" id="notam_${notamupdate.appearnotam}_${notamupdate.appearline}" checked="0"/>
</td>
<td onclick="click_item(${notamupdate.appearnotam},${notamupdate.appearline},0);return true" >
<div style="font-size:10px">
<b>${notamupdate.category}</b> 
</div>
<div style="font-size:12px;background">
%for line in notamupdate.text.splitlines():
${line}<br/>
%endfor
Downloaded: <b>${notamupdate.notam.downloaded}</b>
</div>
</td>
</tr>
%endfor
</table>
</div>


