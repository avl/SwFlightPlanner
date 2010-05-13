import shapelib
import dbflib
import mapnik
import fplan.lib.mapper as mapper 

prj = mapnik.Projection("+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +no_defs +over")


def run():
    sf=shapelib.open("/home/anders/saker/avl_fplan_world/mapnik_render/world_boundaries/world_boundaries_m.shp")
    d=dbflib.DBFFile("/home/anders/saker/avl_fplan_world/mapnik_render/world_boundaries/world_boundaries_m.dbf")
    num_shapes=sf.info()[0]
    assert num_shapes==d.record_count()
    swedish_polygons=0
    for idx in xrange(num_shapes):
        obj=sf.read_object(idx)
        rec=d.read_record(idx)
        if rec['CNTRY_NAME']=='Sweden':
            #print "Sweden: ",obj.vertices()
            swedish_polygons+=1
            assert len(obj.vertices())==1
            out=[]
            for vert in obj.vertices()[0]:                
                cd=prj.inverse(mapnik.Coord(vert[1],vert[0]))
                #print "lat: %s, lon: %s,"%(cd.y,cd.x)
                out.append(mapper.format_lfv(cd.y,cd.x))
            
            print "Swedpol:", " - ".join(out)
    print "Swedish polygons: %d"%(swedish_polygons,)
if __name__=='__main__':
    run()
    