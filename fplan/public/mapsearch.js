searchpopup=0;
searchpopup_sel=-1;
searchlastdata=[];
searchordinal=0;

function add_searched_waypoint(sel)
{
	var d=searchlastdata[sel];
	if (d.length>2)
		add_waypoint(d[2],d[1]);
	else
		add_waypoint(d[0],d[1]);	
}

function findPos(obj) {
	var curleft = curtop = 0;

	if (obj.offsetParent) {
		do {
			curleft += obj.offsetLeft;
			curtop += obj.offsetTop;			
		} while (obj = obj.offsetParent);
	}
	
	return [curleft,curtop];
}
function remove_searchpopup()
{
	var s=document.getElementById('searchpopup');
	s.style.display='none';
	searchpopup=0;
	searchlastdata=[];
}
function searchsel(delta)
{
	if (searchpopup_sel>=0)
		searchpopup.childNodes[searchpopup_sel].style.background='#ffffff';
	searchpopup_sel+=delta;
	if (searchpopup_sel<0)
		searchpopup_sel=0;
	if (searchpopup_sel>=searchpopup.childNodes.length)
		searchpopup_sel=searchpopup.childNodes.length-1;
	if (searchpopup_sel>=0)
		searchpopup.childNodes[searchpopup_sel].style.background='#ff0000';
}

function on_search_keydown(event)
{
	
	if (searchpopup)
	{	
		//38=up, 40=ner, 13 = enter
		if (event.which==38)
		{ //up			
			searchsel(-1);
			return false;
		}
		if (event.which==40)
		{ //down
			searchsel(1);
			return false;
		}
		if (event.which==13)
		{			
			if (searchpopup_sel>=0 && searchpopup_sel<searchlastdata.length)
			{
				add_searched_waypoint(searchpopup_sel);
        	    document.getElementById('searchfield').value='';
            	remove_searchpopup();	
			}
			if (searchpopup_sel==-1)
			{
				mapsearch_add_to_route_button();
			}
			return false;
		}
	}
	return true;
}
function mapsearch_add_to_route_button()
{
	if (searchlastdata.length==0)
	{
		alert('The search matches no items!');
		return;
	}
	add_searched_waypoint(0);
    document.getElementById('searchfield').value='';
	remove_searchpopup();	
}
function search_select(idx)
{
    if (idx>=0 && idx<searchlastdata.length)
    {
		add_searched_waypoint(idx);
	}
    remove_searchpopup();
}

function on_search_keyup(keyevent)
{
	if (keyevent.which==38 || keyevent.which==40 || keyevent.which==13)
		return false;
	var field=document.getElementById('searchfield');
	searchfor(field.value);
}
function set_searchinprog()
{
	var e=document.getElementById('searchprogtext');
	e.style.display='inline';
}
function clear_searchinprog()
{
	var e=document.getElementById('searchprogtext');
	e.style.display='none';	
}
searchinprog=0;
searchnext=null;
function searchfor(fieldval)
{
	var s=document.getElementById('searchpopup');
	var field=document.getElementById('searchfield');
	if (searchinprog!=0)
	{
		searchnext=fieldval;
		return;
	}
	searchnext=null;
	function search_cb(req)
	{	
		searchinprog=0;
		if (req.responseText=='')
		{			
			s.style.display='none';
			searchpopup=0;
		}
		else
		{
			s.style.display='block';
			searchpopup=s;
			searchpopup_sel=-1;
			var pos=findPos(field);
			s.style.left=''+pos[0]+'px';
			s.style.top=''+(pos[1]+field.offsetHeight)+'px';
			var ret=evalJSONRequest(req);
			
			if (parseInt(ret.ordinal)==searchordinal)
			{
					
				searchlastdata=ret.hits;
				
				var inner='';
				for(var i=0;i<searchlastdata.length;++i)
				{
					inner+='<p style="cursor:pointer" onclick="search_select('+i+')">'+searchlastdata[i][0]+'</p>';
				}
				inner+='<p style="cursor:pointer;color:#808080" onclick="remove_searchpopup();"><u>close</u></p>';
				s.innerHTML=inner;
			}
		}
		if (searchnext!=null)
		{
			searchfor(searchnext);
		}
		else
		{
			clear_searchinprog();			
		}
	}
	
	if (fieldval=='')
	{
		clear_searchinprog();			
		searchinprog=0;
		++searchordinal;
		remove_searchpopup();
	}	
	else
	{	
		var params={};	
		params['search']=fieldval;
		++searchordinal;
		params['ordinal']=searchordinal;
		searchinprog=1;
		set_searchinprog();			
		var def=doSimpleXMLHttpRequest(searchairporturl,
			params);
		def.addCallbacks(search_cb);
	}	
}

