
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
next_waypoint_id=${c.next_waypoint_id};
selfurl='${h.url_for(controller="mapview",action="index")}';
shareurl='${h.url_for(controller="mapview",action="share")}';
saveurl='${h.url_for(controller="mapview",action="save")}';
coordparseurl='${h.url_for(controller="mapview",action="coordparse")}';
searchairporturl='${h.url_for(controller="flightplan",action="search")}';
showareaurl='${h.url_for(controller="mapview",action="showarea")}';
mapinfourl='${h.url_for(controller="maptile",action="get_airspace")}';
dynamic_id='${c.dynamic_id}'; /*Id to keep different tiles uniquely named - needed since we allow the browser to cache the tiles*/
uploadtrackurl='${h.url_for(controller="mapview",action="upload_track")}';
fastmap=${"1" if c.fastmap else "0"};
mapvariant='${c.mapvariant}';
overlay_left=0;
overlay_top=0;

function calctileurl(zoomlevel,mercx,mercy)
{
	return '/maptile/get?zoom='+zoomlevel+'&mercx='+mercx+'&mercy='+mercy+'&mapvariant='+mapvariant+'&dynamic_id='+dynamic_id+'&mtime=${c.mtime}';
}

merc5_limx1=${c.merc5_limx1};
merc5_limy1=${c.merc5_limy1};
merc5_limx2=${c.merc5_limx2};
merc5_limy2=${c.merc5_limy2};

function clip_mappos(mercx,mercy)
{
	var a=merc2merc([merc5_limx1,merc5_limy1],5,map_zoomlevel);
	var b=merc2merc([merc5_limx2,merc5_limy2],5,map_zoomlevel);
    if (mercx+screen_size_x>b[0]) mercx=b[0]-screen_size_x;
    if (mercy+screen_size_y>b[1]) mercy=b[1]-screen_size_y;
    if (mercx<a[0]) mercx=a[0];
    if (mercy<a[1]) mercy=a[1];

    return [mercx,mercy];
}

function loadmap()
{
	document.getElementById('sidebar-a').style.width='276px';
	document.getElementById('content').style.marginRight='282px';

    force_refresh_on_back_button('${h.url_for(controller="mapview",action="index")}','maprefresh');


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
	map_topleft_merc=clip_mappos(map_topleft_merc[0],map_topleft_merc[1]);


	content.innerHTML=''+
	'<div id="mapcontainer" style="overflow:hidden;position:absolute;z-index:1;left:'+left+'px;top:'+top+'px;width:'+w+'px;height:'+h+'px;"'+
    'onmouseout="on_mouseout();return false;" oncontextmenu="return on_rightclickmap(event);return false;" onmousemove="on_mousemovemap(event);return false;" onmouseup="on_mouseup(event);return false;" onmousedown="on_mousedown(event);return false;">'+
	'</div>'+	
	
	'<div id="mmenu" class="popup">'+	
	'<div class="popopt" id="menu-insert" onclick="menu_insert_waypoint_mode()">Insert Waypoint</div>'+
	'<div class="popopt" id="menu-del" onclick="remove_waypoint()">Remove Waypoint</div>'+
	'<div class="popopt" id="menu-move" onclick="move_waypoint()">Move Waypoint</div>'+
	'<div class="popopt" onclick="center_map()">Center Map</div>'+ 
	'<div class="popopt" onclick="add_waypoint_here(event);">Add Waypoint Here</div>'+ 
	'<div class="popopt" onclick="hidepopup()">Close menu</div>'+
	'</div>'+
	'<div id="entercoord" class="opopup" style="display:none">'+
	'<h2>Enter coordinates:</h2>'+
	'<div>'+
	'<input type="text" id="coordfield" onchange="oncoordchange()" onkeyup="oncoordchange()"/>'+
	'<div id="coordresult">Enter a coordinate in any format</br>in the field above'+
	'</div>'+
	'</div>'+
	'<button onclick="enter_coordinate_addwp();return false;">Add Waypoint</button>'+
	'<button onclick="enter_coordinate_center();return false;">Center on map</button>'+
	'<button onclick="enter_coordinate_close();return false;">Close</button>'+
	'</div>'+
	'<form id="helperform" action="${h.url_for(controller="mapview",action="zoom")}">'+
	'<input type="hidden" name="zoom" value="" />'+
	'<input type="hidden" name="center" value="" />'+
	'</form>'+
	'<div id="progmessage" class="progress-popup">'+
	''+
	'</div>'+
	'<div id="searchpopup" class="popup"></div>'	
	;
	
	var sidebar=document.getElementById('sidebar-a');
	sidebar.innerHTML=''+
	'<div class="first" id="search-pane" onkeydown="return on_search_keydown(event)" size="15" onkeyup="on_search_keyup(event)">'+
	'<form id="searchform" action="" onblur="remove_searchpopup()" >'+
	'Search Destination:<span id="searchprogtext" style="display:none">searching...</span> <br/><input style="background:#ffffc0" id="searchfield"  name="searchfield" type="text" value="" />'+
	'<button onclick="mapsearch_add_to_route_button();return false;" style="font-size:10px">Add</button>'+	
	'</form>'+
	'</div>'+
	'<div class="first" id="trip-pane">'+
	'<form id="tripform" action="${h.url_for(controller="mapview",action="trip_actions")}" method="POST">'+
	'Trip Name:<br/><input style="background:#c0ffc0" onchange="setdirty();" onkeydown="setdirty();return not_enter(event)" onkeypress="setdirty();return not_enter(event)" ${"readonly=\"readonly\"" if c.sharing else ""|n} id="entertripname" name="tripname" type="text" value="${h.jsescape(c.tripname)}" />'+
	'<button style="font-size:10px" onclick="more_trip_functions();return false;">more</button>'+
	%if c.sharing:
	'<br/><span style="font-size:9px">(Trip owner: ${c.shared_by})</span>'+
	%endif
	'<div id="moretripfunctions" style="display:none">'+
	'<button style="font-size:10px" onclick="add_new_trip();return false;">New</button>'+
%if not c.sharing:
	'<button style="font-size:10px" onclick="on_delete_trip();return false;">Delete</button>'+
%endif
	'<button style="font-size:10px" onclick="open_trip();return false;">Previous Trips</button>'+
	'<button style="font-size:10px" onclick="navigate_to(shareurl);return false;">Share Trip</button>'+
	'</div>'+
	'<div id="addtripfunctions" style="display:none">'+
	'Enter name of new trip:<br/><input style="background:#c0ffc0" id="addtripname" name="addtripname" type="text" value="" />'+
	'<button style="font-size:10px" onclick="on_add_trip();return false;">Add</button>'+	
	'</div>'+
	'<div id="opentripfunctions" style="display:none">'+

%if len(c.all_trips)>1 or (len(c.all_trips)==1 and c.all_trips[0].trip!=c.tripname):
'Other saved trips:<br/><select name="choose_trip" id="choose_trip">'+
%for ctrip in sorted(c.all_trips,key=lambda x:x.trip):
%if ctrip.trip!=c.tripname:
'<option>'+
'${ctrip.trip}'+
'</option>'+
%endif
%endfor
'</select>'+
	'<button onclick="on_open_trip();return false;">Open</button>'+	
%endif
%if not (len(c.all_trips)>1 or (len(c.all_trips)==1 and c.all_trips[0].trip!=c.tripname)):
'You have no saved trips!'+
%endif
	'</div>'+
	'<input id="oldtripname" name="oldtripname" type="hidden" value="${h.jsescape(c.tripname)}" />'+
	'<input id="deletetripname" name="deletetripname" type="hidden" value="" />'+
	'<input id="opentripname" name="opentripname" type="hidden" value="" />'+
	'</form>'+
	'</div>'+
	'<div class="first"><form id="showdataformbuttons" action="">'+
	'Show on map:'+
	'<select style="font-size:10px" onchange="on_change_mapvariant()" id="mapvariant" name="mapvariant"/>'+
    '<option value="plain" ${'selected="selected"' if c.mapvariant=='plain' else ''}>Regular</option>'+
    '<option value="airspace" ${'selected="selected"' if c.mapvariant=='airspace' else ''}>Airspace</option>'+
    '<option value="elev" ${'selected="selected"' if c.mapvariant=='elev' else ''}>Elevation</option>'+
    '</select>'+
	'<br/><button style="font-size:10px" onclick="zoom_in([map_topleft_merc[0]+screen_size_x/2,map_topleft_merc[1]+screen_size_y/2]);return false;">Zoom in</button>'+
	'<button style="font-size:10px" onclick="zoom_out([map_topleft_merc[0]+screen_size_x/2,map_topleft_merc[1]+screen_size_y/2]);return false;">Zoom out</button>'+

%if not c.showarea and not c.showtrack:
	'<br/><button style="font-size:10px"  onclick="visualize_track_data();return false" title="Show a point or track on the map, for example from a GPS logger.">Upload Track</button>'+
	'<button style="font-size:10px"  onclick="visualize_area_data();return false" title="Show an area on the map, for example from NOTAM.">Upload Area</button>'+	
%endif	
	'<button style="font-size:10px"  onclick="enter_coordinate();return false" title="Enter a coordinate.">Enter coordinate</button>'+
%if c.showtrack:
	'<br/><button style="font-size:10px" onclick="clear_uploaded_data();return false" title="Clear uploaded track">Clear Track</button>'+
%endif	
%if c.showarea:
	'<br/><button style="font-size:10px" onclick="clear_uploaded_data();return false" title="Clear uploaded area">Clear Area</button>'+
%endif	

	'</form></div>'+
	'<div class="first"><form id="fplanformbuttons" action="">'+
	'Route/Waypoints:<br/>'+
	'<button onclick="remove_all_waypoints();return false" style="font-size:10px" title="Remove all waypoints">Remove All</button>'+
	'<button onclick="menu_add_new_waypoints();return false" style="font-size:10px" title="Add a new waypoint. Click here, then click start and end point in map.">Add on Map</button>'+
	'</form><form id="fplanform" action="">'+
	'<table id="tab_fplan" width="100%">'+
	'</table></form></div>'+

	'<div id="mapinfo" class="first" style="display:none"></div>'+

	
	'<div style="display:block;background:#d0d0d0	" class="second" id="detail-pane">'+
	'<ul><li>Enter a name for your trip above (under Trip Name).</li>'+
	'<li>Click the \'Add on Map\' button above, then click in the map to enter waypoints.</li>'+
	'<li>Right click to stop adding waypoints.</li>'+
	'<li>Right click again in the map to move or delete waypoints.</li></ul>'+
	'</div>'
	;
	
	
	
	map_ysize=h;
	map_xsize=w;
    
	
	
	
	
	var idx=0;	
	%for wp in sorted(c.waypoints,key=lambda x:x.ordering):	
	var me=latlon2merc([${wp.get_lat()},${wp.get_lon()}]);
	wps.push([me[0],me[1]]);
	tab_add_waypoint(idx,me,${wp.id},'${h.jsescape(wp.waypoint)|n}','${h.jsescape(wp.altitude)|n}');
	idx++;
	%endfor
	
	reload_map();
	
	draw_jg();
	setInterval("if (getisdirty()) save_data(null)", 5*1000);
	
	register_foldedlink_hook(save_data);

	
}

addLoadEvent(loadmap);

</script>



	
