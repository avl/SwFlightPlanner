from struct import pack
from StringIO import StringIO
import zlib

def android_fplan_hmap_format(hmap):
    out=StringIO()
    print "Binary hmap download in progress"

    def writeFloat(f):
        out.write(pack(">f",f))
    def writeInt(i):
        assert i>=-(1<<31) and i<(1<<31)
        out.write(pack(">I",i))
    def writeBuf(encoded):
        assert type(encoded)==str
        l=len(encoded)
        assert l<65000
        out.write(pack(">I",l)) #short
        out.write(encoded)
    
    writeInt(len(hmap)) #zoomlevels    
    for zoomlevel,tiles in hmap.items():
        writeInt(zoomlevel)
        writeInt(len(tiles)) #tiles in this zoomlevel
        for merc,tile in tiles.items():
            #print "Zoom: %d Merc: %s"%(zoomlevel,merc)
            writeInt(merc[0])
            writeInt(merc[1])
            writeBuf(tile if tile else "")
    writeInt(0x1beef) #Magic to verify writing
    print "Binary hmap download complete"
    return out.getvalue()
    
def android_fplan_map_format(airspaces,points):
    out=StringIO()
    print "Binary download in progress"

    def writeFloat(f):
        out.write(pack(">f",f))
    def writeInt(i):
        out.write(pack(">I",i))
    def writeUTF(s):
        if s==None: s=u""
        try:
            encoded=s.encode('utf8')
        except Exception,cause:
            print "While trying to encode: %s"%(s,)
            raise
        l=len(encoded)
        out.write(pack(">H",l)) #short
        out.write(encoded)
        
    writeInt(0x8A31CDA)
    writeInt(1)
    writeInt(len(airspaces))
    for space in airspaces:
        writeUTF(space['name'])
        writeInt(len(space['points']))
        for point in space['points']:
            lat,lon=point['lat'],point['lon']
            writeFloat(lat)
            writeFloat(lon)
        writeInt(len(space['freqs']))
        for station,freq in space['freqs']:
            writeUTF("%s: %.3f"%(station,freq))
        writeUTF(space['floor'])
        writeUTF(space['ceiling'])
    
    writeInt(len(points))
    for point in points:
        writeUTF(point['name'])
        writeUTF(point['kind'])
        writeFloat(float(point['alt']))
        lat,lon=point['lat'],point['lon']
        writeFloat(lat)
        writeFloat(lon)
        
    ret=out.getvalue()
    assert ret[0]==chr(0x08)
    assert ret[1]==chr(0xA3)
    return ret
    

