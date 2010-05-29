"""The application's model objects"""
import sqlalchemy as sa
from sqlalchemy import orm

from fplan.model import meta

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
DateTime=sa.types.DateTime
Boolean=sa.types.Boolean
Float=sa.types.Float

user_table = sa.Table("user",meta.metadata,
                        sa.Column("user",Unicode(32),primary_key=True, nullable=False),
                        sa.Column("password",Unicode(100),nullable=False),
                        sa.Column("isregistered",Boolean(),nullable=False)
                        )

rating_table = sa.Table("rating",meta.metadata,
                        sa.Column('user',Unicode(32),sa.ForeignKey("user.user"),primary_key=True,nullable=False),
                        sa.Column("rating",Unicode(100),primary_key=True,nullable=False),
                        sa.Column("description",Unicode(),nullable=False),
                        sa.Column("valid",Boolean(),nullable=False),
                        sa.Column("lapse_date",DateTime(),nullable=True)
                        )
plane_type_table = sa.Table("plane_type",meta.metadata,
                        sa.Column('user',Unicode(32),sa.ForeignKey("user.user"),primary_key=True,nullable=False),
                        sa.Column('plane_type',Unicode(50),nullable=False,primary_key=False),
                        sa.Column('tas_sealevel_cruise',Float(),nullable=False,primary_key=False),
                        sa.Column('power_sealevel_cruise',Float(),nullable=False,primary_key=False),
                        sa.Column("fuel_consumption_sealevel_cruise",Float(),nullable=False,primary_key=False),
                        sa.Column('ceiling',Float(),nullable=False,primary_key=False),
                        sa.Column('stall_speed',Float(),nullable=False,primary_key=False),                        
                        )

plane_table = sa.Table("plane",meta.metadata,
                        sa.Column('user',Unicode(32),sa.ForeignKey("user.user"),primary_key=True,nullable=False),
                        sa.Column('plane',Unicode(32),primary_key=True,nullable=False),#Registration, like SE-VLI
                        sa.Column('plane_type',Unicode(50),nullable=False),
                        sa.ForeignKeyConstraint(['user', 'plane_type'], ['plane_type.user', 'plane_type.plane_type'],onupdate="CASCADE",ondelete="CASCADE"),                                                        
                        )

trip_table = sa.Table("trip",meta.metadata,
                        sa.Column('user',Unicode(32),sa.ForeignKey("user.user"),primary_key=True,nullable=False),
                        sa.Column('trip',Unicode(50),primary_key=True,nullable=False),
                        sa.Column('plane',Unicode(32),nullable=True,primary_key=False),
                        sa.ForeignKeyConstraint(['user', 'plane'], ['plane.user', 'plane.plane'],onupdate="CASCADE",ondelete="CASCADE"),                                                        
                        )

waypoint_table = sa.Table("waypoint",meta.metadata,
                        sa.Column('user',Unicode(32),sa.ForeignKey("user.user"),primary_key=True,nullable=False),
                        sa.Column('trip',Unicode(50),primary_key=True,nullable=False),
                        sa.Column('pos',String(30),primary_key=True,nullable=False),
                        sa.Column('ordinal',Integer(),primary_key=False,nullable=False),
                        sa.Column('waypoint',Unicode(50),primary_key=False,nullable=False),
                        sa.ForeignKeyConstraint(['user', 'trip'], ['trip.user', 'trip.trip'],onupdate="CASCADE",ondelete="CASCADE"),                                                        
                        )
route_table = sa.Table("route",meta.metadata,
                        sa.Column('user',Unicode(32),sa.ForeignKey("user.user"),primary_key=True,nullable=False),
                        sa.Column('trip',Unicode(50),primary_key=True,nullable=False),
                        sa.Column('waypoint1',String(30),primary_key=True,nullable=False),                        
                        sa.Column('waypoint2',String(30),primary_key=True,nullable=False),                        
                        sa.Column('winddir',Float(),primary_key=False,nullable=False),
                        sa.Column('windvel',Float(),primary_key=False,nullable=False),
                        sa.Column('tas',Float(),primary_key=False,nullable=False),
                        sa.Column('variation',Float(),primary_key=False,nullable=True),
                        sa.Column('altitude',String(6),primary_key=False,nullable=False),
                        sa.ForeignKeyConstraint(['user', 'trip', 'waypoint1'], ['waypoint.user', 'waypoint.trip', 'waypoint.pos'],
                                                onupdate="CASCADE",ondelete="CASCADE"),                                                                                
                        sa.ForeignKeyConstraint(['user', 'trip', 'waypoint2'], ['waypoint.user', 'waypoint.trip', 'waypoint.pos'],
                                                onupdate="CASCADE",ondelete="CASCADE")                                                                                
                        )
                        
                        

airport_table = sa.Table("airport",meta.metadata,                         
                        sa.Column('airport',Unicode(50),primary_key=True,nullable=False),                        
                        sa.Column('icao',String(4),primary_key=False,nullable=False),                        
                        sa.Column('pos',String(30),nullable=False,primary_key=False),
                        sa.Column('elev',Float(),nullable=True,primary_key=False)
                        ) 
obstacle_table = sa.Table("obstacle",meta.metadata,                         
                        sa.Column('obstacle',Unicode(50),primary_key=True,nullable=False),                        
                        sa.Column('lat',Float(),nullable=False,primary_key=False),
                        sa.Column('lon',Float(),nullable=False,primary_key=False),
                        sa.Column('base_altitude_msl',Float(),nullable=True,primary_key=False),
                        sa.Column('top_altitude_msl',Float(),nullable=False,primary_key=False)
                        )

class Route(object):
    def __init__(self,user,trip,waypoint1,waypoint2,winddir,windvel,tas,variation,altitude):
        self.user=user
        self.trip=trip
        self.waypoint1=waypoint1
        self.waypoint2=waypoint2
        self.winddir=winddir
        print "Creating Route with windvel",windvel
        self.windvel=windvel
        self.tas=tas        
        self.variation=variation
        self.altitude=altitude
                 
class Waypoint(object):
    def __init__(self, user, trip, pos, ordinal, waypoint):
        self.user=user
        self.trip=trip
        self.pos=pos
        self.ordinal=ordinal
        self.waypoint=waypoint
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
    def __init__(self, user, trip):
        self.user=user
        self.trip=trip
class User(object):
    def __init__(self, user, password):        
        self.user = user
        self.password = password
        self.isregistered=False
    def __unicode__(self):
        return "User(%s)"%(self.user,)
    def __repr__(self):
        return "User(%s)"%(self.user,)
    
orm.mapper(User, user_table)
orm.mapper(Trip, trip_table)
orm.mapper(Waypoint, waypoint_table)
orm.mapper(Route, route_table)
orm.mapper(Airport, airport_table)


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
