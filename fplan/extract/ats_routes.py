import math
import fplan.lib.mapper as mapper


def rotL(p):
    x,y=p
    return (-y,x)
def rotR(p):
    x,y=p
    return (y,-x)
def add(a,b):
    return (a[0]+b[0],a[1]+b[1])    
def sub(a,b):
    return (a[0]-b[0],a[1]-b[1])    
def scalar(a,b):
    return a[0]*b[0]+a[1]*b[1]
def mul(k,a):
    return (k*a[0],k*a[1])
def norm(a):
    return math.sqrt(a[0]**2+a[1]**2)    
def normalize(a):
    dlen=norm(a)
    if abs(dlen)<1e-6: raise Exception("Attempt to normalize zero-vector")
    return mul(1.0/dlen,a)

def get_merc_outline(coords,width):
    left=[]
    right=[]
    print("Coords:\n<%s>\n, width: <%s>"%(coords,width))
    for idx in xrange(len(coords)):
        here=coords[idx]
        mid=True
        if idx==0:
            prev=coords[idx]
            mid=False
        else:
            prev=coords[idx-1]
        if idx==len(coords)-1:
            next=coords[idx]
            mid=False
        else:
            next=coords[idx+1]
        d=(float(next[0]-prev[0]),float(next[1]-prev[1]))
        enwiden=1.0
        if mid:
            d1=normalize(sub(here,prev))
            d2=normalize(sub(next,here))
            s=scalar(d1,d2)
            if s<=-1.0: s=-1.0
            if s>=1.0: s=1.0
            a=math.acos(s)
            if abs(a)>45.0/(180.0/math.pi): 
                raise Exception("ATS route turns too sharply, at index: %d"%(idx,))
            enwiden=1.0/math.cos(a)
        twidth=width*enwiden
        d=normalize(d)
        left.append(add(here,mul(0.5*twidth,rotL(d))))
        right.append(add(here,mul(0.5*twidth,rotR(d))))
    return right+list(reversed(left))

def get_latlon_outline(latlonseq,width_nm):
    print "Width nm:",width_nm
    mercseq=[mapper.latlon2merc(mapper.from_str(ll),13) for ll in latlonseq]
    width=float(mapper.approx_scale(mercseq[0],13,width_nm))    
    
    mercout=get_merc_outline(mercseq,width)
    
    points=[mapper.to_str(mapper.merc2latlon(x,13)) for x in mercout]
    return points    
