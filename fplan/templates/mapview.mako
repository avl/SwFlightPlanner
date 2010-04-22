
<%inherit file="base.mako"/>


<script type="text/javascript" src="/wz_jsgraphics.js"></script>
<script type="text/javascript" src="/mwheel.js"></script>
<script src="/MochiKit.js" type="text/javascript"></script>


<script type="text/javascript">

function save_data(cont)
{
	cont();
}

/*
function solvablecb(req)
{
	var elem=getElement('solvable');
	elem.innerHTML=req.responseText;
	inprogress=0;
	if (runagain==1)
	{
		runagain=0;
		checksolvable_impl();
	}		
}
function checksolvable_impl()
{
	if (inprogress==1)
	{
		runagain=1;
		return;
	}
	else
	{
		inprogress=1;
	}
	var svct=getElement("solvable");
	svct.innerHTML='${_(u"Calculating...")}';
	var fm=getElement('mainform');
	var elems=fm.getElementsByTagName('select');
	params={};
	for(var i=0;i<elems.length;++i)
	{
		var elem=elems[i];
		if (elem.name.substr(0,3)=='add')
			continue;
		params[elem.name]=elem.value;
	}
		
	def=doSimpleXMLHttpRequest(checkurl,
		params);
	def.addCallback(solvablecb);
}
*/

function tab_modify_pos(idx,pos)
{
	var glist=document.getElementById('tab_fplan');
	var rowpos=glist.rows[idx].cells[2];
	rowpos.value=''+pos[0]+','+pos[1];	
}
function tab_remove_waypoint(idx)
{
	var glist=document.getElementById('tab_fplan');
	glist.deleteRow(idx);
	tab_renumber(idx);
}
function tab_renumber(idx)
{
	var glist=document.getElementById('tab_fplan');
	for(var i=idx;i<glist.rows.length;i++)
	{
		var rowelem=glist.rows[i];		
		rowelem.cells[0].innerHTML='<td>#'+i+':';
		rowelem.cells[1].childNodes[0].name='row_'+i+'_name';
		rowelem.cells[2].childNodes[0].name='row_'+i+'_pos';
	}	
}
function tab_add_waypoint(idx,pos)
{
	
	var glist=document.getElementById('tab_fplan');
	var elem=0;
	if (idx>=wps.length)
	{
		idx=wps.length;
   		elem=glist.insertRow(-1);
    }
   	else
   	{
   		elem=glist.insertRow(idx);
   	}
   	
    elem.innerHTML=\
    '<td>#'+idx+':</td>'+
    '<td><input type="text" name="row_'+idx+'_name" value=""/></td>'+
    '<td><input type="hidden" name="row_'+idx+'_pos" value="'+pos[0]+','+pos[1]+'"/></td> '+
    '';

	if (idx!=wps.length)
	{
		tab_renumber(idx+1);	
	}
	
}

function on_key(event)
{
/*
	if (event.which==67)
	{
		if (last_mousemove_lat==-90)
			return false;
		
		var form=document.getElementById('helperform');
		form.center.value=''+last_mousemove_lat+','+last_mousemove_lon;
		form.submit();	
	}
*/
}
keyhandler=on_key

function dozoom(how)
{
	var form=document.getElementById('helperform');
	form.zoom.value=''+how;
	form.submit();	
}
function zoom_out_impl()
{
	dozoom(1);
}
function zoom_in_impl()
{
	dozoom(-1);
}
function zoom_out()
{
 	save_data(zoom_out_impl);
}
function zoom_in()
{
 	save_data(zoom_in_impl);
}
function handle_mouse_wheel(delta) 
{
	if (delta>0)
		zoom_in();
	if (delta<0)
		zoom_out(); 		
}


map_ysize=0;
map_xsize=0;
PI=3.1415926535897931;
function sinh(x) 
{
	return (Math.exp(x) - Math.exp(-x))/2.0;
}
function aviation_format(lat,lon)
{
	var lathemi='N';
	if (lat<0)
	{
		lathemi='S';
		lat=-lat;
	} 
	var latdeg=Math.floor(lat);
	var latmin=((lat+90)%1.0)*60.0;

	lonhemi='E';
	if (lon<0)
	{
		lonhemi='W';
		lon=-lon;
	} 
	var londeg=Math.floor(lon);
	var lonmin=((lon+90)%1.0)*60.0;
	
	return latdeg.toFixed(0)+"'"+latmin.toFixed(2)+lathemi+londeg.toFixed(0)+"'"+lonmin.toFixed(2)+lonhemi;	
}
function to_lat(y)
{
	return (180.0/PI)*Math.atan(sinh(y));
}
function to_y(lat)
{
	lat/=(180.0/PI);
	return Math.log(Math.tan(lat)+1.0/Math.cos(lat));
} 

function to_latlon(px,py)
{
	if (map_ysize==0)
	{
		return [0,0];
	}
	var x=(px)/(map_xsize+0.0);
	var y=(map_ysize-py)/(map_ysize+0.0);
	
	var wfactor=map_xsize/map_ysize;
	var min_merc_y=to_y(${c.lat-0.5*c.size});
	var max_merc_y=to_y(${c.lat+0.5*c.size});
	var cury=y*(max_merc_y-min_merc_y)+min_merc_y;
	var lat=to_lat(cury);
					
	var lon=${c.lon}-${0.5*c.lonwidth}*wfactor+${c.lonwidth}*x*wfactor;	
	lon = lon % 360.0;
	if (lon<0) lon=lon+360.0;	
	return [lat,lon];	
}

wps=[];

popupvisible=0;
movingwaypoint=-1;
function hidepopup()
{
	var cm=document.getElementById("mmenu");
	cm.style.display="none";
	popupvisible=0;
}

lastrightclickx=0;
lastrightclicky=0;
function on_rightclickmap(event)
{
	waypointstate='none';	
	jgq.clear();
	var relx=get_rel_x(event.clientX);
	var rely=get_rel_y(event.clientY);
	
	var clo=get_close_line(relx,rely);
	var cm=document.getElementById("mmenu");
	
	if (clo.length==3)
	{ //A line nearby	
		document.getElementById("menu-add").innerHTML="Insert waypoint";	
	}
	else
	{
		document.getElementById("menu-add").innerHTML="Add destination";	
	}
		
	cm.style.display="block";
	popupvisible=1;
	lastrightclickx=get_rel_x(event.clientX);
	lastrightclicky=get_rel_y(event.clientY);
	
	cm.style.left=''+event.clientX+'px';
	cm.style.top=''+event.clientY+'px';
	return false;
}

function abs_x(x)
{
	return x;
}
function abs_y(y)
{
	return y;
}
function get_rel_x(clientX)
{
	var x=clientX-document.getElementById('mapid').offsetLeft;
	return x;
}
function get_rel_y(clientY)
{
	var y=clientY-document.getElementById('mapid').offsetTop;
	return y;
}
function draw_jg()
{
	jg.clear();
	
    for(var i=0;i<wps.length;i++)
    {
    	if (waypointstate!='moving' || (
    		i-1!=movingwaypoint && i!=movingwaypoint))
    	{
    		if (i!=0)    		
	    		jg.drawLine(
		    		abs_x(wps[i-1][0]),
	    			abs_y(wps[i-1][1]),
	    			abs_x(wps[i][0]),
	    			abs_y(wps[i][1]));	    		
		    jg.fillEllipse(abs_x(wps[i][0])-5,abs_y(wps[i][1])-5,10,10);
		}
    }    
    jg.paint();
}

waypointstate='none';
anchorx=-1;
anchory=-1;
jg=0;
jgq=0;

function on_clickmap(event)
{
	relx=get_rel_x(event.clientX);
	rely=get_rel_y(event.clientY);
	if (popupvisible)
	{
		hidepopup();		
		return;	
	}	
	if (waypointstate=='addwaypoint')
	{
		tab_add_waypoint(wps.length,[relx,rely]);
		wps.push([get_rel_x(event.clientX),get_rel_y(event.clientY)]);
		waypointstate='none';
		jgq.clear();
		draw_jg();
		return;		
	}
	else if (waypointstate=='moving')
	{
		wps[movingwaypoint]=[relx,rely];
		tab_modify_pos(movingwaypoint,[relx,rely]);
		waypointstate='none';
		jgq.clear();
		draw_jg();
		return;		
	}
	else
	{
		if (wps.length==0)
		{
			anchorx=get_rel_x(event.clientX);
			anchory=get_rel_y(event.clientY);		
			tab_add_waypoint(wps.length,[relx,rely]);
			wps.push([anchorx,anchory]);
			waypointstate='addwaypoint';
		}
		else
		{	
			var closest_i=get_close_waypoint(get_rel_x(event.clientX),get_rel_y(event.clientY));
			if (closest_i==-1)
			{
			
				var clo=get_close_line(relx,rely);
				if (clo.length==3)
				{
					alert("Change this - show information about clicked line instead of adding");
					var tmpwps=[];
					for(var i=0;i<wps.length;i++)
					{						
						tmpwps.push(wps[i]);
						if (i==clo[0])
							tmpwps.push([clo[1],clo[2]]);
					}
					wps=tmpwps;
					tab_add_waypoint(clo[0],[relx,rely]);
					waypointstate='moving';
					movingwaypoint=clo[0]+1;						
					draw_jg();
					draw_dynamic_lines(get_rel_x(event.clientX),get_rel_y(event.clientY));
				}
				else
				{
					anchorx=wps[wps.length-1][0];
					anchory=wps[wps.length-1][1];
					waypointstate='addwaypoint';
					draw_jg();
					draw_dynamic_lines(get_rel_x(event.clientX),get_rel_y(event.clientY));		
				}
			}
			else
			{
				alert("Change this - show information about clicked waypoint instead of adding");
				waypointstate='moving';
				movingwaypoint=closest_i;	
				draw_jg();
				draw_dynamic_lines(get_rel_x(event.clientX),get_rel_y(event.clientY));		
			}
		}
		
		draw_dynamic_lines(get_rel_x(event.clientX),get_rel_y(event.clientY));
	}

}

function draw_dynamic_lines(cx,cy)
{
	if (waypointstate=='addwaypoint')
	{
		jgq.clear();
		jgq.drawLine(anchorx,anchory,cx,cy);
		jgq.paint();
	}
	else if (waypointstate=='moving')
	{
		jgq.clear();
		if (movingwaypoint!=0)
			jgq.drawLine(wps[movingwaypoint-1][0],wps[movingwaypoint-1][1],cx,cy);
		if (movingwaypoint!=wps.length-1)
			jgq.drawLine(wps[movingwaypoint+1][0],wps[movingwaypoint+1][1],cx,cy);
		jgq.paint();
		
	}
}

last_mousemove_lat=-90;
last_mousemove_lon=-360;

function on_mousemovemap(event)
{
	var latlon=to_latlon(get_rel_x(event.clientX),get_rel_y(event.clientY));
	var lat=latlon[0];
	var lon=latlon[1];
	last_mousemove_lat=lat;
	last_mousemove_lon=lon;
	document.getElementById("footer").innerHTML=aviation_format(lat,lon)
		
	draw_dynamic_lines(get_rel_x(event.clientX),get_rel_y(event.clientY));
}
function get_close_waypoint(relx,rely)
{
	var closest_i=0;
	var closest_dist=1e12;
	for(var i=0;i<wps.length;i++)
	{
		dist=(wps[i][0]-relx)*(wps[i][0]-relx)+(wps[i][1]-rely)*(wps[i][1]-rely);
		if (dist<closest_dist)
		{
			closest_i=i;closest_dist=dist;
		}			
	}
	
	if (closest_dist<30*30)
		return closest_i;
	return -1;
}
function get_close_line(relx,rely)
{
	var closest_i=0;
	var closest_dist=1e12;
	var close_x=0;
	var close_y=0;
	for(var i=1;i<wps.length;i++)
	{
		var x1=wps[i-1][0];
		var y1=wps[i-1][1];
		var x2=wps[i][0];
		var y2=wps[i][1];
		var dx1=relx-x1;
		var dy1=rely-y1;
		var dx2=relx-x2;
		var dy2=rely-y2;
		var vx=(x2-x1);
		var vy=(y2-y1);
		var vl=Math.sqrt(vx*vx+vy*vy);
		vx=vx/vl;
		vy=vy/vl;
		var p1=vx*dx1+vy*dy1;
		if (p1<0) continue;
		var p2=vx*dx2+vy*dy2;
		if (p2>0) continue;
		var ox=x1+p1*vx;
		var oy=y1+p1*vy;
		
		var dist=Math.sqrt((ox-relx)*(ox-relx)+(oy-rely)*(oy-rely));
		
		if (dist<closest_dist)
		{
			closest_dist=dist;
			closest_i=i-1;
			close_x=ox;
			close_y=oy;
		}				
	}	
	
	if (closest_dist<10)
		return [closest_i,close_x,close_y];
	return -1;
}

function move_waypoint()
{
	hidepopup();
	var closest_i=get_close_waypoint(lastrightclickx,lastrightclicky);
	waypointstate='moving';
	movingwaypoint=closest_i;	
	draw_jg();
	draw_dynamic_lines(lastrightclickx,lastrightclicky);
}
function remove_waypoint()
{

	hidepopup();
	var closest_i=get_close_waypoint(lastrightclickx,lastrightclicky);	
	if (closest_i!=-1)
	{
		var wpsout=[];
		for(var i=0;i<wps.length;++i)
		{
			if (i!=closest_i)
				wpsout.push([wps[i][0],wps[i][1]]);
		}
		wps=wpsout;
		tab_remove_waypoint(closest_i);

		draw_jg();		
	}
}

function close_menu()
{
	hidepopup();
}
function menu_add_waypoint_mode()
{
	hidepopup();
	var relx=lastrightclickx;
	var rely=lastrightclicky;

	var clo=get_close_line(relx,rely);
	if (clo.length==3)
	{
		var tmpwps=[];
		for(var i=0;i<wps.length;i++)
		{						
			tmpwps.push(wps[i]);
			if (i==clo[0])
				tmpwps.push([clo[1],clo[2]]);
		}
		wps=tmpwps;
		tab_add_waypoint(clo[0],[relx,rely]);
		waypointstate='moving';
		movingwaypoint=clo[0]+1;						
		draw_jg();
		draw_dynamic_lines(relx,rely);
	}
	else
	{
		if (wps.length==0)	
		{	
			waypointstate='addwaypoint';
			anchorx=lastrightclickx;		
			anchory=lastrightclicky;		
			wps.push([anchorx,anchory]);
		}
		else
		{
			anchorx=wps[wps.length-1][0];
			anchory=wps[wps.length-1][1];
			waypointstate='addwaypoint';		
		}
		draw_dynamic_lines(anchorx,anchory);
	}

	
	
}

function center_map()
{
	var latlon=to_latlon(lastrightclickx,lastrightclicky);
	var lat=latlon[0];
	var lon=latlon[1];
	var form=document.getElementById('helperform');
	form.center.value=''+lat+','+lon;
	form.submit();	
}

function loadmap()
{
	var content=document.getElementById('content')
	var h=content.offsetHeight;
	var w=content.offsetWidth;
	var left=content.offsetLeft;
	var top=content.offsetTop;

		
	content.innerHTML='<img id="mapid" src="/maptile/get?pos=${c.pos}&latitudes=${c.size}&width='+(w-3)+'&height='+(h-3)+'"/>'+
	'<div id="overlay1" style="position:absolute;z-index:1;left:'+left+'px;top:'+top+'px;width:'+w+'px;height:'+h+'px;"></div>'+
	'<div oncontextmenu="return on_rightclickmap(event)" onmousemove="on_mousemovemap(event)" onclick="on_clickmap(event)" id="overlay2" style="position:absolute;z-index:2;left:'+left+'px;top:'+top+'px;width:'+w+'px;height:'+h+'px;"></div>'+
	'<div id="mmenu" class="popup">'+
	'<div class="popopt" id="menu-add" onclick="menu_add_waypoint_mode()">Add Waypoint</div>'+
	'<div class="popopt" onclick="remove_waypoint()">Remove Waypoint</div>'+
	'<div class="popopt" onclick="move_waypoint()">Move Waypoint</div>'+
	'<div class="popopt" onclick="close_menu()">Close menu</div>'+
	'<div class="popopt" onclick="center_map()">Center Map</div>'+ 
	'</div>'+
	'<form id="helperform" action="${h.url_for(controller="mapview",action="zoom")}">'+
	'<input type="hidden" name="zoom" value="">'+
	'<input type="hidden" name="center" value="">'+
	'</form>'
	;
	
	var sidebar=document.getElementById('sidebar-a');
	sidebar.innerHTML='<form id="fplanform" action="${h.url_for(controller="mapview",action="save")}">'+
	'<table id="tab_fplan" width="100%">'+
	'</table></form>';
	
	
	map_ysize=h;
	map_xsize=w;
	
	
	jgq = new jsGraphics("overlay1");
	jgq.setStroke("3");
	jgq.setColor("#00ff00"); // green
	

	jg = new jsGraphics("overlay2");
	jg.setStroke("3");
	jg.setColor("#00d000"); 
	
	
	
}
addLoadEvent(loadmap);

</script>


	