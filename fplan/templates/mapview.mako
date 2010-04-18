
<%inherit file="base.mako"/>


<script type="text/javascript" src="/wz_jsgraphics.js"></script>



<script type="text/javascript">

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
	var cm=document.getElementById("mmenu");
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
		wps.push([get_rel_x(event.clientX),get_rel_y(event.clientY)]);
		waypointstate='none';
		jgq.clear();
		draw_jg();
		return;		
	}
	else if (waypointstate=='moving')
	{
		wps[movingwaypoint]=[get_rel_x(event.clientX),get_rel_y(event.clientY)];
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
					var tmpwps=[];
					for(var i=0;i<wps.length;i++)
					{						
						tmpwps.push(wps[i]);
						if (i==clo[0])
							tmpwps.push([clo[1],clo[2]]);
					}
					wps=tmpwps;
					waypointstate='moving';
					movingwaypoint=clo[0]+1;						
					draw_jg();
					draw_dynamic_lines(event.clientX,event.clientY);
				}
				else
				{
					anchorx=wps[wps.length-1][0];
					anchory=wps[wps.length-1][1];
					waypointstate='addwaypoint';
					draw_jg();
					draw_dynamic_lines(event.clientX,event.clientY);		
				}
			}
			else
			{
				waypointstate='moving';
				movingwaypoint=closest_i;	
				draw_jg();
				draw_dynamic_lines(event.clientX,event.clientY);		
			}
		}
		
		draw_dynamic_lines(event.clientX,event.clientY);
	}

}

function draw_dynamic_lines(cx,cy)
{
	if (waypointstate=='addwaypoint')
	{
		jgq.clear();
		jgq.drawLine(abs_x(anchorx),abs_y(anchory),cx,cy);
		jgq.paint();
	}
	else if (waypointstate=='moving')
	{
		jgq.clear();
		if (movingwaypoint!=0)
			jgq.drawLine(abs_x(wps[movingwaypoint-1][0]),abs_y(wps[movingwaypoint-1][1]),cx,cy);
		if (movingwaypoint!=wps.length-1)
			jgq.drawLine(abs_x(wps[movingwaypoint+1][0]),abs_y(wps[movingwaypoint+1][1]),cx,cy);
		jgq.paint();
		
	}
}

function on_mousemovemap(event)
{
	document.getElementById("footer").innerHTML=''+get_rel_x(event.clientX)+','+get_rel_y(event.clientY);
	draw_dynamic_lines(event.clientX,event.clientY);
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
	
	if (closest_dist<100)
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
		draw_jg();		
	}
}

function close_menu()
{
	hidepopup();
}
function go_add_waypoint_mode()
{
	hidepopup();
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
	'<div class="popopt" onclick="go_add_waypoint_mode()">Add Waypoint</div>'+
	'<div class="popopt" onclick="remove_waypoint()">Remove Waypoint</div>'+
	'<div class="popopt" onclick="move_waypoint()">Move Waypoint</div>'+
	'<div class="popopt" onclick="close_menu()">Close menu</div>'+
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


	