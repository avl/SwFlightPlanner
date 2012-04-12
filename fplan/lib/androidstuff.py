from struct import pack
from StringIO import StringIO
import zlib
from fplan.lib.tilegen_worker import get_airspace_color
from deltify import deltify

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


    
def android_fplan_map_format(airspaces,points,version,user_aipgen):
    print "fplan_map_format, version: ",version,"aipgen",user_aipgen
    versionnum=1
    
    airspaces=airspaces    
    points=points#[x for x in points if not x['name'].upper().count("G")]
    try:
        versionnum=int(version.strip())
    except:
        pass
    assert versionnum in [0,1,2,3,4,5]
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
    
    if versionnum>=5:
        print "User aipgen",user_aipgen
        clearall,new_aipgen,data,new_namechecksum=deltify(user_aipgen,
                dict(airspaces=airspaces,points=points))
        print "clearall",clearall,"new_namechecksum;",new_namechecksum
        airspaces=data['airspaces']
        points=data['points']
        
    
    writeInt(versionnum)
    
        
    if versionnum>=5:
        print "Wrote aipgen:",new_aipgen
        writeUTF(new_aipgen)
        if clearall:
            writeByte(1)
        else:
            writeByte(0)
    
    writeInt(len(airspaces))
    for space in airspaces:
        if versionnum>=5:
            if 'kill' in space:
                print "Killing space index",space['idx']
                writeByte(0)
                writeInt(space['idx'])
                continue
            writeByte(1)
        print "Sending space",space['name']
        writeUTF(space['name'])
        if versionnum>=2:
            (r,g,b,a),dummy_edge_col=get_airspace_color(space['type'])
            writeByte(255*r)
            writeByte(255*g)
            writeByte(255*b)
            writeByte(255*a)
        writeInt(len(space['points']))
        for point in space['points']:
            point=dict(point)
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
        if versionnum>=5:
            if 'kill' in point:
                print "Killing points index",point['idx']
                writeByte(0)
                writeInt(point['idx'])
                continue
            writeByte(1)
        print "Sending point",point['name']
        writeUTF(point['name'])
        writeUTF(point['kind'])
        if versionnum>=5:
            if point.get('notams',[]):
                notams=point['notams']
                writeInt(len(notams))
                for notam in notams:
                    writeUTF(notam)
            else:
                writeInt(0)
            if point.get('icao',None):
                writeByte(1)
                writeUTF(point['icao'])
            else:
                writeByte(0)
            if point.get('taf',None):
                writeByte(1)
                writeUTF(point['taf'])
            else:
                writeByte(0)
            if point.get('metar',None):
                writeByte(1)
                writeUTF(point['metar'])
            else:
                writeByte(0)
                
            
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
    if versionnum>=5:
        print "New namechecksum;",new_namechecksum
        writeInt(0x1eedbaa5)
        writeUTF(new_namechecksum)
            
        
    ret=out.getvalue()
    assert ret[0]==chr(0x08)
    assert ret[1]==chr(0xA3)
    print "binary download complete"
    return ret
    

