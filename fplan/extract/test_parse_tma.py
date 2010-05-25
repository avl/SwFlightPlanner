from fplan.extract.parse_tma import *


def test_parse_dist():
    assert parse_dist("1 NM")==1.0
    assert parse_dist("1852 NM")==1852.0    
    assert parse_dist("1852 m")==1.0
    assert parse_dist("926 m")==0.5

def test_create_seg_sequence():
    segs=create_seg_sequence("58,18","59,18","60,18",10.0)
    h=len(segs)/2
    assert segs[h][1]<18.0
    assert segs[h][0]>58.5
    assert segs[h][0]<59.5
       
def test_create_seg_sequence1():
    segs=create_seg_sequence("58,18","59,0","58,18",10.0)
    assert len(segs)==0


def test_parse_area_seg():
    prev="58,18"
    next="59,0"
    dist="10 NM"
    seg="clockwise along an arc centred on 550404N0144448E and with radius 16.2 NM"

    segs=parse_area_segement(seg,prev,next)
    print segs
    
    
    
    