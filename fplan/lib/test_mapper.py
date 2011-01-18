from fplan.lib.mapper import *



def test_basic_latlon():
    assert abs(merc2latlon((0,0),0)[0]-85.05113)<1e-7
    assert abs(merc2latlon((0,256),0)[0]--85.05113)<1e-7
    assert abs(merc2latlon((0,0),2)[0]-85.05113)<1e-7
    assert abs(merc2latlon((0,256<<2),2)[0]--85.05113)<1e-7

def test_parse_coord():
    c,=parsecoords("590000N0180000E")
    assert from_str(c)[0]==59
    assert from_str(c)[1]==18
    c,=parsecoords("590000.999999999999N0180000E")
    assert abs(from_str(c)[0]-(59+1/3600.0))<1e-6
    assert from_str(c)[1]==18

    c,=parsecoords("590000.5N0180000.5E")
    assert abs(from_str(c)[0]-(59+0.5/3600.0))<1e-6
    assert abs(from_str(c)[1]-(18+0.5/3600.0))<1e-6
    c,=parsecoords("5900.5N01800.5E")
    assert abs(from_str(c)[0]-(59+0.5/60.0))<1e-6
    assert abs(from_str(c)[1]-(18+0.5/60.0))<1e-6

    c,=parsecoords("5900.5N01800.5W")
    print c
    assert abs(from_str(c)[0]-(59+0.5/60.0))<1e-6
    assert abs(from_str(c)[1]--(18+0.5/60.0))<1e-6

    c,=parsecoords("590000N 0180000E")
    assert from_str(c)[0]==59
    assert from_str(c)[1]==18
    
    c,=parsecoords("590000,00N 0180000,00E")
    assert from_str(c)[0]==59
    assert from_str(c)[1]==18
    
    c,=parsecoords("590000,0N 0180000,0E")
    assert from_str(c)[0]==59
    assert from_str(c)[1]==18
    
