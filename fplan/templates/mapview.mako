
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
		pane.innerHTML=\
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
		pane.innerHTML=\
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
function to_lat(y)
{
	return (180.0/PI)*Math.atan(sinh(y));
}
function to_y(lat)
{
	lat/=(180.0/PI);
	return Math.log(Math.tan(lat)+1.0/Math.cos(lat));
} 

function to_latlon(p)
{
	px=p[0];
	py=p[1];
	if (map_ysize==0)
	{
		return [0,0];
	}
	var min_merc_y=to_y(${c.lat-0.5*c.size});
	var max_merc_y=to_y(${c.lat+0.5*c.size});
	
	var x=(px)/(map_xsize+0.0);
	var y=(map_ysize-py)/(map_ysize+0.0);
	
	var wfactor=map_xsize/map_ysize;
	var cury=y*(max_merc_y-min_merc_y)+min_merc_y;
	var lat=to_lat(cury);
					
	var lon=${c.lon}-${0.5*c.lonwidth}*wfactor+${c.lonwidth}*x*wfactor;	
	lon = lon % 360.0;
	if (lon<0) lon=lon+360.0;
	
	return [lat,lon];	
}

function to_merc(latlon)
{
	var lat=latlon[0];
	var lon=latlon[1];
	if ((lon-${c.lon})>180.0)
	{
		lon-=360.0;
	}
	if ((lon-${c.lon})<-180.0)
	{
		lon+=360.0;
	}
	var wfactor=map_xsize/map_ysize;
	var min_merc_y=to_y(${c.lat-0.5*c.size});
	var max_merc_y=to_y(${c.lat+0.5*c.size});
	var cury=to_y(lat);
	var y=(cury-min_merc_y)/(max_merc_y-min_merc_y);
	var x=(lon+${0.5*c.lonwidth}*wfactor-${c.lon})/(${c.lonwidth}*wfactor);
	
	var px=x*(map_xsize+0.0);
	var py=map_ysize-y*(map_ysize+0.0);
	return [px,py];	
}
function draw_great_circle(curw,endw)
{
	var cur=to_latlon(curw);
	var end=to_latlon(endw);
	var dist=dist_between(cur,end);
	var numseg=dist/150000.0;	
	if (numseg<2)
	{
 		jg.drawLine(
    		abs_x(curw[0]),
			abs_y(curw[1]),
			abs_x(endw[0]),
			abs_y(endw[1]));
	}
	else
	{
		ps=great_circle_points(cur,end,parseInt(numseg));		
		for(var i=1;i<ps.length;++i)
		{
				//alert('GC: '+(ps[i-1]));
 			jg.drawLine(
	    		abs_x(to_merc(ps[i-1])[0]),
				abs_y(to_merc(ps[i-1])[1]),
				abs_x(to_merc(ps[i])[0]),
				abs_y(to_merc(ps[i])[1])
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
 
function vector_difference(v1,v2)
{
	return [v1[0]-v2[0],v1[1]-v2[1],v1[2]-v2[2]];
}
function vector_sum(v1,v2)
{
	return [v1[0]+v2[0],v1[1]+v2[1],v1[2]+v2[2]];
}
function vector_length(v1)
{
	return Math.sqrt(v1[0]*v1[0]+v1[1]*v1[1]+v1[2]*v1[2]);
}
function vector_crossprod(v1,v2)
{
 	var r=[0,0,0];
    r[0]=v1[1]*v2[2] - v1[2]*v2[1];
    r[1]=v1[2]*v2[0] - v1[0]*v2[2];
    r[2]=v1[0]*v2[1] - v1[1]*v2[0];
    return r;
}

function scalar_prod(v1,v2)
{
	var sum=0;
	for(var i=0;i<3;++i)
		sum+=v1[i]*v2[i];
	return sum;
}
function scalar_vector_prod(sc,v2)
{
	return [sc*v2[0],sc*v2[1],sc*v2[2]];
}
function format_distance(meters)
{
	var naut=meters/1852.0;
	return ''+naut.toFixed(0)+" NM";	
}
function to_vector(latlon)
{	
	var lat=latlon[0]/(180.0/Math.PI);
	var lon=latlon[1]/(180.0/Math.PI);
	var z=Math.sin(lat);
	var t=Math.cos(lat);
	var x=t*Math.cos(lon);
	var y=t*Math.sin(lon);	
	return [x,y,z];
}
function vector_normalize(v1)
{
	var len=vector_length(v1);
	return scalar_vector_prod(1.0/len,v1);
}
function vector_angle_between(v1,v2)
{
	var sc=scalar_prod(v1,v2);
	if (sc<0.9999)
	{
		if (sc<-1.0) sc=-1.0;
		return Math.acos(sc);
	}
	return vector_length(vector_difference(v1,v2));	
}
function heading_between(latlon1,latlon2)
{
	var v1=to_vector(latlon1);
	var v2=to_vector(latlon2);
	var k=0.5e-5;
	var direct=scalar_vector_prod(k,vector_normalize(vector_difference(v2,v1)));	
	var wp=vector_normalize(vector_sum(v1,direct));	
	var wpdir=vector_normalize(vector_difference(wp,v1));
	

	var lat=latlon1[0]/(180.0/Math.PI);
	var lon=latlon1[1]/(180.0/Math.PI);
	var z=Math.cos(lat);
	var t=Math.sin(lat);
	var x=-t*Math.cos(lon);
	var y=-t*Math.sin(lon);	
	var TN=[x,y,z]; //True north	
	
	var rad=vector_angle_between(TN,wpdir);
	var posposdeg=scalar_prod(v1,vector_crossprod(wpdir,TN));
	if (posposdeg<0)
	{
		rad=2*Math.PI-rad;
	}	
	var hdg=rad*(180.0/Math.PI);
	if (hdg<0)
		hdg+=360.0;
	return hdg;
}
function format_heading(hdg)
{
	return hdg.toFixed(0)+'\u00B0';		
}
function to_polar_coord(cur)
{
	var lat=Math.asin(cur[2])*(180.0/Math.PI);
	var lon=Math.atan2(cur[1],cur[0])*(180.0/Math.PI);

	if (lon<0.0)
		lon+=360.0;
	//alert('to polar('+cur+') = '+lat+', '+lon);
	return [lat,lon];
}
function great_circle_points(c1,c2,num)
{
	var v1=to_vector(c1);
	var v2=to_vector(c2);	
	out=[];
	var cur=v1;	
	for(var i=0;i<num;++i)
	{
		
		out.push(to_polar_coord(cur));
			
		var delta=scalar_vector_prod(1.0/(num-i),vector_difference(v2,cur));
		cur=vector_normalize(vector_sum(cur,delta));
		
		
	}
	out.push(to_polar_coord(v2));
	return out;
}
function dist_between(latlon1,latlon2)
{	
	var v1=to_vector(latlon1);
	var v2=to_vector(latlon2);
	var sc=scalar_prod(v1,v2);

	var ang=0;
	if (sc>=0.9999 || sc<-0.9999)
	{
		ang=vector_length(vector_difference(v1,v2));
	}
	else
	{
		ang=Math.acos(sc);
	}
	return  6367500*ang; //meters
	
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
						draw_great_circle(
							wps[i-1],wps[i]);		    			
			    		/*jg.drawLine(
				    		abs_x(wps[i-1][0]),
			    			abs_y(wps[i-1][1]),
			    			abs_x(wps[i][0]),
			    			abs_y(wps[i][1]));*/
			    	}
			    }
			    if (pass==1)
			    {	
			    	if (selected_waypoint_idx==i)
			    	{
			    		jg.setColor("#0000bf");
				    	jg.fillEllipse(abs_x(wps[i][0])-5,abs_y(wps[i][1])-5,10,10);
			    		jg.setColor("#ffffff");
			    		jg.fillEllipse(abs_x(wps[i][0])-3,abs_y(wps[i][1])-3,6,6);
			    	}
			    	else
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
			if (!check_and_clear_selections())
			{
				anchorx=relx;
				anchory=rely;		
				tab_add_waypoint(wps.length,[relx,rely]);
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
	var latlon=to_latlon([lastrightclickx,lastrightclicky]);
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
	'<div class="popopt" id="menu-del" onclick="remove_waypoint()">Remove Waypoint</div>'+
	'<div class="popopt" id="menu-move" onclick="move_waypoint()">Move Waypoint</div>'+
	'<div class="popopt" onclick="close_menu()">Close menu</div>'+
	'<div class="popopt" onclick="center_map()">Center Map</div>'+ 
	'</div>'+
	'<form id="helperform" action="${h.url_for(controller="mapview",action="zoom")}">'+
	'<input type="hidden" name="zoom" value="">'+
	'<input type="hidden" name="center" value="">'+
	'</form>'
	;
	
	var sidebar=document.getElementById('sidebar-a');
	sidebar.innerHTML='<div class="first"><form id="fplanform" action="${h.url_for(controller="mapview",action="save")}">'+
	'<table id="tab_fplan" width="100%">'+
	'</table></form></div>'+
	'<div style="display:none" class="second" id="detail-pane">'+
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
	
	
	
}
addLoadEvent(loadmap);

</script>


	