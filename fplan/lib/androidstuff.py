from struct import pack
from StringIO import StringIO
import zlib
from fplan.lib.tilegen_worker import get_airspace_color

def android_fplan_bitmap_format(hmap):
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
        assert l<(1<<31)
        out.write(pack(">I",l)) #short
        out.write(encoded)
    
    writeInt(len(hmap)) #zoomlevels    
    for zoomlevel,tiles in hmap.items():
        writeInt(zoomlevel)
        nonemptytiles=[(merc,tile) for (merc,tile) in tiles.items() if tile]
        writeInt(len(nonemptytiles)) #tiles in this zoomlevel
        for merc,tile in nonemptytiles:
            #print "Zoom: %d Merc: %s"%(zoomlevel,merc)
            writeInt(merc[0])
            writeInt(merc[1])
            #assert len(tile)==2*2*64*64
            #print "Tile len is:%d"%(len(tile,))
            writeBuf(tile)
    writeInt(0x1beef) #Magic to verify writing
    out.flush()
    print "Binary hmap download complete"
    return out.getvalue()


    
def android_fplan_map_format(airspaces,points,version):
    versionnum=1
    try:
        versionnum=int(version.strip())
    except:
        pass
    assert versionnum in [0,1,2,3,4]
    out=StringIO()
    print "Binary download in progress"

    def writeFloat(f):
        out.write(pack(">f",f))
    def writeDouble(f):
        out.write(pack(">d",f))
    def writeInt(i):
        out.write(pack(">I",i))
    def writeByte(b):
        if b<0: b=0
        if b>255: b=255
        out.write(pack(">B",b))
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
    writeInt(versionnum)
    writeInt(len(airspaces))
    for space in airspaces:
        writeUTF(space['name'])
        if versionnum>=2:
            (r,g,b,a),dummy_edge_col=get_airspace_color(space['type'])
            writeByte(255*r)
            writeByte(255*g)
            writeByte(255*b)
            writeByte(255*a)
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
        if versionnum>=3:
            if 'adchart_url' in point:
                writeByte(1)
                writeInt(point['adchart_width'])
                writeInt(point['adchart_height'])
                writeUTF(point['adchart_name'])                
                writeUTF(point['adchart_checksum'])
                writeUTF(point['adchart_url'])
                for f in point['adchart_matrix']:
                    if versionnum>=4:
                        writeDouble(f)
                    else:
                        writeFloat(f)
            else:
                writeByte(0)
        
    ret=out.getvalue()
    assert ret[0]==chr(0x08)
    assert ret[1]==chr(0xA3)
    print "binary download complete"
    return ret
    

