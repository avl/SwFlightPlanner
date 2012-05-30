
<%inherit file="base.mako"/>
<script src="/wz_jsgraphics.js" type="text/javascript"></script>
<script src="/mapmath.js" type="text/javascript"></script>

<script type="text/javascript">


width=${c.width};
height=${c.height};
map_zoomlevel=13;

base_coords=[
%for bc in c.base_coords:
[${bc[0]},${bc[1]}],
%endfor 
0
]

function pixel2merc(x,y)
{
	var values=[x,y];
	var out=[0,0];
	for(var i=0;i<2;++i)
	{
		var cx=x/width;
		var cy=y/height;
		
		var value=values[i];
		var l=(1-cy)*base_coords[0][i]+(cy)*base_coords[2][i];
		var r=(1-cy)*base_coords[1][i]+(cy)*base_coords[3][i];
		out[i]=(1-cx)*l+cx*r;
	}	
	return out;
}


function findAbsolutePosition(obj) {
	var curleft = 0;
	var curtop = 0;
	if (obj.offsetParent) {
		do {
			curleft += obj.offsetLeft;
			curtop += obj.offsetTop;
		} while (obj = obj.offsetParent);
	}
	return [curleft,curtop];
}


cur_idx=null;
%for num,mark in enumerate(c.markers):
%if c.curadmarker==(mark.x,mark.y):
cur_idx=${num};
%endif
%endfor

runways=[
%for num,rwy in enumerate(c.runways):
%if num!=0:
,
%endif
[${rwy[0][0]},${rwy[0][1]},${rwy[1][0]},${rwy[1][1]}]
%endfor
];

marks=[
%for num,mark in enumerate(c.markers):
%if num!=0:
,
%endif
[${mark.x},${mark.y},'${h.degmin(mark.latitude) if mark.latitude else ""}','${h.degmin(mark.longitude) if mark.longitude else ""}']
%endfor	

];

	revmarks=[
%for num,rev in enumerate(c.revmarkers):
%if num!=0:
,
%endif
[${rev[0]},${rev[1]}]
%endfor
]

function drawall()
{
	jg.clear();
    jg.setFont("arial","14px",Font.BOLD);
%if c.transform_reasonable:
    jg.setColor("#ff0000");
	for(var i=0;i<revmarks.length;++i)
	{
		rm=revmarks[i];	
		var x=rm[0];
		var y=rm[1]
		jg.drawLine(x-5,y-5,x-20,y-20);
		jg.drawLine(x+5,y-5,x+20,y-20);
		jg.drawLine(x+5,y+5,x+20,y+20);
		jg.drawLine(x-5,y+5,x-20,y+20);		
		jg.drawString('R'+i,x+25,y-4);
	}

    jg.setColor("#0000ff");
	for(var i=0;i<runways.length;++i)
	{
		var rwy=runways[i];
		jg.drawLine(rwy[0],rwy[1],rwy[2],rwy[3]);
	}
	
	{
		var x=${c.arp[0]};
		var y=${c.arp[1]};
		var x1=${c.arp1[0]};
		var y1=${c.arp1[1]};
		var x2=${c.arp2[0]};
		var y2=${c.arp2[1]};
		jg.drawLine(x-5,y-5,x-20,y-20);
		jg.drawLine(x+5,y-5,x+20,y-20);
		jg.drawLine(x+5,y+5,x+20,y+20);
		jg.drawLine(x-5,y+5,x-20,y+20);		
	    jg.drawString('ARP',x+25,y-4);
		jg.setColor("#00ff00");
		jg.drawLine(x,y,x1,y1);
		jg.drawLine(x,y,x2,y2);
		jg.setColor("#ffffff");
        jg.fillRect(x+30,y-30,125,15);			    				
		jg.setColor("#00ff00");
		jg.drawString('Squish:${"%.3f%%"%(100.0*c.ratio,)}',x+30,y-30);
	}			    				
%endif	
	
	for(var i=0;i<marks.length;++i)
	{
		var x=marks[i][0];
		var y=marks[i][1];
		jg.setColor("#ffffff");
        jg.fillRect(x+25,y-5,125,15);			    				
		if (i==cur_idx)		
			jg.setColor("#00ff00");
		else
			jg.setColor("#0000ff");
		
		jg.drawLine(x-10,y,x-3,y);
		jg.drawLine(x+3,y,x+10,y);
		jg.drawLine(x,y+3,x,y+10);
		jg.drawLine(x,y-10,x,y-3);		
        jg.drawString('#'+i+' lat:'+marks[i][2]+' lon:'+marks[i][3],x+25,y-4);			    				
	}
    jg.paint();

}


function domark(x,y)
{
	if (cur_idx==null)
		return;
	var v=document.getElementById('lowerpart');
	var abspos=findAbsolutePosition(v);	
	x+=v.scrollLeft;
	y+=v.scrollTop;
	x-=abspos[0];
	y-=abspos[1];
	
%if c.maptype!='base':
	var mx=document.getElementById('curmarker_x');
	mx.value=x;
	var my=document.getElementById('curmarker_y');
	my.value=y;
	marks[cur_idx]=[x,y];	
	//jg.fillRect(screen_x-3,screen_y-3,6,6);
	drawall();
	var m=document.getElementById('curmarker_latitude');
	if (m) m.focus();	
%endif
%if c.maptype=='base':
	var latlon=merc2latlon(pixel2merc(x,y));
	var mx=document.getElementById('curmarker_latitude');
	mx.value=latlon[0];
	var my=document.getElementById('curmarker_longitude');
	my.value=latlon[1];
%endif	
	
	
}
function navigate_to(where)
{	
	function finish_nav()
	{				
		window.location.href=where;
	}
	finish_nav();
}


function update_scroll()
{
	var v=document.getElementById('lowerpart');
	var sx=document.getElementById('scroll_x');
	var sy=document.getElementById('scroll_y');
	sx.value=v.scrollLeft;
	sy.value=v.scrollTop;	
}
function select_maptype(maptype)
{
	var mt=document.getElementById('maptype');
	mt.value=maptype;
	var mf=document.getElementById('mainform');
	mf.submit();
}
function loadproj()
{
	var l=document.getElementById('lowerpart');
	var cont=document.getElementById('content');
	var rest=cont.offsetHeight;
	l.style.height=''+rest+'px';
	
	var h=l.offsetHeight;
	var w=l.offsetWidth;
	var left=l.offsetLeft;
	var top=l.offsetTop;
	
	var htm='';


	htm+='<div style="position:relative;z-index:0;left:'+0+'px;top:'+0+'px;width:'+w+'px;height:'+h+'px;">'+
	

%if c.maptype=='chart' or c.maptype=='both':	
'<img style="position:absolute;z-index:2;left:0px;top:0px;${"opacity:0.4;" if c.maptype=='both' else ""}" id="imageid" src="${h.url_for(controller='airportproj',action='showimg',random=c.random,variant=c.variant,adimg=c.img,maptype='chart')}"/>'+
%endif			
%if c.maptype=='base' or c.maptype=='both':	
'<img style="position:absolute;z-index:1;left:0px;top:0px;" id="imageid" src="${h.url_for(controller='airportproj',action='showimg',random=c.random,variant=c.variant,adimg=c.img,maptype='base')}"/>'+
%endif
	'<div id="overlay1" style="position:absolute;z-index:3;left:'+0+'px;top:'+0+'px;width:'+w+'px;height:'+h+'px;" />'+
			
		'</div';
		
	l.innerHTML=htm;
	
	
	
		
	jg = new jsGraphics("overlay1");
	jg.setStroke("3");
	jg.setColor("#00d000");
	
	drawall();
	var m=document.getElementById('curmarker_latitude');
	if (m)
		m.focus();
		
	var v=document.getElementById('lowerpart');
	v.scrollTop=${c.initial_scroll_y};
	v.scrollLeft=${c.initial_scroll_x};
	
	v.onscroll=update_scroll;
	update_scroll();
	
}
addLoadEvent(loadproj);


</script>
<table>
<tr>
<td style="width:25%;height:100%;overflow:auto">

<h1>Airport Projection</h1>
<a href="${h.url_for(controller="airportproj",action="index")}">back</a>

<div>


<form id="mainform" action="${h.url_for(controller='airportproj',action='save')}" method="POST">
Size(mm): ${c.mapsize}<br/>
Scale: <input type="text" name="scale" value="${c.scale}" /><br/>
North: <input type="text" name="north" value="${c.north}" /><br/>
Maptype: 
<button 
%if c.maptype=='chart':
style="background-color:#00ff00"
%endif
onClick="select_maptype('chart');return false;"
>
chart
</button>

<button 
%if c.maptype=='base':
style="background-color:#00ff00"
%endif
onClick="select_maptype('base');return false;"
>
base
</button>
<button
%if c.maptype=='both':
style="background-color:#00ff00"
%endif
onClick="select_maptype('both');return false;"
>
both
</button>


<div>
%if c.flash:
<b>${c.flash}</b>
%endif
<input type="hidden" name="ad" value="${c.ad}"/>
<input type="hidden" name="mapchecksum" value="${c.mapchecksum}"/>
<input id="scroll_x" type="hidden" name="scroll_x" value=""/>
<input id="scroll_y" type="hidden" name="scroll_y" value=""/>
<input id="maptype" type="hidden" name="maptype" value="${c.maptype}"/>
<table>
<tr>
<td></td><td>Image X</td><td>Image Y</td><td>Latitude</td><td>Longitude</td><td>action</td>
</tr>
%for num,mark in enumerate(c.markers):
%if c.curadmarker==(mark.x,mark.y):
<tr style="background:#80ff80">
%endif
%if c.curadmarker!=(mark.x,mark.y):
<tr>
%endif
<td>
${'#%d'%(num)}
</td>
%for attrib in ['x','y','latitude','longitude']:
<td>
<input size="3"
%if c.curadmarker==(mark.x,mark.y):
id="curmarker_${attrib}";
%endif
type="text" name="mark_${mark.x}_${mark.y}_${attrib}" 
%if attrib in ['latitude','longitude']:
value="${h.degmin(getattr(mark,attrib))}"
%endif
%if not (attrib in ['latitude','longitude']):
value="${getattr(mark,attrib)}"
%endif

/>
</td>
%endfor
<td>
<input type="submit" name="set_${mark.x}_${mark.y}" value="set" />
<input type="submit" name="del_${mark.x}_${mark.y}" value="del" />
</td>
</tr>
%endfor
</table>
</div>
<div>
<input type="submit" name="save" value="save"/>
<input type="submit" name="add" value="add marker"/> Add a marker, then click in map below on a point with either a known latitude, a known longitude, or both. Then enter the longitude or latitude above for the newly added mark.
</div>
</form>
</div>
</td>
<td style="width:100%;height:100%">

<div id="lowerpart" onclick="domark(event.clientX,event.clientY);return true;" style="height:100%;width:100%;overflow:auto;	">


</div>

</td>
</tr>
</table>

