
<%inherit file="base.mako"/>


<script src="/wz_jsgraphics.js" type="text/javascript"></script>
<script src="/MochiKit.js" type="text/javascript"></script>
<script src="/mwheel.js" type="text/javascript"></script>
<script src="/mapmath.js" type="text/javascript"></script>
<script src="/mapsearch.js" type="text/javascript"></script>
<script src="/mapmain.js" type="text/javascript"></script>


<script type="text/javascript">

map_zoomlevel=${c.zoomlevel};
map_topleft_merc=undefined;
screen_size_x=0;
screen_size_y=0;
tilesize=256;
xsegcnt=0;
ysegcnt=0;
saveurl='${h.url_for(controller="mapview",action="save")}';
searchairporturl='${h.url_for(controller="flightplan",action="search")}';
showareaurl='${h.url_for(controller="mapview",action="showarea")}';
mapinfourl='${h.url_for(controller="maptile",action="get_airspace")}';
uploadtrackurl='${h.url_for(controller="mapview",action="upload_track")}';

showairspaces=${"1" if c.show_airspaces else "0"};

tilestart=[];//upper left corner of tile grid
tiles=[];
overlay_left=0;
overlay_top=0;

function calctileurl(zoomlevel,mercx,mercy)
{
/*temporary:*/
	return '/maptile/get?zoom='+zoomlevel+'&mercx='+mercx+'&mercy='+mercy+'&showairspaces='+showairspaces;

%if c.showarea or c.showtrack:
	return '/maptile/get?zoom='+zoomlevel+'&mercx='+mercx+'&mercy='+mercy+'&showairspaces='+showairspaces;
%endif
	if (showairspaces)
	{
		return '/tiles/airspace/'+zoomlevel+'/'+mercy+'/'+mercx+'.png';
	}
	else
	{
		return '/tiles/plain/'+zoomlevel+'/'+mercy+'/'+mercx+'.png';
	}
}


function loadmap()
{
	var content=document.getElementById('content')
	var h=content.offsetHeight;
	var w=content.offsetWidth;
	var left=content.offsetLeft;
	var top=content.offsetTop;
	overlay_left=0; //relative to mapcontainer, the parent
	overlay_top=0;
	screen_size_x=parseInt(w);
	screen_size_y=parseInt(h);
	
	var sidebar_a=document.getElementById('sidebar-a');
	sidebar_a.style.height=content.style.height;
	
	map_topleft_merc=[parseInt(${c.merc_x}-0.5*w),parseInt(${c.merc_y}-0.5*h)];
	if (map_topleft_merc[1]<0)
		map_topleft_merc[1]=0;


	tilestart=[map_topleft_merc[0],map_topleft_merc[1]];
	tilestart[0]=parseInt(tilestart[0]-(tilestart[0]%tilesize));
	tilestart[1]=parseInt(tilestart[1]-(tilestart[1]%tilesize));
	//alert('topleft merc x: '+map_topleft_merc[0]+' tilestart x: '+tilestart[0]);
	var tileoffset_x=tilestart[0]-map_topleft_merc[0];
	var tileoffset_y=tilestart[1]-map_topleft_merc[1];
	//alert('tileoffset x: '+tileoffset_x);
	var imgs='';
	xsegcnt=parseInt(Math.ceil(w/tilesize)+1.5);
	ysegcnt=parseInt(Math.ceil(h/tilesize)+1.5);
	var offy1=tileoffset_y;
	var mercy=tilestart[1];
	for(var iy=0;iy<ysegcnt;++iy)
	{
		var row=[];
		var offx1=tileoffset_x;
		var mercx=tilestart[0];
		for(var ix=0;ix<xsegcnt;++ix)
		{
			imgs+='<img style="border:0px;margin:0px;padding:0px;position:absolute;z-index:0;left:'+(offx1)+'px;top:'+
				(offy1)+'px;width:'+(tilesize)+'px;height:'+(tilesize)+'px" '+
				'id="mapid'+iy+''+ix+
				'" src="'+calctileurl(${c.zoomlevel},mercx,mercy)+'"/>';
			offx1+=tilesize
			mercx+=tilesize;
		}
		offy1+=tilesize;
		mercy+=tilesize;
	}

	content.innerHTML=''+
	'<div id="mapcontainer" style="overflow:hidden;position:absolute;z-index:1;left:'+left+'px;top:'+top+'px;width:'+w+'px;height:'+h+'px;">'+	
	imgs+
	'<div id="overlay1" style="overflow:hidden;position:absolute;z-index:1;left:'+0+'px;top:'+0+'px;width:'+w+'px;height:'+h+'px;"></div>'+
	'<div id="overlay2" style="overflow:hidden;position:absolute;z-index:2;left:'+0+'px;top:'+0+'px;width:'+w+'px;height:'+h+'px;"></div>'+
	'<div onmouseout="on_mouseout()" oncontextmenu="return on_rightclickmap(event)" onmousemove="on_mousemovemap(event)" onmouseup="on_mouseup(event)" onmousedown="on_mousedown(event)" id="overlay3" '+
	'style="overflow:hidden;position:absolute;z-index:3;left:'+0+'px;top:'+0+'px;width:'+w+'px;height:'+h+'px;"></div>'+
	'</div>'+	
	'<div id="mmenu" class="popup">'+
	'<div class="popopt" id="menu-insert" onclick="menu_insert_waypoint_mode()">Insert Waypoint</div>'+
	'<div class="popopt" id="menu-del" onclick="remove_waypoint()">Remove Waypoint</div>'+
	'<div class="popopt" id="menu-move" onclick="move_waypoint()">Move Waypoint</div>'+
	'<div class="popopt" onclick="center_map()">Center Map</div>'+ 
	'<div class="popopt" onclick="hidepopup()">Close menu</div>'+
	'</div>'+
	'<form id="helperform" action="${h.url_for(controller="mapview",action="zoom")}">'+
	'<input type="hidden" name="zoom" value="">'+
	'<input type="hidden" name="center" value="">'+
	'</form>'+
	'<div id="progmessage" class="progress-popup">'+
	''+
	'</div>'+
	'<div id="searchpopup" class="popup"></div>'	
	;
	
	var sidebar=document.getElementById('sidebar-a');
	sidebar.innerHTML=''+
	'<div class="first" id="search-pane">'+
	'<form id="searchform" action="">'+
	'Search:<input onkeydown="return on_search_keydown(event)" size="15" onkeyup="on_search_keyup(event)" onblur="remove_searchpopup()" id="searchfield" name="searchfield" type="text" value="" />'+	
	'</form>'+
	'</div>'+
	'<div class="first" id="trip-pane">'+
	'<form id="tripform" action="">'+
	'Trip:<input onkeypress="return not_enter(event)" id="entertripname" name="tripname" type="text" value="${c.tripname}" />'+
	'<input id="oldtripname" name="oldtripname" type="hidden" value="${c.tripname}" />'+
	'</form>'+
	'</div>'+
	'<div class="first"><form id="showdataformbuttons" action="">'+
	'Show on map:<br/>'+
	'<input type="checkbox" onchange="on_change_showairspace()" id="showairspaces" name="showairspaces" ${'checked="1"' if c.show_airspaces else ''|n} />Show airspaces'+
%if not c.showarea and not c.showtrack:
	'<br/><button onclick="visualize_track_data();return false" title="Show a point or track on the map, for example from a GPS logger.">Upload Track</button>'+
	'<br/><button onclick="visualize_area_data();return false" title="Show an area on the map, for example from NOTAM.">Upload Area</button>'+
%endif	
%if c.showtrack:
	'<br/><button onclick="clear_uploaded_data();return false" title="Clear uploaded track">Clear Track</button>'+
%endif	
%if c.showarea:
	'<br/><button onclick="clear_uploaded_data();return false" title="Clear uploaded area">Clear Area</button>'+
%endif	

	'</form></div>'+
	'<div class="first"><form id="fplanformbuttons" action="">'+
	'Waypoints:<br/>'+
	'<button onclick="remove_all_waypoints();return false" title="Remove all waypoints">Remove All</button>'+
	'<button onclick="menu_add_new_waypoints();return false" title="Add a new waypoint. Click here, then click start and end point in map.">Add</button>'+
	'</form></div>'+

	'<div id="mapinfo" class="first" style="display:none"></div>'+

	'<div class="first"><form id="fplanform" action="">'+
	'<table id="tab_fplan" width="100%">'+
	'</table></form></div>'+
	'<div style="display:block;background:#d0d0d0	" class="second" id="detail-pane">'+
	'<ul><li>Enter a name for your trip above.</li>'+
	'<li>Click the \'Add\' button above, then click in the map to enter waypoints.</li>'+
	'<li>Right click in the map to move or delete waypoints.</li></ul>'+
	'</div>'
	;
	
	
	map_ysize=h;
	map_xsize=w;

	var mercy=tilestart[1];
	var offy=tileoffset_y;
	for(var iy=0;iy<ysegcnt;++iy)
	{
		var mercx=tilestart[0];
		var offx=tileoffset_x;
		for(var ix=0;ix<xsegcnt;++ix)
		{
			var tile=new Object();
			tile.img=document.getElementById('mapid'+iy+''+ix);
			tile.mercx=parseInt(mercx);
			tile.mercy=parseInt(mercy);
			tile.x1=parseInt(offx);	
			tile.y1=parseInt(offy);	
			tiles.push(tile);
			offx+=tilesize;
			mercx+=tilesize;				
		}
		offy+=tilesize;
		mercy+=tilesize;
	}	
	
	
	
	jgq = new jsGraphics("overlay1");
	jgq.setStroke("3");
	jgq.setColor("#00ff00"); // green
	

	jg = new jsGraphics("overlay2");
	jg.setStroke("3");
	jg.setColor("#00d000"); 
	
	var idx=0;	
	%for wp in sorted(c.waypoints,key=lambda x:x.ordinal):	
	var me=latlon2merc([${wp.get_lat()},${wp.get_lon()}]);
	wps.push([me[0],me[1]]);
	tab_add_waypoint(idx,me,'${wp.pos}','${wp.waypoint}');
	idx++;
	%endfor
	draw_jg();
	anychangetosave=0;
	setInterval("if (anychangetosave!=0) save_data(null)", 30*1000);
	
	
}

addLoadEvent(loadmap);

</script>


	
