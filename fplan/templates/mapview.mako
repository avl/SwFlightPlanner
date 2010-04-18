
<%inherit file="base.mako"/>


<script type="text/javascript" src="/wz_jsgraphics.js"></script>



<script type="text/javascript">

wps=[];

popupvisible=0;
function hidepopup()
{
	var cm=document.getElementById("mmenu");
	cm.style.display="none";
	popupvisible=0;
}

lastrightclickx=0
lastrightclicky=0
function on_rightclickmap(event)
{	
	var cm=document.getElementById("mmenu");
	cm.style.display="block";
	lastrightclickx=get_rel_x(event.clientX);
	lastrightclicky=get_rel_y(event.clientY);
	
	cm.style.left=''+event.clientX+'px';
	cm.style.top=''+event.clientY+'px';
	return false;
}
function abs_x(x)
{
	return x+document.getElementById('mapid').offsetLeft;
}
function abs_y(y)
{
	return y+document.getElementById('mapid').offsetTop;
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
    for(var i=1;i<wps.length;i++)
    {
    	jg.drawLine(
    		abs_x(wps[i-1][0]),
    		abs_y(wps[i-1][1]),
    		abs_x(wps[i][0]),
    		abs_y(wps[i][1]));
    }    
    jg.paint();
}

waypointstate='pristine';
anchorx=-1;
anchory=-1;
jg=0;
jgq=0;

function on_clickmap(event)
{
	if (popupvisible)
	{
		hidepopup();		
		return;	
	}	
	if (waypointstate=='addwaypoint')
	{
		wps.push([get_rel_x(event.clientX),get_rel_y(event.clientY)]);
		waypointstate='none';
		jgq.clear();
		draw_jg();
		return;		
	}
	else
	{
		if (waypointstate=='pristine')
		{
			anchorx=get_rel_x(event.clientX);
			anchory=get_rel_y(event.clientY);		
			wps.push([anchorx,anchory]);
		}
		else
		{
			anchorx=wps[wps.length-1][0];
			anchory=wps[wps.length-1][1];
		}
		waypointstate='addwaypoint';
	}

}
function on_mousemovemap(event)
{
	document.getElementById("footer").innerHTML=''+get_rel_x(event.clientX)+','+get_rel_y(event.clientY);
	if (waypointstate=='addwaypoint')
	{
		jgq.clear();
		jgq.drawLine(abs_x(anchorx),abs_y(anchory),event.clientX,event.clientY);
		jgq.paint();
	}
}
function remove_waypoint()
{

	hidepopup();
	var relx=lastrightclickx;
	var rely=lastrightclicky;
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
	var wpsout=[];
	
	if (closest_dist<30*30)
	{		
		for(var i=0;i<wps.length;++i)
		{
			if (i!=closest_i)
				wpsout.push([wps[i][0],wps[i][1]]);
		}
		wps=wpsout;
		draw_jg();		
	}
}

function go_add_waypoint_mode()
{
	hidepopup();
	if (waypointstate=='pristine')	
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
	
}

function loadmap()
{
	var content=document.getElementById('content')
	var h=content.offsetHeight;
	var w=content.offsetWidth;
	var left=content.offsetLeft;
	var top=content.offsetLeft;

		
	content.innerHTML='<img id="mapid" src="/maptile/get?pos=${c.pos}&latitudes=${c.size}&width='+(w-3)+'&height='+(h-3)+'"/>'+
	'<div id="overlay1" style="position:absolute;z-index:1;left:'+left+'px;top:'+top+'px;width:'+w+'px;height:'+h+'px;"></div>'+
	'<div oncontextmenu="return on_rightclickmap(event)" onmousemove="on_mousemovemap(event)" onclick="on_clickmap(event)" id="overlay2" style="position:absolute;z-index:2;left:'+left+'px;top:'+top+'px;width:'+w+'px;height:'+h+'px;"></div>'+
	'<div id="mmenu" class="popup">'+
	'hej'+
	'<ul>'+
	'<li class="popopt" onclick="go_add_waypoint_mode()">Add Waypoint</li>'+
	'<li class="popopt" onclick="remove_waypoint()">Remove Waypoint</li>'+
	'<li class="popopt" onclick="move_waypoint()">Move Waypoint</li>'+
	'<li class="popopt" onclick="close_menu()">Close menu</li>'+
	'</ul>'+
	'</div>'
	;
	
	
	
	jgq = new jsGraphics("overlay1");
	jgq.setStroke("3");
	jgq.setColor("#00ff00"); // green
	

	jg = new jsGraphics("overlay2");
	jg.setStroke("3");
	jg.setColor("#00d000"); 
	
	
	
}
addLoadEvent(loadmap);

</script>


	