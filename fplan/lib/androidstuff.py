from struct import pack
from StringIO import StringIO
import traceback
import mapper
import zlib
from fplan.lib.tilegen_worker import get_airspace_color
from deltify import deltify
import helpers
import fplan.extract.aip_text_documents as aip_text_documents 

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


    
def android_fplan_map_format(airspaces,points,aiptexts,trips,version,user_aipgen,correct_pass):
    
    assert type(aiptexts)==list
    print "fplan_map_format, version: ",version,"aipgen",user_aipgen,"corr pass",correct_pass
    versionnum=1
    
    
    #airspaces=airspaces[:10]    
    #points=points[:10]#[x for x in points if not x['name'].upper().count("G")]
    #trips=trips[:10]
    #aiptexts=aiptexts[:10]
    try:
        versionnum=int(version.strip())
    except Exception:
        pass
    assert versionnum>=1 and versionnum<=9
    out=StringIO()
    print "Binary download in progress"

    def writeFloat(f):
        out.write(pack(">f",f))
    def writeDouble(f):
        out.write(pack(">d",f))
    def writeInt(i):
        out.write(pack(">I",i))
    def writeLong(i):
        out.write(pack(">Q",i))
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
    def writeBlob(b):
        assert type(b)==str and type(b)!=unicode
        writeInt(len(b))
        out.write(b)
        
    writeInt(0x8A31CDA)
    
    if versionnum>=5:        
        #print "User aipgen",user_aipgen
        #print "AIptexts",type(aiptexts),repr(aiptexts)
        try:
            clearall,new_aipgen,data,new_namechecksum=deltify(user_aipgen,
                    dict(airspaces=airspaces,points=points,aiptexts=aiptexts,trips=trips))
            print "clearall",clearall,"new_namechecksum;",new_namechecksum
            airspaces=data['airspaces']
            points=data['points']
            aiptexts=data['aiptexts']
            trips=data['trips']
        except Exception:
            print traceback.format_exc()
            
        
    
    writeInt(versionnum)
    
    if versionnum>=7:
        print "Writing corr pass",correct_pass
        writeByte(1 if correct_pass else 0)
        
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
                #print "Killing space index",space['idx']
                writeByte(0)
                writeInt(space['idx'])
                continue
            writeByte(1)
        #print "Sending space",space['name']
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
                #print "Killing points index",point['idx']
                writeByte(0)
                writeInt(point['idx'])
                continue
            writeByte(1)
        #print "Sending point",point['name']
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
            """
            Format is: (key
            [{'ends': [{'pos': '61.8552555556,24.7619638889', 'thr': u'08'},
    {'pos': '61.8568416667,24.8112611111', 'thr': u'26'}]}
            """
            if versionnum>=7:
                runways=point.get('runways',[])
                writeByte(len(runways))
                #if runways: print "Writing runways,",runways
                for runway in runways:     
                    runway=dict(runway)               
                    for end in runway['ends']:
                        end=dict(end)
                        writeUTF(end['thr'])
                        lat,lon=mapper.from_str(end['pos'])
                        writeFloat(lat)
                        writeFloat(lon)
                    if versionnum>=9:
                        if runway.get('surface',''):
                            writeByte(1)
                            writeUTF(runway.get('surface',''))
                        else:
                            writeByte(0)
                            
            if versionnum>=9:
                if point.get('remark',''):
                    writeByte(1)
                    writeUTF(point['remark'])
                else:
                    writeByte(0)
                    
                
            
        writeFloat(float(point['alt']))
        lat,lon=point['lat'],point['lon']
        writeFloat(lat)
        writeFloat(lon)
        if versionnum>=3 and versionnum<=5:
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
                
                
    if versionnum>=6:
        writeInt(len(aiptexts))
        print "Writing",len(aiptexts),"aiptexts"
        for aipd in aiptexts:
            if 'kill' in aipd:
                print "Killing aip index",aipd['idx']
                writeByte(0)
                writeInt(aipd['idx'])
                continue
            aip=dict(aipd['data']) 
            print "Sending aiptext",aipd['icao'],aip['category']
            writeByte(1)
            writeUTF(aipd['icao'])
            writeUTF(aipd['name'])
            writeUTF(aip['category'])
            writeUTF(aip['checksum'])
            writeLong(helpers.utcdatetime2stamp_inexact(aip['date']))            
            doc=aip_text_documents.get_doc(aip['icao'],aip['category'],aip['checksum'])
            writeByte(1) #Contains doc blob
            writeBlob(doc)
    if versionnum>=7:
        writeInt(len(trips))
        
        for trip in trips:
            if 'kill' in trip:
                print "Killing trip index",trip['idx']
                writeByte(0)
                writeInt(trip['idx'])
                continue
            writeByte(1)
            writeUTF(trip['name'])
            if versionnum>=8:
                writeUTF(trip['aircraft'])
                writeUTF(trip['atsradiotype'])

            writeInt(len(trip['waypoints']))
            for way in trip['waypoints']:
                way=dict(way)
                writeInt(0xbeef)
                writeUTF(way['name'])
                writeFloat(way['lat'])
                writeFloat(way['lon'])
                writeUTF(way['altitude'])
                writeFloat(way['startalt'])
                writeFloat(way['endalt'])
                writeFloat(way['winddir'])
                writeFloat(way['windvel'])
                writeFloat(way['gs'])
                writeUTF(way['what'])
                writeUTF(way['legpart'])
                writeFloat(way['d'])
                writeFloat(way['tas'])
                writeByte(1 if way['land_at_end'] else 0)
                writeFloat(way['endfuel'])
                writeFloat(way['fuelburn'])
                #print "The depart_dt which was suspicous is onw",way['depart_dt'],"represented as",helpers.utcdatetime2stamp_inexact(way['depart_dt'])
                writeLong(helpers.utcdatetime2stamp_inexact(way['depart_dt']))
                writeLong(helpers.utcdatetime2stamp_inexact(way['arrive_dt']))
                writeByte(way['lastsub'])
                
    
    if versionnum>=5:
        print "New namechecksum;",new_namechecksum
        writeInt(0x1eedbaa5)
        writeUTF(new_namechecksum)
            
        
    ret=out.getvalue()
    assert ret[0]==chr(0x08)
    assert ret[1]==chr(0xA3)
    print "binary download complete"
    return ret
    

