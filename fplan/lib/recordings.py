import struct
import fplan.lib.mapper as mapper
from datetime import datetime
from fplanquick.fplanquick import decode_flightpath
from fplan.model import Recording
from md5 import md5

def parseRecordedTrip(user,inp,headers_only=False):
	
	def readShort():
		return struct.unpack(">H",inp.read(2))[0]
	def readInt():
		return struct.unpack(">I",inp.read(4))[0]
	def readLong():
		return struct.unpack(">Q",inp.read(8))[0]
	def readUTF():
		len=readShort()
		#print "Read string of length %d"%(len,)
		data=inp.read(len)
		return unicode(data,"utf8")
	
	magic=readInt()
	#print "magic",magic
	#print "magic:",hex(magic)
	if magic!=0xfafafa01:
		raise Exception("Bad magic in uploaded file")
	version=readInt()
	if version<2 or version>3:
		raise Exception("Version not even supported by server: %d"%(version,))
	departure=readUTF()
	destination=readUTF()
	buf=inp.read()
	#print "Read %d bytes to parse using c++ optimized triplog decoding routine"%(len(buf),)
	path=decode_flightpath(buf,version)
	startstamp=path['startstamp']
	endstamp=path['endstamp']
	startpos=path['startpos']
	endpos=path['endpos']
	distance=path['distance']
	path=path['path']
	#print "uploaded stamp:",startstamp
	rec=Recording(user,datetime.utcfromtimestamp(startstamp//1000))
	rec.end=datetime.utcfromtimestamp(endstamp//1000)
	rec.duration=float(endstamp-startstamp)
	rec.distance=distance
	rec.depdescr=departure[:99]
	rec.destdescr=destination[:99]
	rec.trip=buf
	rec.version=version
						
	return rec	
class Track():pass
			
def load_recording(rec):
	print "Rec.trip type:",type(rec.trip)
	path=decode_flightpath(str(rec.trip),rec.version)
	dynamic_id=md5(rec.trip).hexdigest()	
	out=Track()
	out.points=[]
	maxlat=-1000
	maxlon=-1000
	minlat=1000
	minlon=1000
	laststamp=None
	numpoints=path['path']
	le=len(numpoints)
	cutoff=le
	for idx,(pos,stamp,altitude) in enumerate(path['path']):
		lat,lon=mapper.merc2latlon(pos,17)
		maxlat=max(maxlat,lat)
		minlat=min(minlat,lat)
		maxlon=max(maxlon,lon)
		minlon=min(minlon,lon)
		if laststamp==None or stamp-laststamp>cutoff or idx==le-1:
			out.points.append(((lat,lon),altitude*0.3048,datetime.utcfromtimestamp(stamp/1000.0)))
		laststamp=stamp
	out.bb1=(maxlat,minlon)
	out.bb2=(minlat,maxlon)
	out.dynamic_id=dynamic_id
	return out
