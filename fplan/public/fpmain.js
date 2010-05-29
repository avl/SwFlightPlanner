function on_updaterow(idx,col)
{
	function get(wcol)
	{
		var vid='fplanrow'+idx+wcol;
		var e=document.getElementById(vid);
		return parseFloat(e.value);
	}

	
	if (col=='TAS' || col=='TT' || col=='W' || col=='V')
	{
		var tas=get('TAS');
		var tt=get('TT');
		var w=get('W');
		var v=get('V');
		var variation=get('Var');
		var dev=get('Dev');
		
	
	}
	if (col=='TAS' || col=='TT' || col=='W' || col=='V' || col=='Var' || col=='Dev')
	{
	}	
	

	return;	
}
function fpaddwaypoint(pos,name,rowdata)
{
	var noyet=document.getElementById('nowaypointsyet');
	noyet.display='none';
	searchpopup=0;

	
	var tab=document.getElementById('flightplantable');
	if (rowdata==null)
	{
		rowdata=[];
		for(var i=0;i<fpcolnum;++i)
			rowdata.push('');
	}
	var idx=0;
	if (tab.rows.length==1)
		idx=0;
	else
		idx=(tab.rows.length-1)/2;
	var elem=tab.insertRow(-1);
	elem.innerHTML='<td colspan="'+fpcolnum+'">#'+idx+': <input type="text" onblur="remove_searchpopup()" onkeydown="return searchmaneuver(event)" onkeyup="search_destination(event,\'wpid'+idx+'\')" id="wpid'+idx+'" name="name'+idx+'" value="'+name+'"/></td>';
	if (rowdata!=null && rowdata.length>0)
	{
		var elem=tab.insertRow(-1);
		var s='';
		for(var i=0;i<rowdata.length;++i)
		{			
			s=s+'<td><input id="fplanrow'+idx+fpcolshort[i]+'" onchange="on_updaterow('+idx+',\''+fpcolshort[i]+'\');" size="'+fpcolwidth[i]+'" title="'+fpcoldesc[i]+' '+fpcolextra[i]+'" type="text" name="row'+i+''+fpcolshort[i]+'" value="'+rowdata[i]+'"/></td>\n';		
		}
		elem.innerHTML=s;
	}
}
