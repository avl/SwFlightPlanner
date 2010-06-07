import os
from struct import pack,unpack
import md5
    
    
class BlobFile(object):
    
    def get_tile_number(self,x,y):
        assert x>=0
        assert y>=0
        tx,ty=(x-self.x1)/self.tilesize,(y-self.y1)/self.tilesize
        return tx,ty
    def __init__(self,name,zoomlevel,x1,y1,x2,y2,mode):
        self.mode=mode
        if mode=="w":
            if os.path.dirname(name).strip() and not os.path.exists(os.path.dirname(name)):
                os.makedirs(os.path.dirname(name))
            if os.path.exists(name):
                self.f=open(name,"r+")
                self.size=os.path.getsize(name)            
            else:            
                self.f=open(name,"w+")
                self.size=0
        else:
            assert mode=="r"
            self.f=open(name,"r")
        print x2,x1
        assert x2>x1
        assert y2>y1
        self.tilesize=256
        self.x1=x1
        self.y1=y1
        self.x2=x2
        self.y2=y2
        self.tx1,self.ty1=self.get_tile_number(x1,y1)
        self.tx2,self.ty2=self.get_tile_number(x2,y2)
        self.sx=self.tx2-self.tx1+1
        self.sy=self.ty2-self.ty1+1
        self.dupmap=dict()
        assert self.sx>0
        assert self.sy>0
        
        if self.size!=0:
            assert self.size>=8*self.sx*self.sy
        else:
            assert len(pack('>I',0))==4
            self.f.write("".join(pack('>I',0) for x in xrange(2*self.sx*self.sy)))
            self.size=8*self.sx*self.sy
    def get_size(self):
        return self.size
    def add_tile(self,x,y,data):
        assert self.mode=="w"
        hash=md5.md5(data).digest()
        p=self.dupmap.get(hash,None)
        if p==None:
            self.f.seek(0,2) #seek to end of file        
            p=self.f.tell()
            print "writing %d bytes to %d"%(len(data),p)
            self.f.write(data)
            self.dupmap[hash]=p
            self.size+=len(data)
        tx,ty=self.get_tile_number(x,y)        
        assert tx>=0 and tx<self.sx
        assert ty>=0 and ty<self.sy
        print "Get tile number for %d,%d  = %d,%d"%(x,y,tx,ty)
        self.f.seek(8*(tx+ty*self.sx))        
        print "Writing %d to off %d"%(p,self.f.tell())
        self.f.write(pack(">I",p))
        self.f.write(pack(">I",len(data)))
    def get_tile(self,x,y):
        tx,ty=self.get_tile_number(x,y)
        self.f.seek(8*(tx+ty*self.sx))
        p=unpack(">I",self.f.read(4))[0]
        s=unpack(">I",self.f.read(4))[0]
        print "Seeking to: ",p
        self.f.seek(p)
        return self.f.read(s)
        
    def close(self):
        self.f.close()
        

def test_blobfile():
    if os.path.exists("test.blob"):
        os.unlink("test.blob")
    b=BlobFile("test.blob",5,0,0,256<<2,256<<2,'w')
    b.add_tile(256,256,"hej")
    b.add_tile(512,256,"svejs")
    b.add_tile(256,256,"da")
    bef=b.get_size()
    b.add_tile(1024,256,"svejs")
    assert b.get_size()==bef
    
    b.add_tile(512,1024,"svejs")
    assert b.get_tile(256,256)=="da"
    print b.get_tile(512,256)
    assert b.get_tile(512,256)=="svejs"
    assert b.get_tile(1024,256)=="svejs"
    assert b.get_tile(512,1024)=="svejs"
