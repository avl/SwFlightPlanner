from fplanquick.fplanquick import decode_flightpath
from fplan.lib.recordings import parseRecordedTrip
def test_decode_flightpath_simple1():
    f=open("fplanquick/testdata/simple1.dat")
    print parseRecordedTrip(None,f)
    """
    Correct gammacoded values in this dat-file:
    Gammacoding: 0
    Gammacoding: 180
    Gammacoding: -50
    """
def test_decode_flightpath_simple2():
    f=open("fplanquick/testdata/simple2.dat")
    print parseRecordedTrip(None,f)
def test_decode_flightpath_long3():
    for i in xrange(3):
        f=open("fplanquick/testdata/long%d.dat"%(i+1,))
        d=parseRecordedTrip(None,f)
        


if __name__=="__main__":
    test_decode_flightpath_simple1()
    test_decode_flightpath_simple2()
    test_decode_flightpath_long3()
    
    