<%inherit file="base.mako"/>

<div style="height:100%;width:100%;overflow:auto;">

<table>

%for notamupdate in c.notamsupdates:
<tr>
<td>
${notamupdate.text}
</td>
</tr>
%endfor
</table>
</div>


