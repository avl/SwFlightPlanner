
use_great_circles=0;

function provide_help(msg)
{
	var h=document.getElementById('detail-pane');
	h.style.background="#ffe0e0";
	h.style.display='block';
	h.innerHTML='<b>Hints:</b><br/>'+msg;
}

opinprogress=0;
anychangetosave=0;

function navigate_to(where)
{	
	function finish_nav()
	{				
		window.location.href=where;
	}
	save_data(finish_nav);
}
function save_data(cont)
{
	anychangetosave=0;
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
			if (cont!=null)
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
	anychangetosave=1;
	var glist=document.getElementById('tab_fplan');
	var rowpos=glist.rows[idx].cells[2].childNodes[0];
	var latlon=merc2latlon(pos);
	rowpos.value=''+latlon[0]+','+latlon[1];
		
}
function tab_remove_waypoint(idx)
{
	anychangetosave=1;
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
			'<p><b>Position:</b>'+aviation_format_pos(merc2latlon(wps[idx]))+'</p>'+
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
			'<p><b>Distance:</b> '+format_distance(dist_between(merc2latlon(wps[idx1]),merc2latlon(wps[idx2])))+'</p>'+
			'<p><b>True Heading:</b> '+format_heading(heading_between(merc2latlon(wps[idx1]),merc2latlon(wps[idx2])))+'</p>'+
			''+
			''+
			'';
		pane.style.backgroundColor="#ffa0a0";
		pane.style.display='block';
		
		
	}
	
}
function to_latlon_str(pos)
{
	latlon=merc2latlon(pos);
	return ''+latlon[0]+','+latlon[1];
}
function tab_add_waypoint(idx,pos,origpos,name)
{
	anychangetosave=1;
	
	if (name==null)
		name='Unnamed Waypoint';
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
   	
   	var latlon=merc2latlon(pos);
   	function onclick_waypoint()
   	{
   		select_waypoint(idx);
   	}
   	elem.onclick=onclick_waypoint;
    elem.innerHTML=''+
    '<td>#'+idx+':</td>'+
    '<td><input type="text" onkeypress="return not_enter(event)" name="row_'+idx+'_name" value="'+name+'"/></td>'+
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
	}
*/
}
keyhandler=on_key

function dozoom(how,pos)
{
	var form=document.getElementById('helperform');

	
	var mercx=pos[0];
	var mercy=pos[1];
	if (how==1 && map_zoomlevel<13)
	{
		mercx*=2.0;
		mercy*=2.0;
		map_zoomlevel+=1;
	}
	else if (how==-1 && map_zoomlevel>0)
	{
		mercx/=2.0;
		mercy/=2.0;
		map_zoomlevel-=1;
	}
	form.zoom.value=''+(map_zoomlevel);
	form.center.value=''+mercx+','+mercy;
		
	form.submit();
}
function zoom_out(pos)
{
	function zoom_out_impl()
	{
		dozoom(-1,pos);
	}
 	save_data(zoom_out_impl);
}
function zoom_in(pos)
{
	function zoom_in_impl()
	{
		dozoom(1,pos);
	}
 	save_data(zoom_in_impl);
}
function handle_mouse_wheel(delta,event) 
{
	var relx=client2merc_x(event.clientX);
	var rely=client2merc_y(event.clientY);
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
	var cur=merc2latlon(curw);
	var end=merc2latlon(endw);
	var dist=dist_between(cur,end);
	var numseg=dist/150000.0;	
	if (numseg<2)
	{
		var l=clipline(
			merc2screen_x(curw[0]),
			merc2screen_y(curw[1]),
			merc2screen_x(endw[0]),
			merc2screen_y(endw[1])
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
			    merc2screen_x(latlon2merc(ps[i-1])[0]),
	    		merc2screen_y(latlon2merc(ps[i-1])[1]),
				merc2screen_x(latlon2merc(ps[i])[0]),
				merc2screen_y(latlon2merc(ps[i])[1])
				);
			if (l.length)
	 			jg.drawLine(
		    		l[0],l[1],l[2],l[3]
					);
			
 			/*jg.drawLine(
	    		merc2screen_x(latlon2merc(cur)[0]),
				merc2screen_y(latlon2merc(cur)[1]),
				merc2screen_x(latlon2merc(end)[0]),
				merc2screen_y(latlon2merc(end)[1])
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
		if (wps.length==1)
		{
			provide_help('<ul><li>You have added a starting point, but no further waypoints. You need at least two points to define a journey!</li><li>Click the "Add" button above to add a new waypoint</li></ul>');
		}
		else
		{
			provide_help('<ul><li>Use the "Add" button up to the right to add more waypoints</li><li>To move or delete a waypoint, right-click it and choose add or delete.</li><li>To insert a new waypoint in the middle of the trip, right-click a track-line, and choose "Insert Waypoint".</li></ul>');
		}
		jgq.clear();
		draw_jg();
		return false;
	}	
	jgq.clear();
	var relx=client2merc_x(event.clientX);
	var rely=client2merc_y(event.clientY);
	lastrightclickx=relx;
	lastrightclicky=rely;
	
	var clo=get_close_line(relx,rely);
	var cm=document.getElementById("mmenu");
	found=0;
	if (clo.length==3)
	{ //A line nearby	
		document.getElementById("menu-insert").style.display='block';
		provide_help('<ul><li>You have right-clicked on a track line. You can insert a waypoint in the middle of it.</li><li>You can left-click on a track-line to get information about it.</li></ul>');
		found=1;				
			
	}
	else
	{
		document.getElementById("menu-insert").style.display='none';
	}
	var closest_i=get_close_waypoint(lastrightclickx,lastrightclicky);
	if (closest_i==-1)
	{
		document.getElementById('menu-move').style.display='none';
		document.getElementById('menu-del').style.display='none';
	}
	else
	{
		provide_help('<ul><li>You have right-clicked on a waypoint. You can move or delete it.</li><li>Left click on a waypoint to get information about it.</li></ul>');
		document.getElementById('menu-move').style.display='block';
		document.getElementById('menu-del').style.display='block';
		found=1;
	}
	if (!found)
		provide_help('<ul><li>Use the "Add" button up to the right to add new waypoints</li><li>Choose Center Map to center the feature you clicked on, in the middle of the screen.</li><li>Right click on an added waypoint or track-line to modify.</li></ul>');	
	cm.style.display="block";
	popupvisible=1;
	
	cm.style.left=''+event.clientX+'px';
	cm.style.top=''+event.clientY+'px';
	return false;
}

function merc2screen_x(merc_x)
{ //screen = map
	
	return parseInt(merc_x)-map_topleft_merc[0];
}
function merc2screen_y(merc_y)
{ //screen = map
	return parseInt(merc_y)-map_topleft_merc[1];
}
function client2merc_x(clientX)
{
	var screen_x=clientX-document.getElementById('mapcontainer').offsetLeft;
	return map_topleft_merc[0]+screen_x;
}
function client2merc_y(clientY)
{
	var screen_y=clientY-document.getElementById('mapcontainer').offsetTop;
	return map_topleft_merc[1]+screen_y;
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
								merc2screen_x(wps[i-1][0]),
								merc2screen_y(wps[i-1][1]),
								merc2screen_x(wps[i][0]),
								merc2screen_y(wps[i][1])
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
			    	var screen_x=merc2screen_x(wps[i][0]);
			    	var screen_y=merc2screen_y(wps[i][1]);
			    	if (selected_waypoint_idx==i)
			    	{
			    		if (clippoint(screen_x,screen_y))
			    		{
				    		jg.setColor("#20207f");
							jg.setFont("arial","14px",Font.BOLD);
							jg.drawString(''+i,screen_x+6,screen_y-5);			    		
				    		jg.setColor("#0000bf");
					    	jg.fillEllipse(screen_x-5,screen_y-5,10,10);
				    		jg.setColor("#ffffff");
				    		jg.fillEllipse(screen_x-3,screen_y-3,6,6);
				    	}
			    	}
			    	else
			    	{
			    		if (clippoint(screen_x,screen_y))
			    		{
			    			jg.setColor("#207f20");
							jg.setFont("arial","14px",Font.BOLD);
							jg.drawString(''+i,screen_x+7,screen_y-5);			    		
				    		jg.setColor("#00bf00");
					    	jg.fillEllipse(screen_x-5,screen_y-5,10,10);
				    		jg.setColor("#ffffff");
				    		jg.fillEllipse(screen_x-3,screen_y-3,6,6);
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

function add_waypoint(name,pos)
{
	var merc=latlon2merc(pos);
	relx=merc[0];
	rely=merc[1];
	tab_add_waypoint(wps.length,[relx,rely],to_latlon_str([relx,rely]),name);
	wps.push([relx,rely]);
	jgq.clear();
	draw_jg();
}

mouse_is_down=0;
var initial_mouse_down=[-100,-100];
function on_mouseout()
{
	mouse_is_down=0;
	end_drag_mode(last_mousemove_x,last_mousemove_y);
}
function on_mouseup(event)
{
	if (event.which!=1)
	{	 //not left button
		return true;
	}
	mouse_is_down=0;
	if (end_drag_mode(event.clientX,event.clientY))
		return false;

	relx=client2merc_x(event.clientX);
	rely=client2merc_y(event.clientY);
	
	if (wps.length>0)
		extra='<li>Left click on a waypoint or track-line to get more information about it.</li>';
	else
		extra='';
	provide_help('<ul><li>Use the "Add"-button above to add new waypoints.</li>'+extra+'</ul>');				
	
	if (popupvisible)
	{
	
		hidepopup();		
		return;	
	}	
	if (waypointstate=='addwaypoint' || waypointstate=='addfirstwaypoint')
	{
		tab_add_waypoint(wps.length,[relx,rely],to_latlon_str([relx,rely]),null);
		wps.push([client2merc_x(event.clientX),client2merc_y(event.clientY)]);

		anchorx=wps[wps.length-1][0];
		anchory=wps[wps.length-1][1];
		waypointstate='addwaypoint';
		provide_help('<ul><li>Place your next waypoint.</li><li>When you are finished, right-click anywhere in the map</il></ul>');
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
			{/*
				anchorx=relx;
				anchory=rely;		
				tab_add_waypoint(wps.length,[relx,rely],to_latlon_str([relx,rely]),null);
				wps.push([anchorx,anchory]);
				waypointstate='addwaypoint';
				*/
			}
		}
		else
		{	
			var closest_i=get_close_waypoint(client2merc_x(event.clientX),client2merc_y(event.clientY));
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
					{/*
						anchorx=wps[wps.length-1][0];
						anchory=wps[wps.length-1][1];
						waypointstate='addwaypoint';
						draw_jg();
						draw_dynamic_lines(relx,rely);
						*/
					}		
				}
			}
			else
			{
				select_waypoint(closest_i);
			}
		}
		
		draw_dynamic_lines(client2merc_x(event.clientX),client2merc_y(event.clientY));
	}
	
}
function on_mousedown(event)
{
	if (event.which!=1)
	{	 //not left button
		return true;
	}
	if(event.preventDefault) //prevent imagedrag on firefox
	{
	  event.preventDefault();
	}
	mouse_is_down=1;
	end_drag_mode(event.clientX,event.clientY);
	initial_mouse_down=[event.clientX,event.clientY];

	return false;
}

function draw_dynamic_lines(cx,cy)
{
	if (waypointstate=='addfirstwaypoint')
	{
		
		jgq.clear();
		jgq.setColor("#00bf00");
		if (clippoint(merc2screen_x(cx),merc2screen_y(cy)))
		{
	    	jgq.fillEllipse(merc2screen_x(cx-5),merc2screen_y(cy-5),10,10);
			jgq.setColor("#ffffff");
			jgq.fillEllipse(merc2screen_x(cx-3),merc2screen_y(cy-3),6,6);
			jgq.setColor("#00bf00");
		}
		
		jgq.paint();
	}
	else if (waypointstate=='addwaypoint')
	{
		jgq.clear();
		l=clipline(merc2screen_x(anchorx),merc2screen_y(anchory),merc2screen_x(cx),merc2screen_y(cy));
		if (l.length>0) 
			jgq.drawLine(l[0],l[1],l[2],l[3]);

		if (clippoint(merc2screen_x(cx),merc2screen_y(cy)))
		{
			jgq.setColor("#00bf00");		
	    	jgq.fillEllipse(merc2screen_x(cx-5),merc2screen_y(cy-5),(10),(10));
			jgq.setColor("#ffffff");
			jgq.fillEllipse(merc2screen_x(cx-3),merc2screen_y(cy-3),(6),(6));
			jgq.setColor("#00bf00");
		}
		
		jgq.paint();
	}
	else if (waypointstate=='moving')
	{
		jgq.clear();
				
		if (movingwaypoint!=0)
		{
			l=clipline(merc2screen_x(wps[movingwaypoint-1][0]),merc2screen_y(wps[movingwaypoint-1][1]),merc2screen_x(cx),merc2screen_y(cy));
			if (l.length>0)
				jgq.drawLine(l[0],l[1],l[2],l[3]);
		}
		if (movingwaypoint!=wps.length-1)
		{
			l=clipline(merc2screen_x(wps[movingwaypoint+1][0]),merc2screen_y(wps[movingwaypoint+1][1]),merc2screen_x(cx),merc2screen_y(cy));
			if (l.length>0)
				jgq.drawLine(l[0],l[1],l[2],l[3]);
		}
		jgq.paint();
		
	}
}

last_mousemove_x=0;
last_mousemove_y=0;
dragmode=0;
dragstart=[];
function on_mousemovemap(event)
{
	last_mousemove_x=event.clientX;
	last_mousemove_y=event.clientY;
	var mercy=client2merc_y(event.clientY);
	var mercx=client2merc_x(event.clientX);

	if (mouse_is_down)
	{
		if (dragmode==1)
		{
			var dx=event.clientX-dragstart[0];
			var dy=event.clientY-dragstart[1];
			//alert('drag:'+dx+' , '+dy);
			pan_map(dx,dy);						
		}
		else
		{
			var dx=Math.abs(event.clientX-initial_mouse_down[0]);
			var dy=Math.abs(event.clientY-initial_mouse_down[1]);
			if (Math.max(dx,dy)>20)
			{
				dragmode=1;
				dragstarttopleftmerc=[map_topleft_merc[0],map_topleft_merc[1]];
				dragstarttilestart=[tilestart[0],tilestart[1]];
				dragstart=[event.clientX,event.clientY];
				
			}
		}
	}
	
	
	var latlon=merc2latlon([client2merc_x(event.clientX),mercy]);
	var lat=latlon[0];
	var lon=latlon[1];
	document.getElementById("footer").innerHTML='clientX:'+event.clientX+' clientY: '+event.clientY+' mercX: '+mercx+' mercY:'+mercy+' '+aviation_format_pos(latlon);
		
	draw_dynamic_lines(client2merc_x(event.clientX),client2merc_y(event.clientY));
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
	
	if (closest_dist<10)
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
function remove_all_waypoints()
{
	hidepopup();
	if (!confirm('Really remove all waypoints?'))
		return;
	var oldcnt=wps.length;
	wps=[];
	
	for(var i=0;i<oldcnt;++i)
		tab_remove_waypoint(oldcnt-i-1);

	draw_jg();
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
function menu_insert_waypoint_mode()
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
		tab_add_waypoint(clo[0],[relx,rely],to_latlon_str([relx,rely]),null);
		waypointstate='moving';
		movingwaypoint=clo[0]+1;						
		draw_jg();
		draw_dynamic_lines(relx,rely);
	}
}
function menu_add_new_waypoints()
{	
	if (wps.length==0)	
	{	
		waypointstate='addfirstwaypoint';
		provide_help('<ul><li>Click in map to select the starting point for your journey.</li></ul>');
	}
	else
	{
		anchorx=wps[wps.length-1][0];
		anchory=wps[wps.length-1][1];
		waypointstate='addwaypoint';
		provide_help('<ul><li>Click in map to select the next waypoint in your journey.</li></ul>');				
		draw_dynamic_lines(anchorx,anchory);
	}

	
}

function center_map()
{
	var latlon=merc2latlon([lastrightclickx,lastrightclicky]);
	var lat=latlon[0];
	var lon=latlon[1];
	function implement_center()
	{
		var form=document.getElementById('helperform');
		form.center.value=''+lat+','+lon;
		form.submit();
	}
	save_data(implement_center);	
}

function end_drag_mode(clientX,clientY)
{
	if (dragmode==1)
	{
		dragmode=0;
		var dx=parseInt(clientX-dragstart[0]);
		var dy=parseInt(clientY-dragstart[1]);
		for(var i=0;i<tiles.length;++i)
		{
			var tile=tiles[i];
			tile.x1+=dx;		
			tile.y1+=dy;		
		}
		dragstarttopleftmerc[0]=map_topleft_merc[0];
		dragstarttilestart[0]=tilestart[0];
		dragstarttopleftmerc[1]=map_topleft_merc[1];
		dragstarttilestart[1]=tilestart[1];
		pan_map(0,0); //last mousemove event may have fired some ways away (and on cell phone - there might be no mousemove)
		jgq.clear();
		draw_jg();
		return 1;
	}
	return 0;
}
function pan_map(dx,dy)
{
	var h=screen_size_y;
	var w=screen_size_x;
	map_topleft_merc[0]=dragstarttopleftmerc[0]-dx;
	map_topleft_merc[1]=dragstarttopleftmerc[1]-dy;
	tilestart[0]=dragstarttilestart[0]-dx;
	tilestart[1]=dragstarttilestart[1]-dy;
	
	for(var i=0;i<tiles.length;++i)
	{
		var tile=tiles[i];		
		var x=tile.x1+dx;
		var y=tile.y1+dy;
		var need_reload=0;
		if (x+tilesize<=-tilesize/4)
		{ //tile has passed too far to the left
			tile.mercx+=xsegcnt*tilesize;
			tile.x1+=xsegcnt*tilesize;
			x+=xsegcnt*tilesize;
			need_reload=1;
		}
		if (x>=w+tilesize/4)
		{ //tile has passed too far to the right
			tile.mercx-=xsegcnt*tilesize;
			tile.x1-=xsegcnt*tilesize;
			x-=xsegcnt*tilesize;
			need_reload=1;
		}
		
		if (y+tilesize<=-tilesize/4)
		{ //tile has passed too far up
			tile.mercy+=ysegcnt*tilesize;
			tile.y1+=ysegcnt*tilesize;
			y+=ysegcnt*tilesize;
			need_reload=1;
		}
		if (y>=h+tilesize/4)
		{ //tile has passed too far down
			tile.mercy-=ysegcnt*tilesize;
			tile.y1-=ysegcnt*tilesize;
			y-=ysegcnt*tilesize;
			need_reload=1;
		}
		
		if (need_reload)
		{
			//tile.img.src='/boilerplate.jpg';			
			tile.img.src='/tiles/'+parseInt(map_zoomlevel)+'/'+parseInt(tile.mercy)+'/'+parseInt(tile.mercx)+'.png';
				/*'/maptile/get?x1='+
				(tile.mercx)+'&y1='+
				(tile.mercy)+'&zoomlevel='+map_zoomlevel+'&width='+
				(tilesize)+'&height='+tilesize;*/
	        	
		}
		tile.img.style.left=''+x+'px';
		tile.img.style.top=''+y+'px';
	}

	var overlay2=document.getElementById('overlay2');
	overlay2.style.left=''+(overlay_left+dx)+'px';
	overlay2.style.top=''+(overlay_top+dy)+'px';
}
