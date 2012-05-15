"""The application's model objects"""
import sqlalchemy as sa
from sqlalchemy import orm
from datetime import datetime,timedelta
from fplan.model import meta
from sqlalchemy.dialects import postgresql

def init_model(engine):
    """Call me before using any of the tables or classes in the model"""
    ## Reflected tables must be defined and mapped here
    #global reflected_table
    #reflected_table = sa.Table("Reflected", meta.metadata, autoload=True,
    #                           autoload_with=engine)
    #orm.mapper(Reflected, reflected_table)
    #
    meta.Session.configure(bind=engine)
    meta.engine = engine


def ForeignKeyConstraint(a,b):
    return sa.ForeignKeyConstraint(a,b,onupdate="CASCADE", ondelete="CASCADE")

Unicode=sa.types.Unicode
String=sa.types.String
Integer=sa.types.Integer
Numeric=sa.types.Numeric
DateTime=sa.types.DateTime
Boolean=sa.types.Boolean
Float=sa.types.Float
Binary=sa.types.Binary


user_table = sa.Table("user",meta.metadata,
                        sa.Column("user",Unicode(32),primary_key=True, nullable=False),
                        sa.Column("password",Unicode(100),nullable=False),
                        sa.Column("realname",Unicode(100),nullable=True),
                        sa.Column("phonenr",Unicode(50),nullable=True),
                        sa.Column("isregistered",Boolean(),nullable=False),
                        sa.Column("lastlogin",DateTime(),nullable=False),
                        sa.Column('fastmap',Boolean(),nullable=False,default=True),
                        sa.Column('showobst',Boolean(),nullable=False,default=True),
                        sa.Column('fillable',Boolean(),nullable=False,default=False),
                        sa.Column('lasttrip',Unicode(50),nullable=True,default=None),
                        sa.Column('fullname',Unicode(250),nullable=True,default=None)
                        )

airport_projection = sa.Table("airport_projection",meta.metadata,
                        sa.Column('user',Unicode(32),sa.ForeignKey("user.user",onupdate="CASCADE",ondelete="CASCADE"),primary_key=True,nullable=False),
                        sa.Column('airport',Unicode(100),primary_key=True,nullable=False),
                        sa.Column('mapchecksum',String(32),primary_key=True,nullable=False),                        
                        sa.Column('updated',DateTime(),nullable=False),
                        sa.Column("matrix",postgresql.ARRAY(Float,mutable=False,as_tuple=True),nullable=False,default="")
                        )

airport_marker = sa.Table("airport_marker",meta.metadata,
                        sa.Column("user",Unicode(32),primary_key=True, nullable=False),
                        sa.Column('airport',Unicode(100),primary_key=True,nullable=False),
                        sa.Column('mapchecksum',String(32),primary_key=True,nullable=False),
                        sa.Column('latitude',Float(),primary_key=False,nullable=True),
                        sa.Column('longitude',Float(),primary_key=False,nullable=True),
                        sa.Column('x',Integer(),primary_key=True,nullable=False),
                        sa.Column('y',Integer(),primary_key=True,nullable=False),                        
                        sa.Column('weight',Float(),primary_key=False,nullable=True),                        
                        sa.ForeignKeyConstraint(
                            ['user', 'airport','mapchecksum'], 
                            ['airport_projection.user', 'airport_projection.airport','airport_projection.mapchecksum'],
                            onupdate="CASCADE",ondelete="CASCADE"
                            )                              
                        )

notam_table = sa.Table("notam",meta.metadata,
                        sa.Column('ordinal',Integer(),primary_key=True,nullable=False),
                        sa.Column('downloaded',DateTime(),nullable=False),
                        sa.Column("notamtext",Unicode(),nullable=False),
                        )




notam_category_filter_table = sa.Table("notam_category_filter",meta.metadata,
                        sa.Column('user',Unicode(32),sa.ForeignKey("user.user",onupdate="CASCADE",ondelete="CASCADE"),primary_key=True,nullable=False),
                        sa.Column('category',Unicode(),nullable=False,primary_key=True)
                        )


notam_country_filter_table = sa.Table("notam_country_filter",meta.metadata,
                        sa.Column('user',Unicode(32),sa.ForeignKey("user.user",onupdate="CASCADE",ondelete="CASCADE"),primary_key=True,nullable=False),
                        sa.Column('country',Unicode(32),nullable=False,primary_key=True)
                        )


                        
notamupdate_table = sa.Table('notamupdate',meta.metadata,
                        sa.Column('appearnotam',Integer(),sa.ForeignKey("notam.ordinal",onupdate="CASCADE",ondelete="CASCADE"),nullable=False,primary_key=True),
                        sa.Column('appearline',Integer(),nullable=False,primary_key=True),
                        sa.Column('prevnotam',Integer(),nullable=True,primary_key=False), #if this is an update of a previously existing item 
                        sa.Column('prevline',Integer(),nullable=True,primary_key=False), #the prevnotam,prevline refer to that existing item.
                        sa.Column('category',Unicode(),nullable=True),
                        sa.Column('text',Unicode(),nullable=False),
                        sa.Column('disappearnotam',Integer(),sa.ForeignKey("notam.ordinal",onupdate="CASCADE",ondelete="CASCADE"),nullable=True),
                        sa.ForeignKeyConstraint(
                            ['prevnotam', 'prevline'], 
                            ['notamupdate.appearnotam', 'notamupdate.appearline'],
                            onupdate="CASCADE",ondelete="CASCADE"
                            )
                        )
"""
notamgeo_table = sa.Table('notamgeo',meta.metadata,
                        sa.Column('user',Unicode(32),sa.ForeignKey("user.user",onupdate="CASCADE",ondelete="CASCADE"),primary_key=True,nullable=False),
                        sa.Column('appearnotam',Integer(),sa.ForeignKey("notam.ordinal",onupdate="CASCADE",ondelete="CASCADE"),nullable=False,primary_key=True),
                        sa.Column('appearline',Integer(),nullable=False,primary_key=True),
                        sa.Column("points",postgresql.ARRAY(String,mutable=False,as_tuple=True),nullable=False,default=""),
                        sa.ForeignKeyConstraint(
                            ['appearnotam', 'appearline'], 
                            ['notamupdate.appearnotam', 'notamupdate.appearline'],
                            onupdate="CASCADE",ondelete="CASCADE")
                        )
"""

notamack_table = sa.Table('notamack',meta.metadata,
                        sa.Column('user',Unicode(32),sa.ForeignKey("user.user",onupdate="CASCADE",ondelete="CASCADE"),primary_key=True,nullable=False),
                        sa.Column('appearnotam',Integer(),sa.ForeignKey("notam.ordinal",onupdate="CASCADE",ondelete="CASCADE"),nullable=False,primary_key=True),
                        sa.Column('appearline',Integer(),nullable=False,primary_key=True),
                        sa.ForeignKeyConstraint(
                            ['appearnotam', 'appearline'], 
                            ['notamupdate.appearnotam', 'notamupdate.appearline'],
                            onupdate="CASCADE",ondelete="CASCADE")
                        )
            

rating_table = sa.Table("rating",meta.metadata,
                        sa.Column('user',Unicode(32),sa.ForeignKey("user.user",onupdate="CASCADE",ondelete="CASCADE"),primary_key=True,nullable=False),
                        sa.Column("rating",Unicode(100),primary_key=True,nullable=False),
                        sa.Column("description",Unicode(),nullable=False),
                        sa.Column("valid",Boolean(),nullable=False),
                        sa.Column("lapse_date",DateTime(),nullable=True),
                        )


aircraft_table = sa.Table("aircraft",meta.metadata,
                        sa.Column('user',Unicode(32),sa.ForeignKey("user.user",onupdate="CASCADE",ondelete="CASCADE"),primary_key=True,nullable=False),
                        sa.Column('aircraft',Unicode(32),primary_key=True,nullable=False,default=u"SE-XYZ"),#Registration, like SE-VLI
                        sa.Column('atstype',Unicode(32),primary_key=False,nullable=False,default=u"ULAC"),#Type of aircraft, like ULAC
                        sa.Column('atsradiotype',Unicode(64),primary_key=False,nullable=False,default=u"Ultralight"),#Type of aircraft, like Ultralight, used on radio
                        sa.Column('markings',Unicode(32),primary_key=False,nullable=False,default=u"W"),#Color, for use in ATS-flightplan
                        sa.Column('cruise_speed',Float(),primary_key=False,nullable=False,default=75),
                        sa.Column('cruise_burn',Float(),primary_key=False,nullable=False,default=18),                        
                        sa.Column('climb_speed',Float(),primary_key=False,nullable=False,default=60),                        
                        sa.Column('climb_rate',Float(),primary_key=False,nullable=False,default=400),                        
                        sa.Column('climb_burn',Float(),primary_key=False,nullable=False,default=22),                        
                        sa.Column('descent_speed',Float(),primary_key=False,nullable=False,default=85),                        
                        sa.Column('descent_rate',Float(),primary_key=False,nullable=False,default=750),                        
                        sa.Column('descent_burn',Float(),primary_key=False,nullable=False,default=10),
                        sa.Column("advanced_model",Boolean(),nullable=False,default=False),
                        sa.Column('adv_climb_rate',postgresql.ARRAY(Float,mutable=False,as_tuple=True),primary_key=False,nullable=False,default=""),                        
                        sa.Column('adv_climb_burn',postgresql.ARRAY(Float,mutable=False,as_tuple=True),primary_key=False,nullable=False,default=""),                        
                        sa.Column('adv_climb_speed',postgresql.ARRAY(Float,mutable=False,as_tuple=True),primary_key=False,nullable=False,default=""),                        
                        sa.Column('adv_cruise_burn',postgresql.ARRAY(Float,mutable=False,as_tuple=True),primary_key=False,nullable=False,default=""),                        
                        sa.Column('adv_cruise_speed',postgresql.ARRAY(Float,mutable=False,as_tuple=True),primary_key=False,nullable=False,default=""),                        
                        sa.Column('adv_descent_rate',postgresql.ARRAY(Float,mutable=False,as_tuple=True),primary_key=False,nullable=False,default=""),                        
                        sa.Column('adv_descent_burn',postgresql.ARRAY(Float,mutable=False,as_tuple=True),primary_key=False,nullable=False,default=""),                        
                        sa.Column('adv_descent_speed',postgresql.ARRAY(Float,mutable=False,as_tuple=True),primary_key=False,nullable=False,default="")                        
                        )

trip_table = sa.Table("trip",meta.metadata,
                        sa.Column('user',Unicode(32),sa.ForeignKey("user.user",onupdate="CASCADE",ondelete="CASCADE"),primary_key=True,nullable=False),
                        sa.Column('trip',Unicode(50),primary_key=True,nullable=False),
                        sa.Column('aircraft',Unicode(32),nullable=True,primary_key=False),
                        sa.ForeignKeyConstraint(['user', 'aircraft'], ['aircraft.user', 'aircraft.aircraft'],onupdate="CASCADE",ondelete="RESTRICT")
                        )
tripcache_table = sa.Table("tripcache",meta.metadata,
                        sa.Column('user',Unicode(32),sa.ForeignKey("user.user",onupdate="CASCADE",ondelete="CASCADE"),primary_key=True,nullable=False),
                        sa.Column('trip',Unicode(50),primary_key=True,nullable=False),
                        sa.Column('key',Unicode(32),primary_key=False,nullable=False),
                        sa.Column('value',Binary(),primary_key=False,nullable=False),
                        sa.ForeignKeyConstraint(['user', 'trip'], ['trip.user', 'trip.trip'],onupdate="CASCADE",ondelete="CASCADE")
                        )


download_table = sa.Table("download",meta.metadata,
                        sa.Column('user',Unicode(32),sa.ForeignKey("user.user",onupdate="CASCADE",ondelete="CASCADE"),primary_key=True,nullable=False),
                        sa.Column("when",DateTime(),nullable=False,primary_key=True),
                        sa.Column('bytes',Numeric(20),nullable=False)
                        )

metar_table = sa.Table("metar",meta.metadata,
                        sa.Column('icao',Unicode(4),primary_key=True),
                        sa.Column("last_sync",DateTime(),nullable=False),
                        sa.Column("text",Unicode(),nullable=False))
taf_table = sa.Table("taf",meta.metadata,
                        sa.Column('icao',Unicode(4),primary_key=True),
                        sa.Column("last_sync",DateTime(),nullable=False),
                        sa.Column("text",Unicode(),nullable=False))
                        

aip_history_table = sa.Table("aip_history",meta.metadata,
                        sa.Column('aipgen',Unicode(32),primary_key=True),
                        sa.Column("when",DateTime(),nullable=False),                        
                        sa.Column('data',Binary(),primary_key=False,nullable=False),                        
                        )



recordings_table = sa.Table("recordings",meta.metadata,
                        sa.Column('user',Unicode(32),sa.ForeignKey("user.user",onupdate="CASCADE",ondelete="CASCADE"),primary_key=True,nullable=False),
                        sa.Column("start",DateTime(),nullable=False,primary_key=True),
                        sa.Column("end",DateTime(),nullable=False,primary_key=False),
                        sa.Column("duration",Float(),nullable=False,primary_key=False),
                        sa.Column("distance",Float(),nullable=False,primary_key=False),
                        sa.Column('depdescr',Unicode(100),primary_key=False,nullable=False,default=u""),
                        sa.Column('destdescr',Unicode(100),primary_key=False,nullable=False,default=u""),
                        sa.Column('trip',Binary(),primary_key=False,nullable=False,default=""),                        
                        sa.Column("version",Integer(),nullable=False,primary_key=False,default="2")
                        )
class Recording(object):
    def __init__(self, user, start):
        self.user=user
        self.start=start
                        
stay_table = sa.Table("stay",meta.metadata,
                    sa.Column('user',Unicode(32),sa.ForeignKey("user.user",onupdate="CASCADE",ondelete="CASCADE"),primary_key=True,nullable=False),
                    sa.Column('trip',Unicode(50),primary_key=True,nullable=False),
                    sa.Column('waypoint_id',Integer(),primary_key=True,nullable=False),
                    sa.Column('date_of_flight',Unicode(10),nullable=False,primary_key=False),
                    sa.Column('fuel',Float(),nullable=True,primary_key=False,default=None),
                    sa.Column('departure_time',Unicode(5),nullable=False,primary_key=False,default=u""),
                    sa.Column('nr_persons',Integer(),nullable=True,primary_key=False,default=None),
                    sa.Column('fueladjust',Float(),nullable=True,primary_key=False,default=None),
                    sa.ForeignKeyConstraint(['user', 'trip'], ['trip.user', 'trip.trip'],onupdate="CASCADE",ondelete="CASCADE"),                                                        
                    sa.ForeignKeyConstraint(['user', 'trip','waypoint_id'], ['waypoint.user', 'waypoint.trip','waypoint.id'],onupdate="CASCADE",ondelete="CASCADE"),                                                        
                    )
                        
                        

shared_trip_table = sa.Table("shared_trip",meta.metadata,
                        sa.Column('user',Unicode(32),sa.ForeignKey("user.user",onupdate="CASCADE",ondelete="CASCADE"),primary_key=True,nullable=False),
                        sa.Column('trip',Unicode(50),primary_key=True,nullable=False),
                        sa.Column("secret",Unicode(),nullable=False),
                        sa.ForeignKeyConstraint(['user', 'trip'], ['trip.user', 'trip.trip'],onupdate="CASCADE",ondelete="CASCADE"),                                                        
                        )

waypoint_table = sa.Table("waypoint",meta.metadata,
                        sa.Column('user',Unicode(32),sa.ForeignKey("user.user",onupdate="CASCADE",ondelete="CASCADE"),primary_key=True,nullable=False),
                        sa.Column('trip',Unicode(50),primary_key=True,nullable=False),
                        sa.Column('id',Integer(),primary_key=True,nullable=False),
                        sa.Column('ordering',Integer(),primary_key=False,nullable=False),
                        sa.Column('pos',String(50),primary_key=False,nullable=False),
                        sa.Column('waypoint',Unicode(50),primary_key=False,nullable=False),
                        sa.Column('altitude',String(6),primary_key=False,nullable=False,default=''),
                        sa.ForeignKeyConstraint(['user', 'trip'], ['trip.user', 'trip.trip'],onupdate="CASCADE",ondelete="CASCADE"),                                                        
                        )
route_table = sa.Table("route",meta.metadata,
                        sa.Column('user',Unicode(32),sa.ForeignKey("user.user",onupdate="CASCADE",ondelete="CASCADE"),primary_key=True,nullable=False),
                        sa.Column('trip',Unicode(50),primary_key=True,nullable=False),
                        sa.Column('waypoint1',Integer(),primary_key=True,nullable=False),                        
                        sa.Column('waypoint2',Integer(),primary_key=True,nullable=False),                        
                        sa.Column('winddir',Float(),primary_key=False,nullable=False,default=0),
                        sa.Column('windvel',Float(),primary_key=False,nullable=False,default=0),
                        sa.Column('tas',Float(),primary_key=False,nullable=False,default=75),
                        sa.Column('variation',Float(),primary_key=False,nullable=True),
                        sa.Column('deviation',Float(),primary_key=False,nullable=True),
                        sa.Column('altitude',String(6),primary_key=False,nullable=False,default='1000'),
                        sa.ForeignKeyConstraint(['user', 'trip'], ['trip.user', 'trip.trip'],onupdate="CASCADE",ondelete="CASCADE"),                                                        
                        sa.ForeignKeyConstraint(['user', 'trip', 'waypoint1'], ['waypoint.user', 'waypoint.trip', 'waypoint.id'],
                                                onupdate="CASCADE",ondelete="CASCADE"),                                                                                
                        sa.ForeignKeyConstraint(['user', 'trip', 'waypoint2'], ['waypoint.user', 'waypoint.trip', 'waypoint.id'],
                                                onupdate="CASCADE",ondelete="CASCADE")
                        )
                        
                        
"""
airport_table = sa.Table("airport",meta.metadata,                         
                        sa.Column('airport',Unicode(50),primary_key=True,nullable=False),                        
                        sa.Column('icao',String(4),primary_key=False,nullable=False),                        
                        sa.Column('pos',String(50),nullable=False,primary_key=False),
                        sa.Column('elev',Float(),nullable=True,primary_key=False)
                        ) 
obstacle_table = sa.Table("obstacle",meta.metadata,                         
                        sa.Column('obstacle',Unicode(50),primary_key=True,nullable=False),                        
                        sa.Column('lat',Float(),nullable=False,primary_key=False),
                        sa.Column('lon',Float(),nullable=False,primary_key=False),
                        sa.Column('base_altitude_msl',Float(),nullable=True,primary_key=False),
                        sa.Column('top_altitude_msl',Float(),nullable=False,primary_key=False)
                        )
"""
class Route(object):
    def __init__(self,user,trip,waypoint1,waypoint2,winddir=None,windvel=None,tas=None,variation=None,altitude=None,deviation=None):
        self.user=user
        self.trip=trip
        self.waypoint1=waypoint1
        self.waypoint2=waypoint2
        self.winddir=winddir
        self.windvel=windvel
        self.tas=tas        
        self.variation=variation
        self.altitude=altitude
        self.deviation=deviation
                 
class Waypoint(object):
    def __init__(self, user, trip, pos, id_,ordering, waypoint,altitude=''):
        self.user=user
        self.trip=trip
        self.pos=pos
        assert type(id_) in [int,long]
        assert type(ordering) in [int,long]
        self.id=id_
        self.ordering=ordering
        assert type(waypoint) in [str,unicode]
        self.waypoint=waypoint
        self.altitude=altitude
    def get_lat(self):
        return float(self.pos.split(",")[0])
    def get_lon(self):
        return float(self.pos.split(",")[1])
        
class Airport(object):
    def __init__(self, airport, icao, pos, elev):
        self.airport=airport
        self.icao=icao
        self.pos=pos
        self.elev=elev
class Trip(object):
    def __init__(self, user, trip, aircraft=None):
        self.user=user
        self.trip=trip
        self.aircraft=aircraft
class TripCache(object):
    def __init__(self, user, trip, key,value):
        self.user=user
        self.trip=trip
        self.key=key
        self.value=value
        
class Download(object):
    def __init__(self, user, bytes):
        self.user=user
        self.when=datetime.utcnow()
        self.bytes=bytes
class Stay(object):
    def __init__(self,user,trip,waypoint_id):
        self.user=user
        self.trip=trip
        self.waypoint_id=waypoint_id
        self.fuel=None        
        self.date_of_flight=datetime.utcnow().strftime("%Y-%m-%d")
        self.departure_time=(datetime.utcnow()+timedelta(0,3600)).strftime("%H:%M")
    def fuelstr(self):
        ret=""
        if self.fuel!=None:
            ret="%.1f"%(self.fuel,)
        if self.fueladjust!=None:
            if self.fueladjust<0:
                ret="%.1f"%(self.fueladjust,)
            if self.fueladjust>0:
                ret="+%.1f"%(self.fueladjust,)
        
        print "Fuelstr",self.fuel,self.fueladjust,ret
        return ret
class User(object):
    def __init__(self, user, password):        
        self.user = user
        self.password = password
        self.isregistered=False
        self.lastlogin=datetime.utcnow()
    def __unicode__(self):
        return "User(%s)"%(self.user,)
    def __repr__(self):
        return "User(%s)"%(self.user,)
        
class NotamCategoryFilter(object):
    def __init__(self,user,category):
        self.user=user
        self.category=category
class NotamCountryFilter(object):
    def __init__(self,user,country):
        self.user=user
        self.country=country
class AirportProjection(object):pass
class AirportMarker(object):pass
    
class Aircraft(object):
    def __init__(self,user,aircraft):
        self.user=user
        self.aircraft=aircraft
class SharedTrip(object):
    def __init__(self,user,trip,secret):
        self.user=user
        self.trip=trip
        self.secret=secret
class AipHistory(object):
    def __init__(self,aipgen,when,data):
        self.aipgen=aipgen
        self.when=when
        self.data=data
        
class Metar(object):
    def __init__(self,icao,last_sync,text):
        self.icao=icao
        self.last_sync=last_sync
        self.text=text
    def __repr__(self):
        return "Metar(%s,%s,%s)"%(self.icao,self.last_sync,self.text)
class Taf(object):
    def __init__(self,icao,last_sync,text):
        self.icao=icao
        self.last_sync=last_sync
        self.text=text
    def __repr__(self):
        return "Metar(%s,%s,%s)"%(self.icao,self.last_sync,self.text)
        
orm.mapper(AipHistory,aip_history_table)
orm.mapper(Metar,metar_table)
orm.mapper(Taf,taf_table)
            
orm.mapper(Aircraft,aircraft_table)    
orm.mapper(AirportProjection,airport_projection)    
orm.mapper(AirportMarker,airport_marker)    
orm.mapper(User, user_table)
orm.mapper(Download, download_table)
orm.mapper(Stay, stay_table)
orm.mapper(SharedTrip, shared_trip_table)
orm.mapper(Trip, trip_table, properties=dict(
    acobj=orm.relation(Aircraft,lazy=True)))

orm.mapper(TripCache, tripcache_table)

orm.mapper(Waypoint, waypoint_table,
    properties=dict(
    stay=orm.relation(Stay,primaryjoin=(sa.and_(
        waypoint_table.columns.user==stay_table.columns.user,
        waypoint_table.columns.trip==stay_table.columns.trip,
        waypoint_table.columns.id==stay_table.columns.waypoint_id
        )),lazy=True,foreign_keys=[
            waypoint_table.columns.user,
            waypoint_table.columns.trip,
            waypoint_table.columns.id,
        ])
    ))
orm.mapper(NotamCategoryFilter, notam_category_filter_table)
orm.mapper(NotamCountryFilter, notam_country_filter_table)
orm.mapper(Recording, recordings_table)

orm.mapper(Route, route_table,
 properties=dict(
    a=orm.relation(Waypoint,primaryjoin=(sa.and_(
        waypoint_table.columns.id==route_table.columns.waypoint1,
        waypoint_table.columns.user==route_table.columns.user,
        waypoint_table.columns.trip==route_table.columns.trip,
        )),lazy=True),
    b=orm.relation(Waypoint,primaryjoin=(sa.and_(
        waypoint_table.columns.id==route_table.columns.waypoint2,
        waypoint_table.columns.user==route_table.columns.user,
        waypoint_table.columns.trip==route_table.columns.trip,
        )),lazy=True)
))


class Notam(object):
    def __init__(self,ordinal,downloaded,notamtext):
        self.ordinal=ordinal
        self.downloaded=downloaded
        self.notamtext=notamtext
    def __repr__(self):
        return u"Notam(%s,%s,%d chars)"%(self.ordinal,self.downloaded,len(self.notamtext))


class NotamUpdate(object):
    def __init__(self,appearnotam,appearline,category,text):
        self.appearnotam=appearnotam
        self.appearline=appearline
        self.category=category
        self.text=text
        self.disappearnotam=None
    def __repr__(self):
        return u"NotamUpdate(notam=%d,line=%d,category=%s,text=%s,disappear=%s,prev=%s)"%(
            self.appearnotam,self.appearline,self.category,self.text[0:50].splitlines()[0],self.disappearnotam,self.prev)
         

class NotamAck(object):
    def __init__(self,user,notam,line):
        self.user=user
        self.appearnotam=notam
        self.appearline=line

orm.mapper(Notam,notam_table,
    properties=dict(
        items=(orm.relation(NotamUpdate,
            order_by=notamupdate_table.columns.appearline,
            primaryjoin=(notam_table.columns.ordinal==notamupdate_table.columns.appearnotam),
            lazy=True,cascade="all, delete-orphan")),
        removeditems=(orm.relation(NotamUpdate,
            order_by=notamupdate_table.columns.appearline,
            primaryjoin=(notam_table.columns.ordinal==notamupdate_table.columns.disappearnotam),
            lazy=True,cascade="all, delete-orphan")),
    )
)

    
orm.mapper(NotamUpdate, notamupdate_table,
 properties=dict(
    notam=orm.relation(Notam,
        primaryjoin=(
                notamupdate_table.columns.appearnotam==notam_table.columns.ordinal  ),
        lazy=True),
    prev=orm.relation(NotamUpdate,
        remote_side=[notamupdate_table.columns.appearnotam,
                     notamupdate_table.columns.appearline],
        lazy=True)
))
                        

orm.mapper(NotamAck, notamack_table)



#orm.mapper(Airport, airport_table)


## Non-reflected tables may be defined and mapped at module level
#foo_table = sa.Table("Foo", meta.metadata,
#    sa.Column("id", sa.types.Integer, primary_key=True),
#    sa.Column("bar", sa.types.String(255), nullable=False),
#    )
#
#class Foo(object):
#    pass
#
#orm.mapper(Foo, foo_table)


## Classes for reflected tables may be defined here, but the table and
## mapping itself must be done in the init_model function
#reflected_table = None
#
#class Reflected(object):
#    pass
