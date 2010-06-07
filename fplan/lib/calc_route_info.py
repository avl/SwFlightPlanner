from fplan.model import meta,User,Trip,Waypoint,Route,Aircraft
import fplan.lib.mapper as mapper
import math

def get_route(c,user,trip):
    tripobj=meta.Session.query(Trip).filter(sa.and_(
            Trip.user==user,Trip.trip==trip)).one()
     
    waypoints=list(meta.Session.query(Waypoint).filter(sa.and_(
             Waypoint.user==user,Waypoint.trip==session['current_trip'])).order_by(Waypoint.ordinal).all())
    
    routes=[]
    for a,b in zip(c.waypoints[:-1],c.waypoints[1:]):
        rts=list(meta.Session.query(Route).filter(sa.and_(
            Route.user==user,Route.trip==trip,
            Route.waypoint1==a.ordinal,Route.waypoint2==b.ordinal)).all())
        assert len(rts)<2 and len(rts)>=0
        if len(rts)==0:
            rt=Route(user=user,trip=trip,waypoint1=a.ordinal,waypoint2=b.ordinal,winddir=None,windvel=None,tas=None,variation=None,altitude="1000")
            meta.Session.add(rt)
        else:
            rt=rts[0]
        rt.a=a
        rt.b=b        
        routes.append(rt)
    for rt in routes:
        rt.tt,D=mapper.bearing_and_distance(rt.a.pos,rt.b.pos)
        rt.d=D/1.852
        if rt.tas==None:
            rt.tas=tripobj.acobj.cruise_speed
            
        ac=meta.Session.query(Aircraft).filter(sa.and_(
            Aircraft.user==user,Aircraft.aircraft==tripobj.aircraft
            Route.user==user,Route.trip==trip,
            Route.waypoint1==a.ordinal,Route.waypoint2==b.ordinal)).one()

		f=1.0/(180.0/math.pi)
		wca=0
		GS=0

		winddir=(rt.winddir+180) - rt.tt
		windx=math.cos(winddir*f)*rt.windvel
		windy=math.sin(winddir*f)*rt.windvel
		if (windy>tas or -windy>tas):
			if (windy>tas):
				wca=-90
			else:
				wca=90
			GS=0;
		else
		{
			if (-windx<tas)
			{
				wca=-Math.asin(windy/tas)/f;
				
				var tas_x=Math.cos(wca*f)*tas;
				var tas_y=Math.sin(wca*f)*tas;
				GS = Math.sqrt((tas_x+windx)*(tas_x+windx)+(tas_y+windy)*(tas_y+windy));
			}
			else
			{
				wca=0;
				GS=0;
			}			
		}		
		/* True = Air + Wind -> Air = True - Wind*/
		var wcae=gete(idx,'WCA');
		if (wca>0)
			wcae.value='+'+wca.toFixed(0);
		else
			wcae.value=''+wca.toFixed(0);
		
		var gse=gete(idx,'GS');
		gse.value=GS.toFixed(0);
		next=1;	
	}
	if (next || col=='TAS' || col=='W' || col=='V' || col=='Var' || col=='Dev')
	{
		var tt=get(idx,'TT');
		var wca=get(idx,'WCA');
		var var_=get(idx,'Var');
		var dev=get(idx,'Dev');
		var ch=gete(idx,'CH');
		ch.value=parseInt(0.5+tt+wca-var_-dev)%360;
	}	
	if (next || col=='TAS' || col=='W' || col=='V' || col=='Var' || col=='Dev')
	{
		var gs=get(idx,'GS');
		var D=get(idx,'D');
		var time=gete(idx,'Time');
		if (gs>0.0)
		{
			time_hours=D/gs;
			time.value=format_time(time_hours);
			idx2time_hours[idx]=time_hours;
		}
		else
		{
			time.value="-";
			idx2time_hours[idx]=1e30;
		}
		
       
    
    
    
    return dict(waypoints=waypoints,
                routes=routes)
