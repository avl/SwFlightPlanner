opinprogress=0;
searchagain=0;
searchagainfor='';
function search_destination(searchfor)
{
	var s=document.getElementById('searchmenu');
	if (opinprogress==1)
	{
		searchagain=1;
		searchagainfor=searchfor;
		return;
	}
	function search_cb(req)
	{	
		opinprogress=0;
		s.innerHTML=req.responseText;
		if (searchagain)
		{
			searchagain=0;
			search_destination(searchagainfor);				
		}
	}
	s.innerHTML='Searching...';
	s.style.display='block';
	s.style.left='100px';
	s.style.top='300px';
	
	
	var params={};	
	var field=document.getElementById(searchfor);
	params['search']=field.value;
	var def=doSimpleXMLHttpRequest(searchairporturl,
		params);
	def.addCallback(search_cb);	
}
function fpaddwaypoint(pos,name,rowdata)
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
	var idx=0;
	if (tab.rows.length==1)
		idx=0;
	else
		idx=(tab.rows.length-1)/2;
	var elem=tab.insertRow(-1);
	elem.innerHTML='<td colspan="'+fpcolnum+'">#'+idx+': <input type="text" onkeyup="search_destination(\'wpid'+idx+'\')" id="wpid'+idx+'" name="name'+idx+'" value="'+name+'"/></td>';
	if (rowdata!=null && rowdata.length>0)
	{
		var elem=tab.insertRow(-1);
		var s='';
		for(var i=0;i<rowdata.length;++i)
		{
			s=s+'<td><input size="'+fpcolwidth[i]+'" title="'+fpcoldesc[i]+' '+fpcolextra[i]+'" type="text" name="row'+i+''+fpcolshort[i]+'" value=""/></td>\n';		
		}
		elem.innerHTML=s;
	}

}