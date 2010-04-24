
<%inherit file="base.mako"/>


<script src="/wz_jsgraphics.js" type="text/javascript"></script>
<script src="/MochiKit.js" type="text/javascript"></script>
<script src="/mwheel.js" type="text/javascript"></script>
<script src="/mapmath.js" type="text/javascript"></script>
<script src="/mapmain.js" type="text/javascript"></script>


<script type="text/javascript">

map_proj_lon=${c.lon};
map_proj_lonwidth=${c.lonwidth};
map_proj_lat=${c.lat};
map_proj_size=${c.size};
saveurl='${h.url_for(controller="mapview",action="save")}';
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
	'<div class="popopt" id="menu-del" onclick="remove_waypoint()">Remove Waypoint</div>'+
	'<div class="popopt" id="menu-move" onclick="move_waypoint()">Move Waypoint</div>'+
	'<div class="popopt" onclick="close_menu()">Close menu</div>'+
	'<div class="popopt" onclick="center_map()">Center Map</div>'+ 
	'</div>'+
	'<form id="helperform" action="${h.url_for(controller="mapview",action="zoom")}">'+
	'<input type="hidden" name="zoom" value="">'+
	'<input type="hidden" name="center" value="">'+
	'</form>'+
	'<div id="progmessage" class="progress-popup">'+
	''+
	'</div>'	
	;
	
	var sidebar=document.getElementById('sidebar-a');
	sidebar.innerHTML=''+
	'<div class="first" id="trip-pane">'+
	'<form id="tripform" action="">'+
	'Trip: <input id="entertripname" name="tripname" type="text" value="${c.tripname}" />'+
	'<input id="oldtripname" name="oldtripname" type="hidden" value="${c.tripname}" />'+
	'</form>'+
	'</div>'+
	'<div class="first"><form id="fplanform" action="">'+
	'<table id="tab_fplan" width="100%">'+
	'</table></form></div>'+
	'<div style="display:block;background:#d0d0d0	" class="second" id="detail-pane">'+
	'<ul><li>Enter a name for your trip above.</li>'+
	'<li>Click in the map to enter waypoints.</li>'+
	'<li>Right click in the map to move or delete waypoints.</li></ul>'+
	'</div>'
	;
	
	
	map_ysize=h;
	map_xsize=w;
	
	
	jgq = new jsGraphics("overlay1");
	jgq.setStroke("3");
	jgq.setColor("#00ff00"); // green
	

	jg = new jsGraphics("overlay2");
	jg.setStroke("3");
	jg.setColor("#00d000"); 
	
	var idx=0;	
	%for wp in sorted(c.waypoints,key=lambda x:x.ordinal):	
	var me=to_merc([${wp.get_lat()},${wp.get_lon()}]);
	wps.push([me[0],me[1]]);
	tab_add_waypoint(idx,me,'${wp.pos}');
	idx++;
	%endfor
	draw_jg();
	
	
}

addLoadEvent(loadmap);

</script>


	