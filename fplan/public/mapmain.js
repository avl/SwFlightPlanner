
use_great_circles=0;

/* Used by show-area feature. Set to the area, then
save is called. Save saves this variable */
showarea='';

function setdetailpane(bgcol,display,cont)
{
	var h=document.getElementById('detail-pane');
	h.style.background=bgcol;
	h.style.display=display;
	h.innerHTML=cont;
}
function hidedetailpane()
{
	setdetailpane('#ffffff','none','');	
}
function provide_help(msg)
{
	setdetailpane("#ffe0e0",'block','<b>Hints:</b><br/>'+msg);
}

opinprogress=0;

function navigate_to(where)
{	
	function finish_nav()
	{				
		window.location.href=where;
	}
	save_data(finish_nav);
}
function save_data_if_dirty(cont)
{
	if (getisdirty())
		save_data(cont);
	else
		cont();
}
function save_data(cont)
{
	if (opinprogress==1)
	{
		return;
	}
	setnotdirty();
	var oldtripname=document.getElementById('oldtripname').value;
	var progm=document.getElementById("progmessage");
	function save_data_cb(req)
	{	
		opinprogress=0;
		if (req.responseText!='notok')
		{
			var param=evalJSONRequest(req);
			var newtripname=param[0];
			document.getElementById('oldtripname').value=newtripname;
			document.getElementById('entertripname').value=newtripname;
			progm.style.display='none';
			if (cont!=null)
			{
				cont();
				//setTimeout(cont,100);
			}
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
		var altfield=rowelem.cells[2].childNodes[1];
		var idfield=rowelem.cells[2].childNodes[2];
		params[namefield.name]=namefield.value;
		params[posfield.name]=posfield.value;
		params[altfield.name]=altfield.value;
		params[idfield.name]=idfield.value;
	}			
	params['tripname']=document.getElementById('entertripname').value;
	params['oldtripname']=document.getElementById('oldtripname').value;
	params['showarea']=showarea;
	params['mapvariant']=mapvariant;
	params['pos']=''+parseInt(map_topleft_merc[0]+screen_size_x/2)+','+parseInt(map_topleft_merc[1]+screen_size_y/2);
	params['zoomlevel']=map_zoomlevel;
	var def=doSimpleXMLHttpRequest(saveurl,
		params);
	def.addCallback(save_data_cb);
}

function on_change_mapvariant()
{
	var elem=document.getElementById('mapvariant');
	mapvariant=elem.value;
	if (mapvariant=='elev' && map_zoomlevel>8)
	{
    	zoom_out([map_topleft_merc[0]+screen_size_x/2,map_topleft_merc[1]+screen_size_y/2]);
	}
	else
	{
    	reload_map();
    }
}
function reload_map()
{
	for(var i=0;i<tiles.length;++i)
	{
		var tile=tiles[i];
		tile.img.src=calctileurl(parseInt(map_zoomlevel),parseInt(tile.mercx),parseInt(tile.mercy));
	}
}

function tab_modify_pos(idx,pos)
{
	var glist=document.getElementById('tab_fplan');
	var rowpos=glist.rows[idx].cells[2].childNodes[0];
	var latlon=merc2latlon(pos);
	rowpos.value=''+latlon[0]+','+latlon[1];
		
}
function tab_remove_waypoint(idx)
{
	var glist=document.getElementById('tab_fplan');
	glist.deleteRow(idx);
	tab_renumber(idx);
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
	if (idxs.length==0)
	{
		hidedetailpane();
	}
	if (idxs.length==1)
	{
		var idx=idxs[0];		
		var name=glist.rows[idx].cells[1].childNodes[0].value;
		setdetailpane(
				"#a0a0ff",
				'block',
				'<h2>'+name+'</h2>'+
				'<p><b>Position:</b>'+aviation_format_pos(merc2latlon(wps[idx]),2)+'</p>');
	}
	if (idxs.length==2)
	{
		var idx1=idxs[0];
		var idx2=idxs[1];
		var name1=glist.rows[idx1].cells[1].childNodes[0].value;
		var name2=glist.rows[idx2].cells[1].childNodes[0].value;
		setdetailpane('#ffa0a0',
				'block',
			'<h2>'+name1+' - '+name2+'</h2>'+
			'<p><b>Distance:</b> '+format_distance(dist_between(merc2latlon(wps[idx1]),merc2latlon(wps[idx2])),1)+'</p>'+
			'<p><b>True Heading:</b> '+format_heading(heading_between(merc2latlon(wps[idx1]),merc2latlon(wps[idx2])))+'</p>');
		
		
	}
	
}

function to_latlon_str(pos)
{
	latlon=merc2latlon(pos);
	return ''+latlon[0]+','+latlon[1];
}
function reorder_wp(idx,delta)
{
    if (dragmode!=0)
        return;
    var odx=idx+delta;
    if (odx<0)
    {
        for(var i=0;i<wps.length-1;++i)
        {
            reorder_wp_impl(i,1);
        }
    	select_waypoint(wps.length-1);
        return;
    }
    if (odx>=wps.length)
    {
        for(var i=wps.length-1;i>0;--i)
        {
            reorder_wp_impl(i,-1);
        }
    	select_waypoint(0); 
        return;
    }
    reorder_wp_impl(idx,delta);
	select_waypoint(odx); 
}
function reorder_wp_impl(idx,delta)
{
    var odx=idx+delta;
    if (odx<0) odx=wps.length-1;
    if (odx>=wps.length) odx=0;
    if (idx<0 || idx>=wps.length || odx<0 || odx>=wps.length)
        return false;
    var w1=wps[idx];        
    var w2=wps[odx];        
    wps[odx]=w1;
    wps[idx]=w2;
    setdirty();
    var glist=document.getElementById('tab_fplan');
    var rowelem1=glist.rows[idx];		
	var name1e=rowelem1.cells[1].childNodes[0];
	var pos1e=rowelem1.cells[2].childNodes[0];
	var alt1e=rowelem1.cells[2].childNodes[1];
	var id1e=rowelem1.cells[2].childNodes[2];
    var rowelem2=glist.rows[odx];		
	var name2e=rowelem2.cells[1].childNodes[0];
	var pos2e=rowelem2.cells[2].childNodes[0];
	var alt2e=rowelem2.cells[2].childNodes[1];
	var id2e=rowelem2.cells[2].childNodes[2];

    var pos1=pos1e.value;
    var pos2=pos2e.value;
    var name1=name1e.value;
    var name2=name2e.value;
    var alt1=alt1e.value;
    var alt2=alt2e.value;
    var id1=id1e.value;
    var id2=id2e.value;
    pos1e.value=pos2;
    pos2e.value=pos1;
    name1e.value=name2;
    name2e.value=name1; 
    alt1e.value=alt2;
    alt2e.value=alt1; 
    id1e.value=id2;
    id2e.value=id1; 
}
function tab_add_waypoint(idx,pos,id,name,altitude)
{	
   	var latlon=merc2latlon(pos);
	var curid=id;
	if (curid==null)
	{
	    curid=next_waypoint_id;
	    next_waypoint_id+=1;
	}
	if (name==null)
		name=default_wpname(latlon);
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
   	
   	/*function onclick_waypoint()
   	{
   		select_waypoint(idx);
   	}
   	elem.onclick=onclick_waypoint;
   	*/
    elem.innerHTML=''+
    '<td style="cursor:pointer">#'+(idx+1)+':</td>'+
    '<td><input size="15" style="background:#c0ffc0" type="text" onchange="setdirty();" onkeydown="setdirty();return not_enter(event)" onkeypress="setdirty();return not_enter(event)" name="row_'+idx+'_name" value="'+name+'"/>'+
    '<img src="/uparrow.png" /><img src="/downarrow.png" /> </td>'+
    '<td>'+
    '<input type="hidden" name="row_'+idx+'_pos" value="'+latlon[0]+','+latlon[1]+'"/>'+
    '<input type="hidden" name="row_'+idx+'_altitude" value="'+altitude+'"/>'+
    '<input type="hidden" name="row_'+idx+'_id" value="'+curid+'"/>'+
    '</td>'+
    '';
	
	tab_renumber(idx);	
	
}
function tab_renumber(idx_above)
{
	var glist=document.getElementById('tab_fplan');
	for(var i=idx_above;i<glist.rows.length;i++)
	{
		tab_renumber_single(i);
	}
}
function tab_renumber_single(i)
{
	var glist=document.getElementById('tab_fplan');
	var rowelem=glist.rows[i];		
	rowelem.cells[0].innerHTML='#'+(i+1)+':';
	rowelem.cells[0].oncontextmenu=function(ev) { rightclick_waypoint_tab(i,ev); return false; };
	rowelem.cells[0].onclick=function(ev) { select_waypoint(i); clear_mapinfo(); hidedetailpane(); return false; };
	
	rowelem.cells[1].childNodes[0].onclick=function(ev) { select_waypoint(i); return false; };
	rowelem.cells[1].childNodes[0].name='row_'+i+'_name';
	rowelem.cells[1].childNodes[1].onclick=function(ev) { reorder_wp(i,-1);return false; }; 
	rowelem.cells[1].childNodes[2].onclick=function(ev) { reorder_wp(i,+1);return false; }; 
	rowelem.cells[2].childNodes[0].name='row_'+i+'_pos';
	rowelem.cells[2].childNodes[1].name='row_'+i+'_altitude';
	rowelem.cells[2].childNodes[2].name='row_'+i+'_id';
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

	if (how=='auto')
	{
		form.zoom.value='auto';
		form.submit();
		return;
	}

	var zoomparam=map_zoomlevel;
	var mercx=pos[0];
	var mercy=pos[1];
	if (how==1 && map_zoomlevel<13)
	{
		mercx*=2.0;
		mercy*=2.0;
		zoomparam+=1;
	}
	else if (how==-1 && map_zoomlevel>0)
	{
		mercx/=2.0;
		mercy/=2.0;
		zoomparam-=1;
	}
	
	form.zoom.value=''+(zoomparam);
	form.center.value=''+parseInt(mercx)+','+parseInt(mercy);
	//alert('actually zooming');
	form.submit();
}
function zoom_out(pos)
{
	
	function zoom_out_impl()
	{
		dozoom(-1,pos);
	}
 	save_data_if_dirty(zoom_out_impl);
}
function zoom_in(pos)
{
	function zoom_in_impl()
	{
		dozoom(1,pos);
	}
 	save_data_if_dirty(zoom_in_impl);
}
function handle_mouse_wheel(delta,event) 
{
	var screen_x=event.clientX-document.getElementById('mapcontainer').offsetLeft;
	var screen_y=event.clientY-document.getElementById('mapcontainer').offsetTop;
	if (screen_x<0 || screen_y<0 || screen_x>=screen_size_x || screen_y>=screen_size_y)
	    return false;	   
	var dx=screen_x-(screen_size_x/2);
	var dy=screen_y-(screen_size_y/2);
	var centerx=map_topleft_merc[0]+screen_size_x/2;
	var centery=map_topleft_merc[1]+screen_size_y/2;	
	if (delta>0)
	{
	    var x=centerx+dx/2;
	    var y=centery+dy/2;
		zoom_in([parseInt(x),parseInt(y)]);
	}
	if (delta<0)
	{
	    //newcenterx=2*(centerx+dx/2) => centerx=newcenterx/2-dx/2
	    var x=centerx-dx;
	    var y=centery-dy;
		zoom_out([parseInt(x),parseInt(y)]); 		
	}
	return true;
}


map_ysize=0;
map_xsize=0;
PI=3.1415926535897931;

function zeropad(s2,cnt)
{
    var i=0;
    for(;i<s2.length;++i)
    {
        if (s2[i]=='.') break;
    }
    var need=cnt-i;
    var s=''+s2;
    for(i=0;i<need;++i)
        s='0'+s;
    return s;
}
function aviation_format_pos(latlon,prec)
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
	
	return ''+zeropad(latdeg.toFixed(0),2)+zeropad(latmin.toFixed(prec),2)+lathemi+zeropad(londeg.toFixed(0),3)+zeropad(lonmin.toFixed(prec),2)+lonhemi;	
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
	jgq.clear();
	var relx=client2merc_x(event.clientX);
	var rely=client2merc_y(event.clientY);

	return as_if_rightclick(relx,rely,event);	
}

function rightclick_waypoint_tab(idx,event)
{
	var relxy=wps[idx];
	as_if_rightclick(relxy[0],relxy[1],event);
}

function as_if_rightclick(relx,rely,event)
{
	if (waypointstate!='none')
	{
		waypointstate='none';
		if (wps.length==1)
		{
			provide_help('<ul><li>You have added a starting point, but no further waypoints. You need at least two points to define a journey!</li><li>Click the "Add on Map" button above to add a new waypoint</li></ul>');
		}
		else
		{
			provide_help('<ul><li>Use the "Add on Map" button up to the right to add more waypoints</li><li>To move or delete a waypoint, right-click it and choose add or delete.</li><li>To insert a new waypoint in the middle of the trip, right-click a track-line, and choose "Insert Waypoint".</li></ul>');
		}
		jgq.clear();
		draw_jg();
		return false;
	}	
	
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
function screen2merc_x(x)
{ //screen = map
	return x+map_topleft_merc[0];
}
function screen2merc_y(y)
{ //screen = map
	return y+map_topleft_merc[1];
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
function draw_hatched_line(jg,l,c1,c2)
{
    var geomlen=Math.sqrt((l[0]-l[2])*(l[0]-l[2])+(l[1]-l[3])*(l[1]-l[3]));
    if (geomlen==0) return;
    var dx=l[2]-l[0];
    var dy=l[3]-l[1];
    var alt=0;
    for(var p=30;p<geomlen-5;p+=30)
    {
    
        var cx=parseInt(l[0]+dx*p/geomlen);
        var cy=parseInt(l[1]+dy*p/geomlen);
        alt=!alt;
        if (alt)
        	jg.setColor(c1);
        else 
        	jg.setColor(c2); 
	    jg.fillRect(
	        cx-3,cy-3,6,6);
    }

}
function draw_jg()
{
	jg.clear();

    if (fastmap)
    {
        for(var i=0;i<wps.length;i++)
        {
        	if (waypointstate!='moving' || (
        		i-1!=movingwaypoint && i!=movingwaypoint))
        	{
        		if (i!=0)    		
        		{    		
        			var c1='';
        			var c2='';	
        			if (selected_route_idx==i-1)
        			{
        				c1="#700000";
        				c2="#ff4040";
        			}
        			else
        			{
        				c1="#007000";
        				c2="#40ff40";
        			}
			
			        var l=clipline(
				        merc2screen_x(wps[i-1][0]),
				        merc2screen_y(wps[i-1][1]),
				        merc2screen_x(wps[i][0]),
				        merc2screen_y(wps[i][1])
            			);
            		if (l.length)	    			
            		{
            		    draw_hatched_line(jg,l,c1,c2);
	                }
            	}
            	var screen_x=merc2screen_x(wps[i][0]);
            	var screen_y=merc2screen_y(wps[i][1]);
        		if (clippoint(screen_x,screen_y))
        		{
                	if (selected_waypoint_idx==i)
                	{
                		jg.setColor("#20207f");
			            jg.setFont("arial","14px",Font.BOLD);
			            jg.drawString(''+i,screen_x+7,screen_y-5);			    		
                		jg.setColor("#0000bf");
	                	jg.fillRect(screen_x-5,screen_y-5,10,10);
                		jg.setColor("#ffffff");
                		jg.fillRect(screen_x-3,screen_y-3,6,6);
                	}
                	else
                	{
            			jg.setColor("#207f20");
			            jg.setFont("arial","14px",Font.BOLD);
			            jg.drawString(''+i,screen_x+7,screen_y-5);			    		
                		jg.setColor("#00bf00");
	                	jg.fillRect(screen_x-5,screen_y-5,10,10);
                		jg.setColor("#ffffff");
                		jg.fillRect(screen_x-3,screen_y-3,6,6);
                	}			    	
                }
            }
	    }
    }
    else
    {
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
		        				jg.setColor("#ff0000"); // red
		        			else
		        				jg.setColor("#008000");
		        				
						
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
	}
	
	jg.setColor("#404040");
    jg.setFont("arial","12px",Font.BOLD);
    var nomw=70;
    var x2=screen_size_x-20;
    var x1=x2-nomw;
    var y=screen_size_y-18;
	var mercx1=screen2merc_x(x1);
	var mercx2=screen2merc_x(x2);
	var mercy=screen2merc_y(y);
	var l1=merc2latlon([mercx1,mercy]);
	var l2=merc2latlon([mercx2,mercy])
	var dist=dist_between(l1,l2)/1852.0;
	var odist=dist;
	var factor=1.0;
	while(dist>=10.0)
	{
	    dist/=10.0;
	    factor*=10.0;
	}
	if (dist<=0.5) dist=0.5;	
	else if (dist<=1) dist=1;	
	else if (dist<=1.5) dist=1.5;	
	else if (dist<=2) dist=2;
	else if (dist<=2.5) dist=2.5;
	else if (dist<=5) dist=5;
	else if (dist<=7.5) dist=7.5;
	else dist=10.0;
	dist*=factor;
	var disti=dist.toFixed(1);
	var ratio=parseFloat(disti)/odist;
	var w=nomw*ratio;

	jg.fillRect(x2-w,y,w,1);
	jg.fillRect(x2-w,y-3,1,7);
	jg.fillRect(x2,y-3,1,7);
	var s=''+disti;
	if (s[s.length-1]=='0')
	    s=s.substring(0,s.length-2);
    jg.drawString(s+' NM ',x2-w*0.5-20,screen_size_y-15);			    		
	
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
function default_wpname(latlon)
{
    return aviation_format_pos(latlon,0);
}
function add_waypoint_here(event)
{
	var m=merc2latlon([lastrightclickx,lastrightclicky]);
	add_waypoint(default_wpname(m),m);
	hidepopup();
	return false;
}
function add_waypoint(name,pos)
{
	var merc=latlon2merc(pos);
	relx=merc[0];
	rely=merc[1];
	tab_add_waypoint(wps.length,[relx,rely],null,name,'');
	wps.push([relx,rely]);
	setdirty();
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
function clear_mapinfo()
{
    var div=document.getElementById("mapinfo");
    div.style.display='none';
 	div.innerHTML='';
}
function show_mapinfo(mercx,mercy)
{
    function on_get_mapinfo(req)
    {
        var div=document.getElementById("mapinfo");
    	div.style.display='block';
        div.innerHTML=req.responseText;
    }
	var latlon=merc2latlon([mercx,mercy]);
    var params={};
	params['lat']=latlon[0];
	params['lon']=latlon[1];
	
	var def=doSimpleXMLHttpRequest(mapinfourl,params);
	def.addCallback(on_get_mapinfo);

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
		clear_mapinfo();
		tab_add_waypoint(wps.length,[relx,rely],null,null,'');
		wps.push([client2merc_x(event.clientX),client2merc_y(event.clientY)]);
		setdirty();
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
		clear_mapinfo();
		wps[movingwaypoint]=[relx,rely];
		setdirty();		
		tab_modify_pos(movingwaypoint,[relx,rely]);
		waypointstate='none';
		jgq.clear();
		draw_jg();
		return;		
	}
	else
	{
	    show_mapinfo(relx,rely);		
	    
		if (wps.length==0)
		{
			check_and_clear_selections();			
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
					check_and_clear_selections();				
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
		{
		    draw_hatched_line(jgq,l,'#008000','#ffffff');
		}

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
    		    draw_hatched_line(jgq,l,'#008000','#ffffff');
		}
		if (movingwaypoint!=wps.length-1)
		{
			l=clipline(merc2screen_x(wps[movingwaypoint+1][0]),merc2screen_y(wps[movingwaypoint+1][1]),merc2screen_x(cx),merc2screen_y(cy));
			if (l.length>0)
    		    draw_hatched_line(jgq,l,'#008000','#ffffff');
		}
		jgq.paint();
		
	}
}

last_mousemove_x=0;
last_mousemove_y=0;
dragmode=0;
dragstart=[];
accum_pan_dx=0;
accum_pan_dy=0;
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
		    var evcx=parseInt(event.clientX);
		    var evcy=parseInt(event.clientY);
			var dx=evcx-dragstart[0];
			var dy=evcy-dragstart[1];
			//alert('drag:'+dx+' , '+dy);
			pan_map(dx,dy);						
			dragstart[0]=evcx;
			dragstart[1]=evcy;
		}
		else
		{
			var dx=Math.abs(event.clientX-initial_mouse_down[0]);
			var dy=Math.abs(event.clientY-initial_mouse_down[1]);
			if (Math.max(dx,dy)>20)
			{
				dragmode=1;
				//dragstarttopleftmerc=[map_topleft_merc[0],map_topleft_merc[1]];
				//dragstarttilestart=[tilestart[0],tilestart[1]];
				accum_pan_dx=0;
				accum_pan_dy=0;
				dragstart=[event.clientX,event.clientY];
				
			}
		}
	}
	
	
	var latlon=merc2latlon([client2merc_x(event.clientX),mercy]);
	var lat=latlon[0];
	var lon=latlon[1];

	var ol=document.getElementById('mapcontainer').offsetLeft;

	document.getElementById("footer").innerHTML=aviation_format_pos(latlon,2)+' ('+latlon[0].toFixed(6)+','+latlon[1].toFixed(6)+') (dbg: xm: '+mercx+' ym:'+mercy+' zoom: '+map_zoomlevel+')';
		
	draw_dynamic_lines(client2merc_x(event.clientX),client2merc_y(event.clientY));
}
function upload_areadata()
{	
	
	function upload_areadata_impl()
	{
		dozoom('auto',0);
	}	
	showarea=document.getElementById('visualize_data_text').value;
 	save_data(upload_areadata_impl);
	return false;
}
function clear_uploaded_data()
{
	function clear_uploaded_data_impl()
	{
		window.location.href=selfurl; /*Navigate to same page, will imply a reload of the map tiles (which are non-cacheable)*/
	}
	showarea='.';
 	save_data(clear_uploaded_data_impl);
	return false;
}
function upload_trackdata()
{	
	function upload_trackdata_impl()
	{
		var tform=document.getElementById('uploadtrackform');
		tform.submit();		
	}
	
 	save_data(upload_trackdata_impl);
	return false;
}
function visualize_area_data()
{
	setdetailpane(
			"#ffffc0",
			'block',
			'<form action="#">'+
			'Paste an area definition from NOTAM or other source into '+
			'the area below:<br/>'+
			'<textarea id="visualize_data_text" rows="5" cols="25" name="text">'+
			'</textarea>'+
			'<button onclick="return upload_areadata()">Upload</button>'+
			'<p style="font-size:70%"><b>Example:</b><br/>554937N 0133636E - 553500N 0133850E - 552620N 0134720E - 550715N 0134720E - 550540N 0125958E - 551458N 0125956E - 554358N 0130656E - 554857N 0130636E - 554937N 0133636E</p>'+
			'</form>'
			);
			
}

function uploadtrack_show_period_sel()
{
	var d=document.getElementById('trackdataperiod');
	d.style.display='block';
}

function visualize_track_data()
{
	var d=new Date();
	var year=d.getFullYear();
	var mon=d.getMonth()+1;
	var day=d.getDate();
	setdetailpane(
			"#ffffc0",
			'block',
			'<form enctype="multipart/form-data" id="uploadtrackform" action="'+uploadtrackurl+'" method="POST">'+			
			'Upload a GARMIN .gpx-file:'+
			'<input type="file" name="gpstrack"/>'+
			'<button onclick="return upload_trackdata()">Upload</button><br/>'+
			'<a href="#" onclick="uploadtrack_show_period_sel()">Select time period</a><br/>'+
			'<div id="trackdataperiod" style="display:none">Start: <input type="text" name="start" value="1990-01-01 00:00:00"/><br/>'+
			'End: <input type="text" name="end" value="'+year+'-'+mon+'-'+day+' 23:59:00"/></div>'+
			'</form>'
			);
			
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
	setdirty();
	
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
		setdirty();		
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
		var i=0;
		for(;i<wps.length;i++)
		{						
			tmpwps.push(wps[i]);
			if (i==clo[0])
				tmpwps.push([clo[1],clo[2]]);
		}
		wps=tmpwps;
		setdirty();		
		tab_add_waypoint(clo[0]+1,[relx,rely],null,null,'');
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
		provide_help('<ul><li>Click in map to place the next waypoint in your journey.</li><li>Right click anywhere in map if you are done adding waypoints</li></ul>');				
		draw_dynamic_lines(anchorx,anchory);
	}

	
}

function center_map()
{
	var merc_x=lastrightclickx;
	var merc_y=lastrightclicky;
	function implement_center()
	{
		var form=document.getElementById('helperform');
		form.center.value=''+parseInt(merc_x)+','+parseInt(merc_y);
		form.zoom.value=map_zoomlevel; 
		form.submit();
	}
	save_data(implement_center);	
}

function end_drag_mode(clientX,clientY)
{
	if (dragmode==1)
	{
		dragmode=0;
		/*var dx=parseInt(clientX-dragstart[0]);
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
		dragstarttilestart[1]=tilestart[1];*/
		var dx=parseInt(clientX-dragstart[0]);
		var dy=parseInt(clientY-dragstart[1]);
		pan_map(dx,dy); //last mousemove event may have fired some ways away (and on cell phone - there might be no mousemove)
        accum_pan_dx=0;
        accum_pan_dy=0;
    	var overlay2=document.getElementById('overlay2');
	    overlay2.style.left=''+(overlay_left)+'px';
	    overlay2.style.top=''+(overlay_top)+'px';
		jgq.clear();
		draw_jg();
		return 1;
	}
	return 0;
}
function pan_map(dx,dy)
{
    dx=parseInt(dx);
    dy=parseInt(dy);
	var h=screen_size_y;
	var w=screen_size_x;
	//tilestart[0]-=dx;//dragstarttilestart[0]-dx;
	//tilestart[1]-=dy;//dragstarttilestart[1]-dy;
	
	clipped=clip_mappos(map_topleft_merc[0]-dx,map_topleft_merc[1]-dy);
	var delta=[clipped[0]-map_topleft_merc[0],clipped[1]-map_topleft_merc[1]];
	dx=-delta[0];
	dy=-delta[1];
	map_topleft_merc[0]-=dx; //=dragstarttopleftmerc[0]-dx;
	map_topleft_merc[1]-=dy; //=dragstarttopleftmerc[1]-dy;
	
	for(var i=0;i<tiles.length;++i)
	{
		var tile=tiles[i];	
		tile.x1+=dx;
		tile.y1+=dy;	
		var x=tile.x1;+dx;
		var y=tile.y1;+dy;
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
			tile.img.src='/loading.png';
			tile.img.src=calctileurl(parseInt(map_zoomlevel),parseInt(tile.mercx),parseInt(tile.mercy));
	        	
		}
		tile.img.style.left=''+x+'px';
		tile.img.style.top=''+y+'px';
	}
    accum_pan_dx+=dx;
    accum_pan_dy+=dy;
	var overlay2=document.getElementById('overlay2');
	overlay2.style.left=''+(overlay_left+accum_pan_dx)+'px';
	overlay2.style.top=''+(overlay_top+accum_pan_dy)+'px';
}




function add_new_trip()
{
    var me=document.getElementById('addtripfunctions');
    if (me.style.display=='none')
        me.style.display='block';
    else
        me.style.display='none';
}
function more_trip_functions()
{
    var me=document.getElementById('moretripfunctions');
    if (me.style.display=='none')
        me.style.display='block';
    else
        me.style.display='none';
}
function open_trip()
{
    var me=document.getElementById('opentripfunctions');
    if (me.style.display=='none')
        me.style.display='block';
    else
        me.style.display='none';
}
function on_add_trip()
{
	function finish_add_trip()
	{				
		document.getElementById('tripform').submit();
	}
	save_data(finish_add_trip);
}
function on_delete_trip()
{
	function finish_add_trip()
	{				
		document.getElementById('deletetripname').value=document.getElementById('oldtripname').value;
		document.getElementById('tripform').submit();
	}
	save_data(finish_add_trip);
}
function on_open_trip()
{
	function finish_add_trip()
	{	
	    document.getElementById('opentripname').value=document.getElementById('choose_trip').value;
		document.getElementById('tripform').submit();
	}
	save_data(finish_add_trip);    
}



