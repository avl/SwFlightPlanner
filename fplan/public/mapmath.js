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
function format_distance(meters,extra)
{
	var naut=meters/1852.0;
	if (naut<10.0)
		prec=1;
	if (extra)
	{
		if (meters<1000.0)
		{
			return ''+naut.toFixed(prec)+" NM ("+meters.toFixed(0)+' m)';
		}
		else
		{
			kilometers=meters/1000.0;
			prec=0;
			if (kilometers<10) prec=1;
			return ''+naut.toFixed(prec)+" NM ("+kilometers.toFixed(prec)+' km)';
		}
	}
	else
	{
		return ''+naut.toFixed(prec)+" NM";
	}
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


function sec(x)
{
    return 1.0/Math.cos(x);
}
function sinh(x) 
{
	return (Math.exp(x) - Math.exp(-x))/2.0;
}
function merc(lat)
{
    lat=lat/(180.0/3.14159);
    return Math.log(Math.tan(lat)+sec(lat));
}
function unmerc(y)
{
    return (180.0/3.14159)*Math.atan(sinh(y));
}
function latlon2merc(latlon)
{
	var lat=latlon[0];
	var lon=latlon[1];
    var factor=Math.pow(2.0,map_zoomlevel);
    return [parseInt(factor*256.0*(lon+180.0)/360.0),parseInt(128*factor-128*factor*merc(lat)/merc(85.05113))];
    
}
function merc2latlon(xy)
{
	var x=xy[0];
	var y=xy[1];
    var factor=Math.pow(2.0,map_zoomlevel);
    return [unmerc((128*factor-y)/128.0/factor*merc(85.05113)),x*360.0/(256.0*factor)-180.0];
}
