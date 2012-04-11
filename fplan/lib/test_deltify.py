from copy import deepcopy
import deltify
basic=dict(
        airspaces=[dict(pos="59,18",radio=dict(freq=123.4,name="hej")),
                   dict(pos=18,something="whatever")],
        notams=[dict(test="notam 1: banana"),
                dict(test="notam 2: turkey")],
        points=[dict(name="a point"),
                dict(test="another point")]
        )
def helper(A,B):
    userdata=deltify.freeze_top(A)                
    currdata=deltify.freeze_top(B)
    num_diffs,diffs=deltify.deltify_toplevel(userdata,currdata)
    return num_diffs,diffs                
                
def test_simple():
    A=basic
    B=deepcopy(A)
    B['airspaces'].append(dict(pos="59,19",radio=123))
    num_diffs,diffs=helper(A,B)
    assert num_diffs==1
    assert diffs['airspaces'][0]==dict(pos="59,19",radio=123)

def test_simple2():
    A=basic
    B=deepcopy(A)
    B['airspaces'].append(dict(pos=18,something="whatever"))
    num_diffs,diffs=helper(A,B)
    assert num_diffs==0

def test_simple3():
    A=basic
    B=deepcopy(A)
    B['notams']=[dict(test="notam 1: banana")]
    num_diffs,diffs=helper(A,B)
    assert num_diffs==1
    assert diffs['notams'][0]==dict(idx=1,kill=True)
    
def test_simple4():
    A=basic
    B=deepcopy(A)
    B['airspaces'][0]['radio']['freq']=123.3
    num_diffs,diffs=helper(A,B)
    print "Diffs:",diffs
    assert num_diffs==2
    assert diffs['airspaces'][0]['idx']==0
    assert diffs['airspaces'][0]['kill']
    assert dict(diffs['airspaces'][1]['radio'])['freq']==123.3
    
    