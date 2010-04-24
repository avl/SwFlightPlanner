
use_great_circles=0;



opinprogress=0;
function save_data(cont)
{
	if (opinprogress==1)
	{
		return;
	}
	var progm=document.getElementById("progmessage");
	function save_data_cb(req)
	{	
		opinprogress=0;
		if (req.responseText=='ok')
		{
			progm.style.display='none';
			cont();		
		}
		else
		{
			progm.innerHTML='Error: '+escape(req.responseText);
		}
	}
	progm.innerHTML='Saving...';
	progm.style.display='block';
	
	var glist=document.getElementById('tab_fplan');
	var params={};
	for(var i=0;i<glist.rows.length;i++)
	{
		var rowelem=glist.rows[i];		
		var namefield=rowelem.cells[1].childNodes[0];
		var posfield=rowelem.cells[2].childNodes[0];
		var origposfield=rowelem.cells[2].childNodes[1];
		params[namefield.name]=namefield.value;
		params[posfield.name]=posfield.value;
		params[origposfield.name]=origposfield.value;
	}			
	params['tripname']=document.getElementById('entertripname').value;
	params['oldtripname']=document.getElementById('oldtripname').value;
	var def=doSimpleXMLHttpRequest(saveurl,
		params);
	def.addCallback(save_data_cb);
}


function tab_modify_pos(idx,pos)
{
	var glist=document.getElementById('tab_fplan');
	var rowpos=glist.rows[idx].cells[2].childNodes[0];
	var latlon=to_latlon(pos);
	rowpos.value=''+latlon[0]+','+latlon[1];	
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
		rowelem.cells[2].childNodes[1].name='row_'+i+'_origpos';
	}	
}
function tab_select_waypoints(idxs,col)
{
	var glist=document.getElementById('tab_fplan');
	
	for(var i=0;i<glist.rows.length;i++)
	{
		var rowelem=glist.rows[i];
		var present=0;
		for(var j=0;j<idxs.length;++j)
			if (idxs[j]==i)
				present=1;
		if (idxs.length>0 && present)
			rowelem.style.backgroundColor=col;
		else
			rowelem.style.backgroundColor='#ffffff';
	}
	var pane=document.getElementById('detail-pane');
	if (idxs.length==0)
	{
		pane.innerHTML='';
		pane.style.display='none';
	}
	if (idxs.length==1)
	{
		var idx=idxs[0];		
		var name=glist.rows[idx].cells[1].childNodes[0].value;
		pane.innerHTML=''+
			'<h2>'+name+'</h2>'+
			'<p><b>Position:</b>'+aviation_format_pos(to_latlon(wps[idx]))+'</p>'+
			''+
			''+
			'';
		pane.style.backgroundColor="#a0a0ff";
		pane.style.display='block';
	}
	if (idxs.length==2)
	{
		var idx1=idxs[0];
		var idx2=idxs[1];
		var name1=glist.rows[idx1].cells[1].childNodes[0].value;
		var name2=glist.rows[idx2].cells[1].childNodes[0].value;
		pane.innerHTML=''+
			'<h2>'+name1+' - '+name2+'</h2>'+
			'<p><b>Distance:</b> '+format_distance(dist_between(to_latlon(wps[idx1]),to_latlon(wps[idx2])))+'</p>'+
			'<p><b>True Heading:</b> '+format_heading(heading_between(to_latlon(wps[idx1]),to_latlon(wps[idx2])))+'</p>'+
			''+
			''+
			'';
		pane.style.backgroundColor="#ffa0a0";
		pane.style.display='block';
		
		
	}
	
}
function to_latlon_str(pos)
{
	latlon=to_latlon(pos);
	return ''+latlon[0]+','+latlon[1];
}
function tab_add_waypoint(idx,pos,origpos)
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
   	var latlon=to_latlon(pos);
    elem.innerHTML=''+
    '<td>#'+idx+':</td>'+
    '<td><input type="text" name="row_'+idx+'_name" value=""/></td>'+
    '<td>'+
    '<input type="hidden" name="row_'+idx+'_pos" value="'+latlon[0]+','+latlon[1]+'"/>'+
    '<input type="hidden" name="row_'+idx+'_origpos" value="'+origpos+'"/>'+
    '</td>'+
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

function dozoom(how,pos)
{
	var form=document.getElementById('helperform');
	form.zoom.value=''+how;
	
	var latlon=to_latlon(pos);
	var lat=latlon[0];
	var lon=latlon[1];
	form.center.value=''+lat+','+lon;
		
	form.submit();
}
function zoom_out(pos)
{
	function zoom_out_impl()
	{
		dozoom(1,pos);
	}
 	save_data(zoom_out_impl);
}
function zoom_in(pos)
{
	function zoom_in_impl()
	{
		dozoom(-1,pos);
	}
 	save_data(zoom_in_impl);
}
function handle_mouse_wheel(delta,event) 
{
	var relx=get_rel_x(event.clientX);
	var rely=get_rel_y(event.clientY);
	if (delta>0)
		zoom_in([relx,rely]);
	if (delta<0)
		zoom_out([relx,rely]); 		
}


map_ysize=0;
map_xsize=0;
PI=3.1415926535897931;


function aviation_format_pos(latlon)
{
	lat=latlon[0];
	lon=latlon[1];
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
function clippoint(x1,y1)
{
	var in1=(x1>5 && y1>5 && x1<map_xsize-5 && y1<map_ysize-5);
	return in1;
}
function clipline(x1,y1,x2,y2)
{
	if (x1>x2)
	{
		var tx=x1;
		x1=x2;
		x2=tx;
		var ty=y1;
		y1=y2;
		y2=ty;
	}
	if (Math.abs(x1-x2)<0.1)
	{
		var miny=Math.min(y1,y2);
		var maxy=Math.max(y1,y2);
		return [x1,Math.max(miny,0),x1,Math.min(maxy,map_ysize)];
	}
	var in1=(x1>=0 && y1>=0 && x1<=map_xsize && y1<=map_ysize);
	var in2=(x2>=0 && y2>=0 && x2<=map_xsize && y2<=map_ysize);
	
	if (in1 && in2)
		return [x1,y1,x2,y2];
	var k=(y2-y1)/(x2-x1);
	var m=(y1-k*x1);
	if (x1>map_xsize && x2>map_xsize) return [];
	if (x1<0 && x2<0) return [];
	if (y1>map_ysize && y2>map_ysize) return [];
	if (y1<0 && y2<0) return [];
	if (!in1)
	{
		var isecty_left=0*k+m;
		var isectx_left=0;
		if (isecty_left<0)
		{
			isectx_left=-isecty_left/k;
			if (isectx_left>map_xsize)
				return [];
			isecty_left=0;
		}
		if (isecty_left>map_ysize)
		{
			isectx_left=-(isecty_left-map_ysize)/k;
			
			if (isectx_left>map_xsize)
				return [];
			isecty_left=map_ysize;
		}
		x1=isectx_left;
		y1=isecty_left;
	}
	if (!in2)
	{
		var isecty_right=map_xsize*k+m;
		var isectx_right=map_xsize;
		if (isecty_right<0)
		{
			isectx_right=map_xsize - isecty_right/k;
			
			if (isectx_right<0)
				return [];
			isecty_right=0;
		}
		if (isecty_right>map_ysize)
		{
			isectx_right=map_xsize-(isecty_right-map_ysize)/k;
			if (isectx_right<0)
				return [];
			isecty_right=map_ysize;
		}
		x2=isectx_right;
		y2=isecty_right;
	}
		
	return [x1,y1,x2,y2];	
}
function draw_great_circle(curw,endw)
{
	var cur=to_latlon(curw);
	var end=to_latlon(endw);
	var dist=dist_between(cur,end);
	var numseg=dist/150000.0;	
	if (numseg<2)
	{
		var l=clipline(
			curw[0],
			curw[1],
			endw[0],
			endw[1]
			);
		if (l.length)
 			jg.drawLine(
	    		l[0],l[1],l[2],l[3] 			
    			);
	}
	else
	{
		ps=great_circle_points(cur,end,parseInt(numseg));		
		for(var i=1;i<ps.length;++i)
		{
				//alert('GC: '+(ps[i-1]));
			var l=clipline(
			    to_merc(ps[i-1])[0],
				to_merc(ps[i-1])[1],
				to_merc(ps[i])[0],
				to_merc(ps[i])[1]
				);
			if (l.length)
	 			jg.drawLine(
		    		l[0],l[1],l[2],l[3]
					);
			
 			/*jg.drawLine(
	    		abs_x(to_merc(cur)[0]),
				abs_y(to_merc(cur)[1]),
				abs_x(to_merc(end)[0]),
				abs_y(to_merc(end)[1])
				);*/
			
		}
		
	}
			    			
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
	if (waypointstate!='none')
	{
		waypointstate='none';
		
		jgq.clear();
		draw_jg();
		return false;
	}	
	jgq.clear();
	var relx=get_rel_x(event.clientX);
	var rely=get_rel_y(event.clientY);
	lastrightclickx=relx;
	lastrightclicky=rely;
	
	var clo=get_close_line(relx,rely);
	var cm=document.getElementById("mmenu");
	
	if (clo.length==3)
	{ //A line nearby	
		document.getElementById("menu-add").innerHTML="Insert waypoint";	
	}
	else
	{
		if (wps.length==0)		
			document.getElementById("menu-add").innerHTML="Add starting point";
		else
			document.getElementById("menu-add").innerHTML="Add destination";			
	}
	var closest_i=get_close_waypoint(lastrightclickx,lastrightclicky);
	if (closest_i==-1)
	{
		document.getElementById('menu-move').style.display='none';
		document.getElementById('menu-del').style.display='none';
	}
	else
	{
		document.getElementById('menu-move').style.display='block';
		document.getElementById('menu-del').style.display='block';
	}
		
	cm.style.display="block";
	popupvisible=1;
	
	cm.style.left=''+event.clientX+'px';
	cm.style.top=''+event.clientY+'px';
	return false;
}

function abs_x(x)
{
	return parseInt(x);
}
function abs_y(y)
{
	return parseInt(y);
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

	for(var pass=0;pass<2;pass++)
	{		
	    for(var i=0;i<wps.length;i++)
	    {
	    	if (waypointstate!='moving' || (
	    		i-1!=movingwaypoint && i!=movingwaypoint))
	    	{
	    		if (pass==0)
	    		{
		    		if (i!=0)    		
		    		{    			
		    			if (selected_route_idx==i-1)
		    				jg.setColor("#ffa0a0"); // green
		    			else
		    				jg.setColor("#00bf00");
						
						if (use_great_circles)
						{
							draw_great_circle(
								wps[i-1],wps[i]);
						}
						else
						{				
						var l=clipline(
							wps[i-1][0],
			    			wps[i-1][1],
			    			wps[i][0],
			    			wps[i][1]
			    			);			
			    		if (l.length)	    			
		    				jg.drawLine(
			    				l[0],l[1],l[2],l[3]
				    			);
				    	}
			    	}
			    }
			    if (pass==1)
			    {	
			    	if (selected_waypoint_idx==i)
			    	{
			    		if (clippoint(wps[i][0],wps[i][1]))
			    		{
				    		jg.setColor("#0000bf");
					    	jg.fillEllipse(abs_x(wps[i][0])-5,abs_y(wps[i][1])-5,10,10);
				    		jg.setColor("#ffffff");
				    		jg.fillEllipse(abs_x(wps[i][0])-3,abs_y(wps[i][1])-3,6,6);
				    	}
			    	}
			    	else
			    	{
			    		if (clippoint(wps[i][0],wps[i][1]))
			    		{
				    		jg.setColor("#00bf00");
					    	jg.fillEllipse(abs_x(wps[i][0])-5,abs_y(wps[i][1])-5,10,10);
				    		jg.setColor("#ffffff");
				    		jg.fillEllipse(abs_x(wps[i][0])-3,abs_y(wps[i][1])-3,6,6);
				    	}			    	
			    	}			    	
				    
				}
			}
	    }
	}    
    jg.paint();
}

waypointstate='none';
anchorx=-1;
anchory=-1;
jg=0;
jgq=0;
selected_route_idx=-1;
selected_waypoint_idx=-1;

function select_route(startidx)
{
	selected_route_idx=-1;
	if (selected_waypoint_idx!=-1)
		select_waypoint(-1);
	selected_route_idx=startidx;
	if (selected_route_idx!=-1)
		tab_select_waypoints([selected_route_idx,selected_route_idx+1],'#ffa0a0');
	else
		tab_select_waypoints([],'#ffa0a0');
	draw_jg();
}
function select_waypoint(idx)
{
	selected_waypoint_idx=-1;
	if (selected_route_idx!=-1)
		select_route(-1);	
	selected_waypoint_idx=idx;
	if (selected_waypoint_idx!=-1)
		tab_select_waypoints([selected_waypoint_idx],'#a0a0ff');
	else
		tab_select_waypoints([],'#a0a0ff');
	draw_jg();			
}

function check_and_clear_selections()
{
	ret=0;
	if (selected_route_idx!=-1)
	{
		select_route(-1);
		ret=1;
	}
	if (selected_waypoint_idx!=-1)
	{
		select_waypoint(-1);
		ret=1;
	}
	return ret;
}


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
		tab_add_waypoint(wps.length,[relx,rely],to_latlon_str([relx,rely]));
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
			if (!check_and_clear_selections())
			{
				anchorx=relx;
				anchory=rely;		
				tab_add_waypoint(wps.length,[relx,rely],to_latlon_str([relx,rely]));
				wps.push([anchorx,anchory]);
				waypointstate='addwaypoint';
			}
		}
		else
		{	
			var closest_i=get_close_waypoint(get_rel_x(event.clientX),get_rel_y(event.clientY));
			if (closest_i==-1)
			{			
				var clo=get_close_line(relx,rely);
				if (clo.length==3)
				{
					select_route(clo[0]);
				}
				else
				{
					if (!check_and_clear_selections())				
					{
						anchorx=wps[wps.length-1][0];
						anchory=wps[wps.length-1][1];
						waypointstate='addwaypoint';
						draw_jg();
						draw_dynamic_lines(relx,rely);
					}		
				}
			}
			else
			{
				select_waypoint(closest_i);
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
		{
			l=clipline(wps[movingwaypoint-1][0],wps[movingwaypoint-1][1],cx,cy);
			if (l.length>0)
				jgq.drawLine(l[0],l[1],l[2],l[3]);
		}
		if (movingwaypoint!=wps.length-1)
		{
			l=clipline(wps[movingwaypoint+1][0],wps[movingwaypoint+1][1],cx,cy);
			if (l.length>0)
				jgq.drawLine(l[0],l[1],l[2],l[3]);
		}
		jgq.paint();
		
	}
}

last_mousemove_lat=-90;
last_mousemove_lon=-360;

function on_mousemovemap(event)
{
	var latlon=to_latlon([get_rel_x(event.clientX),get_rel_y(event.clientY)]);
	var lat=latlon[0];
	var lon=latlon[1];
	last_mousemove_lat=lat;
	last_mousemove_lon=lon;
	document.getElementById("footer").innerHTML=aviation_format_pos(latlon);
		
	draw_dynamic_lines(get_rel_x(event.clientX),get_rel_y(event.clientY));
}
function get_close_waypoint(relx,rely)
{
	var closest_i=0;
	var closest_dist=1e12;
	for(var i=0;i<wps.length;i++)
	{
		dist=Math.sqrt((wps[i][0]-relx)*(wps[i][0]-relx)+(wps[i][1]-rely)*(wps[i][1]-rely));
		if (dist<closest_dist)
		{
			closest_i=i;closest_dist=dist;
		}			
	}
	
	if (closest_dist<30)
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
	if (closest_i!=-1)
	{
		waypointstate='moving';
		movingwaypoint=closest_i;	
		draw_jg();
		draw_dynamic_lines(lastrightclickx,lastrightclicky);
	}	
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
		tab_add_waypoint(clo[0],[relx,rely],to_latlon_str([relx,rely]));
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
	var latlon=to_latlon([lastrightclickx,lastrightclicky]);
	var lat=latlon[0];
	var lon=latlon[1];
	var form=document.getElementById('helperform');
	form.center.value=''+lat+','+lon;
	form.submit();	
}

