from fplan.lib.mapper import *
import mapper


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
    
def test_parse_all_alts():
    def check(what,exp):
        got=list(mapper.parse_all_alts(what))
        if got != exp:
            raise Exception("Error, expected: %s, got %s"%(exp,got))
    check('1600 ft',[(1600,'msl')])
    check('FL150',[(150,'fl')])
    check('1400 ft GND',[(1400,'gnd')])
    check('1400 GND',[(1400,'gnd')])
    check('1300 ft AMSL',[(1300,'msl')])
    check('1000 ft/300 m GND',[(1000,'gnd')])
    check(' GND',[(0,'gnd')])
    check('  GND',[(0,'gnd')])
    check('asdfasdf GND',[(0,'gnd')])
    check('1000 ft/300 m GND aksdjf GND',[(1000,'gnd'),(0,'gnd')])
    check('1200 1500 GND 1000 ft/300 m GND aksdjf FL075',[(1200,'msl'),(1500,'gnd'),(1000,'gnd'),(75,'fl')])
    
    
    
        