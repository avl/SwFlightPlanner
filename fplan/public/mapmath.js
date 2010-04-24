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
function to_latlon(p)
{
	px=p[0];
	py=p[1];
	if (map_ysize==0)
	{
		return [0,0];
	}
	var min_merc_y=to_y(map_proj_lat-0.5*map_proj_size);
	var max_merc_y=to_y(map_proj_lat+0.5*map_proj_size);
	
	var x=(px)/(map_xsize+0.0);
	var y=(map_ysize-py)/(map_ysize+0.0);
	
	var wfactor=map_xsize/map_ysize;
	var cury=y*(max_merc_y-min_merc_y)+min_merc_y;
	var lat=to_lat(cury);
					
	var lon=map_proj_lon-0.5*map_proj_lonwidth*wfactor+map_proj_lonwidth*x*wfactor;	
	lon = lon % 360.0;
	if (lon>180.0) lon=lon-360.0;
	if (lon<-180.0) lon=lon+360.0;
	
	return [lat,lon];	
}

function to_merc(latlon)
{
	var lat=latlon[0];
	var lon=latlon[1];
	if ((lon-map_proj_lon)>180.0)
	{
		lon-=360.0;
	}
	if ((lon-map_proj_lon)<-180.0)
	{
		lon+=360.0;
	}
	var wfactor=map_xsize/map_ysize;
	var min_merc_y=to_y(map_proj_lat-0.5*map_proj_size);
	var max_merc_y=to_y(map_proj_lat+0.5*map_proj_size);
	var cury=to_y(lat);
	var y=(cury-min_merc_y)/(max_merc_y-min_merc_y);
	var x=(lon+0.5*map_proj_lonwidth*wfactor-map_proj_lon)/(map_proj_lonwidth*wfactor);
	
	var px=x*(map_xsize+0.0);
	var py=map_ysize-y*(map_ysize+0.0);
	return [px,py];	
}
function sinh(x) 
{
	return (Math.exp(x) - Math.exp(-x))/2.0;
}
function to_lat(y)
{
	return (180.0/Math.PI)*Math.atan(sinh(y));
}
function to_y(lat)
{
	lat/=(180.0/Math.PI);
	return Math.log(Math.tan(lat)+1.0/Math.cos(lat));
} 
