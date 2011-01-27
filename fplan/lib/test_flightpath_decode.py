from fplanquick.fplanquick import decode_flightpath
from fplan.lib.recordings import parseRecordedTrip
def test_decode_flightpath_simple1():
    f=open("fplanquick/testdata/simple1.dat")
    print parseRecordedTrip(f)
    """
    Correct gammacoded values in this dat-file:
    Gammacoding: 0
    Gammacoding: 180
    Gammacoding: -50
    """


if __name__=="__main__":
    test_decode_flightpath_simple1()
    
    