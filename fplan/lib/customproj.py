import numpy
import numpy.linalg as linalg

class Transform():
    def __init__(self,A,T):
        if type(A) in (tuple,list):
            A=numpy.matrix([
                            [A[0],A[2]],
                            [A[1],A[3]]
                          ])
            T=numpy.matrix([[T[0]],[T[1]]])
        self.T=T
        self.A=A
        self.Ai=linalg.inv(A)
    def inverse_matrix(self):
        return self.Ai    
    def to_pixels(self,pos):    
        r=self.Ai*(numpy.matrix(pos).transpose()-self.T)
        return r[0,0],r[1,0]
    def to_latlon(self,pixels):
        r=self.A*(numpy.matrix(pixels).transpose())+self.T        
        return r[0,0],r[1,0]        
        
def solve(markers):
    B=[] #lon
    Bh=[]
    A=[] #lat
    Ah=[]
    for mark in markers:
        if mark.longitude:
            assert type(mark.longitude) in [float,int]
            w=1.0
            if mark.weight:
                w=mark.weight
            print "Weight",w
            B.append((w*mark.x,w*mark.y,w*1))
            Bh.append([w*float(mark.longitude)])
        if mark.latitude:
            assert type(mark.latitude) in [float,int]
            w=1.0
            if mark.weight:
                w=mark.weight
            print "Weight",w
            A.append((w*mark.x,w*mark.y,w*1))
            Ah.append([w*float(mark.latitude)])
    res=solve_and_check_impl(A,Ah,B,Bh)
    error,mA,T=res    
    
    print "Error:",error
    
    rot,mov=[mA[0,0],mA[1,0],mA[0,1],mA[1,1]],[T[0,0],T[1,0]]
    tr=Transform(rot,mov)
    return error,rot,mov
    #Ai*(numpy.matrix(arppos).transpose()-T)        
    
def solve_and_check_impl(A,Ah,B,Bh):
    Am=numpy.matrix(A)
    Amh=numpy.matrix(Ah)
    Bm=numpy.matrix(B)
    Bmh=numpy.matrix(Bh)
    Ar,Aresidue=linalg.lstsq(Am,Amh)[0:2]
    Br,Bresidue=linalg.lstsq(Bm,Bmh)[0:2]
    A11,A12,Tx=Ar.transpose()[0].tolist()[0]
    A21,A22,Ty=Br.transpose()[0].tolist()[0]
    mA=numpy.matrix([[A11,A12],[A21,A22]])
    T=numpy.matrix([[Tx],[Ty]])
    print "Determinant:",linalg.det(mA)
    error=0
    for m,mh in zip(A,Ah):
        #print "m:",m,"mh:",mh        
        x,y,one=m
        deg=mh[0]
        X=numpy.matrix([[x],[y]])        
        Y=mA*X+T
        lat,lon=Y[0,0],Y[1,0]
        #print "Mapped lat",lat,"correct",deg
        error=max(error,(deg-lat))
    for m,mh in zip(B,Bh):
        #print "m:",m,"mh:",mh        
        x,y,one=m
        deg=mh[0]
        X=numpy.matrix([[x],[y]])        
        Y=mA*X+T
        lat,lon=Y[0,0],Y[1,0]
        #print "Mapped lon",lon,"correct",deg
        error=max(error,(deg-lon))
    Ai=linalg.inv(mA)
        
    return error,mA,T
