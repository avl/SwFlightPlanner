<input type="hidden" value="${c.pos}" id="coordprespos"/>
<table>

<tr>
<td>
WGS 84 Decimal
</td>
<td colspan="3"><input readonly="1" type="text" value="${c.deg[0][1]}" size="7"/>°</td>
<td><input readonly="1" type="text" size="1" value="${c.deg[0][0]}"/></td>
<td>&nbsp;</td>
<td colspan="3"><input readonly="1" type="text" value="${c.deg[1][1]}" size="7"/>°</td>
<td><input readonly="1" type="text" size="1" value="${c.deg[1][0]}"/></td>
</tr>

<tr>
<td>
WGS 84 Deg/Min
</td>
<td><input readonly="1" type="text" value="${c.degmin[0][1]}" size="2"/>°</td>
<td colspan="2"><input readonly="1" type="text" value="${c.degmin[0][2]}" size="4"/>'</td>
<td><input readonly="1" type="text" size="1" value="${c.degmin[0][0]}"/></td>
<td>&nbsp;</td>
<td><input readonly="1" type="text" value="${c.degmin[1][1]}" size="3"/>°</td>
<td colspan="2"><input readonly="1" type="text" value="${c.degmin[1][2]}" size="4"/>'</td>
<td><input readonly="1" type="text" size="1" value="${c.degmin[1][0]}"/></td>
</tr>

<tr>
<td>
WGS 84 Deg/Min/Sec
</td>
<td><input readonly="1" type="text" value="${c.degminsec[0][1]}" size="2"/>°</td>
<td><input readonly="1" type="text" value="${c.degminsec[0][2]}" size="2"/>'</td>
<td><input readonly="1" type="text" value="${c.degminsec[0][3]}" size="2"/>"</td>
<td><input readonly="1" type="text" size="1" value="${c.degminsec[0][0]}"/></td>
<td>&nbsp;</td>
<td><input readonly="1" type="text" value="${c.degminsec[1][1]}" size="3"/>°</td>
<td><input readonly="1" type="text" value="${c.degminsec[1][2]}" size="2"/>'</td>
<td><input readonly="1" type="text" value="${c.degminsec[1][3]}" size="2"/>"</td>
<td><input readonly="1" type="text" size="1" value="${c.degminsec[1][0]}"/></td>
</tr>


</table>

