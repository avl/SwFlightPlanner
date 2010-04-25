function fpaddwaypoint(rowdata)
{
	var noyet=document.getElementById('nowaypointsyet');
	noyet.display='none';
	
	var tab=document.getElementById('flightplantable');
	if (rowdata==null)
	{
		rowdata=[];
		for(var i=0;i<fpcolnum;++i)
			rowdata.push('');
	}
	
	elem=tab.insertRow(-1);
	
	var s='';
	for(var i=0;i<rowdata.length;++i)
	{
		s=s+'<td><input size="'+fpcolwidth[i]+'" title="'+fpcolname[i]+'" type="text" name="row'+i+''+fpcolshort[i]+'" value="${c.get('winddir',c.waypoints[cnt],c.waypoints[cnt+1])}"/></td>\n';		
	}
	elem.innerHTML=s;
	''+
<td></td>
<td><input size="3" title="Wind Direction" type="text" name="row${cnt}winddir" value="${c.get('winddir',c.waypoints[cnt],c.waypoints[cnt+1])}"/></td>
<td><input size="2" title="Wind Velocity" type="text" name="row${cnt}windvel" value="${c.get('windvel',c.waypoints[cnt],c.waypoints[cnt+1])}"/></td>
<td><input size="2" type="text" name="row${cnt}temp" value="${c.get('temp',c.waypoints[cnt],c.waypoints[cnt+1])}"/></td>
<td><input size="4" type="text" name="row${cnt}alt" value="${c.get('alt',c.waypoints[cnt],c.waypoints[cnt+1])}"/></td>
<td><input size="3" type="text" name="row${cnt}tas" value="${c.get('tas',c.waypoints[cnt],c.waypoints[cnt+1])}"/></td>
<td><input size="3" type="text" name="row${cnt}tt" value="${c.get('tt',c.waypoints[cnt],c.waypoints[cnt+1])}"/></td>
<td><input size="2" type="text" name="row${cnt}wca" value="${c.get('wca',c.waypoints[cnt],c.waypoints[cnt+1])}"/></td>
<td><input size="2" type="text" name="row${cnt}var" value="${c.get('var',c.waypoints[cnt],c.waypoints[cnt+1])}"/></td>
<td><input size="2" type="text" name="row${cnt}dev" value="${c.get('dev',c.waypoints[cnt],c.waypoints[cnt+1])}"/></td>
<td><input size="3" type="text" name="row${cnt}ch" value="${c.get('ch',c.waypoints[cnt],c.waypoints[cnt+1])}"/></td>
<td><input size="3" type="text" name="row${cnt}dist" value="${c.get('dist',c.waypoints[cnt],c.waypoints[cnt+1])}"/></td>

<tr>
<td colspan="12">
${wp.waypoint}
</td>
</tr>
%if cnt!=len(c.waypoints)-1:
<tr>
<td></td>
<td><input size="3" title="Wind Direction" type="text" name="row${cnt}winddir" value="${c.get('winddir',c.waypoints[cnt],c.waypoints[cnt+1])}"/></td>
<td><input size="2" title="Wind Velocity" type="text" name="row${cnt}windvel" value="${c.get('windvel',c.waypoints[cnt],c.waypoints[cnt+1])}"/></td>
<td><input size="2" type="text" name="row${cnt}temp" value="${c.get('temp',c.waypoints[cnt],c.waypoints[cnt+1])}"/></td>
<td><input size="4" type="text" name="row${cnt}alt" value="${c.get('alt',c.waypoints[cnt],c.waypoints[cnt+1])}"/></td>
<td><input size="3" type="text" name="row${cnt}tas" value="${c.get('tas',c.waypoints[cnt],c.waypoints[cnt+1])}"/></td>
<td><input size="3" type="text" name="row${cnt}tt" value="${c.get('tt',c.waypoints[cnt],c.waypoints[cnt+1])}"/></td>
<td><input size="2" type="text" name="row${cnt}wca" value="${c.get('wca',c.waypoints[cnt],c.waypoints[cnt+1])}"/></td>
<td><input size="2" type="text" name="row${cnt}var" value="${c.get('var',c.waypoints[cnt],c.waypoints[cnt+1])}"/></td>
<td><input size="2" type="text" name="row${cnt}dev" value="${c.get('dev',c.waypoints[cnt],c.waypoints[cnt+1])}"/></td>
<td><input size="3" type="text" name="row${cnt}ch" value="${c.get('ch',c.waypoints[cnt],c.waypoints[cnt+1])}"/></td>
<td><input size="3" type="text" name="row${cnt}dist" value="${c.get('dist',c.waypoints[cnt],c.waypoints[cnt+1])}"/></td>
</tr>
%endif

	
	    '<td>#'+idx+':</td>'+
	    '<td><input type="text" onkeypress="return not_enter(event)" name="row_'+idx+'_name" value="'+name+'"/></td>'+
	    '<td>'+
	    '<input type="hidden" name="row_'+idx+'_pos" value="'+latlon[0]+','+latlon[1]+'"/>'+
	    '<input type="hidden" name="row_'+idx+'_origpos" value="'+origpos+'"/>'+
	    '</td>'+
	    '';	
}