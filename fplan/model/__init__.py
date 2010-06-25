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
                        sa.Column("isregistered",Boolean(),nullable=False),
                        sa.Column('fastmap',Boolean(),nullable=False,default=True)
                        )

notam_table = sa.Table("notam",meta.metadata,
                        sa.Column('ordinal',Integer(),primary_key=True,nullable=False),
                        sa.Column('downloaded',DateTime(),nullable=False),
                        sa.Column("notamtext",Unicode(),nullable=False)
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
                            ['notamupdate.appearnotam', 'notamupdate.appearline'])
                        )


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
                        sa.Column('aircraft',Unicode(32),primary_key=True,nullable=False,default="SE-XYZ"),#Registration, like SE-VLI
                        sa.Column('cruise_speed',Float(),primary_key=False,nullable=False,default=75),                        
                        sa.Column('cruise_burn',Float(),primary_key=False,nullable=False,default=18),                        
                        sa.Column('climb_speed',Float(),primary_key=False,nullable=False,default=60),                        
                        sa.Column('climb_rate',Float(),primary_key=False,nullable=False,default=400),                        
                        sa.Column('climb_burn',Float(),primary_key=False,nullable=False,default=22),                        
                        sa.Column('descent_speed',Float(),primary_key=False,nullable=False,default=85),                        
                        sa.Column('descent_rate',Float(),primary_key=False,nullable=False,default=750),                        
                        sa.Column('descent_burn',Float(),primary_key=False,nullable=False,default=10)                      
                        )

trip_table = sa.Table("trip",meta.metadata,
                        sa.Column('user',Unicode(32),sa.ForeignKey("user.user",onupdate="CASCADE",ondelete="CASCADE"),primary_key=True,nullable=False),
                        sa.Column('trip',Unicode(50),primary_key=True,nullable=False),
                        sa.Column('aircraft',Unicode(32),nullable=True,primary_key=False),
                        sa.ForeignKeyConstraint(['user', 'aircraft'], ['aircraft.user', 'aircraft.aircraft'],onupdate="CASCADE",ondelete="CASCADE"),                                                        
                        )


waypoint_table = sa.Table("waypoint",meta.metadata,
                        sa.Column('user',Unicode(32),sa.ForeignKey("user.user",onupdate="CASCADE",ondelete="CASCADE"),primary_key=True,nullable=False),
                        sa.Column('trip',Unicode(50),primary_key=True,nullable=False),
                        sa.Column('ordinal',Integer(),primary_key=True,nullable=False),
                        sa.Column('pos',String(50),primary_key=False,nullable=False),
                        sa.Column('waypoint',Unicode(50),primary_key=False,nullable=False),
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
                        sa.ForeignKeyConstraint(['user', 'trip', 'waypoint1'], ['waypoint.user', 'waypoint.trip', 'waypoint.ordinal'],
                                                onupdate="CASCADE",ondelete="CASCADE"),                                                                                
                        sa.ForeignKeyConstraint(['user', 'trip', 'waypoint2'], ['waypoint.user', 'waypoint.trip', 'waypoint.ordinal'],
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
    def __init__(self,user,trip,waypoint1,waypoint2,winddir=None,windvel=None,tas=None,variation=None,altitude=None):
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
    def __init__(self, user, trip, aircraft=None):
        self.user=user
        self.trip=trip
        self.aircraft=aircraft
class User(object):
    def __init__(self, user, password):        
        self.user = user
        self.password = password
        self.isregistered=False
    def __unicode__(self):
        return "User(%s)"%(self.user,)
    def __repr__(self):
        return "User(%s)"%(self.user,)
class Aircraft(object):
    def __init__(self,user,aircraft):
        self.user=user
        self.aircraft=aircraft
    
orm.mapper(Aircraft,aircraft_table)    
orm.mapper(User, user_table)
orm.mapper(Trip, trip_table, properties=dict(
    acobj=orm.relation(Aircraft,lazy=True)))

orm.mapper(Waypoint, waypoint_table)
orm.mapper(Route, route_table,
 properties=dict(
    a=orm.relation(Waypoint,primaryjoin=(waypoint_table.columns.ordinal==route_table.columns.waypoint1),lazy=True),
    b=orm.relation(Waypoint,primaryjoin=(waypoint_table.columns.ordinal==route_table.columns.waypoint2),lazy=True)
))


class Notam(object):
    def __init__(self,ordinal,downloaded,notamtext):
        self.ordinal=ordinal
        self.downloaded=downloaded
        self.notamtext=notamtext
    def __repr__(self):
        return u"Notam(%s,%s,%s,%d chars)"%(self.ordinal,self.downloaded,len(self.notamtext))
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
            primaryjoin=(notam_table.columns.ordinal==notamupdate_table.columns.appearnotam))),
        removeditems=(orm.relation(NotamUpdate,
            order_by=notamupdate_table.columns.appearline,
            primaryjoin=(notam_table.columns.ordinal==notamupdate_table.columns.disappearnotam))),
    )
)

    
orm.mapper(NotamUpdate, notamupdate_table,
 properties=dict(
    notam=orm.relation(Notam,
        primaryjoin=(
                notamupdate_table.columns.appearnotam==notam_table.columns.ordinal  ),
        lazy=False),
    prev=orm.relation(NotamUpdate,
        remote_side=[notamupdate_table.columns.appearnotam,
                     notamupdate_table.columns.appearline],
        lazy=False)
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
