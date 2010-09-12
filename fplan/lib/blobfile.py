import os
from struct import pack,unpack
import md5
import sys    
from threading import Lock
import threading
import time
import stat
    
class BlobFile(object):
    
    def get_tile_number(self,x,y):
        assert x>=0
        assert y>=0
        tx,ty=(x-self.x1)/self.tilesize,(y-self.y1)/self.tilesize
        return tx,ty
    def __init__(self,name,zoomlevel=None,x1=None,y1=None,x2=None,y2=None,mode='r'):
        self.tilesize=256
        self.lock=Lock()
        self.threads_reading=0
        assert mode in ["r","w"]
        print "Init Blob: name=%s, zoom=%s, %s,%s-%s,%s, %s"%(
            name,zoomlevel,x1,y1,x2,y2,mode)
        self.mode=mode
        if mode=="w":
            if os.path.dirname(name).strip() and not os.path.exists(os.path.dirname(name)):
                os.makedirs(os.path.dirname(name))
            if os.path.exists(name):
                print "File %s already existed"%(name,)
                self.f=open(name,"r+")
                self.size=os.path.getsize(name)            
            else:            
                print "File did not exist"
                self.f=open(name,"w+")
                assert os.path.getsize(name)==0 
                self.size=0
            print "Opened %s for writing"%(name,)
            self.name=name
            self.x1=x1
            self.y1=y1
            self.x2=x2
            self.y2=y2
            self.zoomlevel=zoomlevel
        else:
            assert mode=="r"
            self.name=name
            f=open(name,"r")
            self.tls=threading.local()
            self.size=os.path.getsize(name)
            params=[]
            buf=f.read(5*4)
            for i in xrange(5):
                params.append(unpack('>I',buf[4*i:4*i+4])[0])
            assert x1==x2==y1==y2==zoomlevel==None
            #print "unpaked:",params
            self.x1,self.y1,self.x2,self.y2,self.zoomlevel=params
            x1=self.x1
            y1=self.y1
            x2=self.x2
            y2=self.y2
            zoomlevel=self.zoomlevel
 
        #print x2,x1
        assert x2>x1
        assert y2>y1
        self.tx1,self.ty1=self.get_tile_number(x1,y1)
        self.tx2,self.ty2=self.get_tile_number(x2,y2)
        self.sx=self.tx2-self.tx1+1
        self.sy=self.ty2-self.ty1+1
        #print "Tilecount for zoomlevel %d: %d"%(zoomlevel,self.sx*self.sy)
        self.dupmap=dict()
        assert self.sx>0
        assert self.sy>0
        #print "File size: %d"%(self.size,)
        if self.size!=0:
            assert self.size>=4*self.sx*self.sy+4*5
        else:
            assert mode=='w'
            assert len(pack('>I',0))==4
            numwords=self.sx*self.sy
            print "Writing %d words to file %s"%(numwords,name)
            self.f.write("".join(pack('>I',param) for param in [self.x1,self.y1,self.x2,self.y2,self.zoomlevel]))
            self.size+=4*5
            self.size+=4*numwords
            while numwords>0:
                towrite=numwords
                if towrite>4096:
                    towrite=4096
                self.f.write("".join(pack('>I',0) for x in xrange(towrite)))
                numwords-=towrite
            self.f.flush()
    def get_size(self):
        return self.size
    def add_tile(self,x,y,data):
        """Threadsafe"""
        self.lock.acquire()
        try:
            assert self.mode=="w"
            tx,ty=self.get_tile_number(x,y)        
            if not ( tx>=0 and tx<self.sx) or not (ty>=0 and ty<self.sy):
                print "Not adding tile at %d,%d, since it is outside the range of %d,%d-%d,%d"%(tx,ty,0,0,self.sx,self.sy)
                return
            hash=md5.md5(data).digest()
            p=self.dupmap.get(hash,None)
            if p==None:
                self.f.seek(0,2) #seek to end of file        
                p=self.f.tell()
                print "writing %d bytes to %d (coords: %d,%d zoom: %d)"%(len(data),p,x,y,self.zoomlevel)
                self.f.write(pack(">I",len(data)))
                self.f.write(data)
                self.f.flush()
                self.dupmap[hash]=p
                self.size+=len(data)
            else:
                print "Using cached value for:",x,y,'zoom:',self.zoomlevel
            #print "Get tile number for %d,%d  = %d,%d"%(x,y,tx,ty)
            self.f.seek(20+4*(tx+ty*self.sx))        
            self.f.write(pack(">I",p))
            self.f.flush()
            #self.f.write(pack(">I",len(data)))
        finally:
            self.lock.release()
        if 1:
            #extra checks
            print "Written file to %d,%d,%d, now checking"%(x,y,self.zoomlevel)
            assert self.get_tile(x,y)==data
            openinode=os.fstat(self.f.fileno())[stat.ST_INO]            
            ondiskinode=os.stat(self.name)[stat.ST_INO]
            print "Inode on disk: %s, inode open for output: %s"%(ondiskinode,openinode)
            assert openinode==ondiskinode
            
        print "Ok  %d,%d,%d"%(x,y,self.zoomlevel)
            
    def get_tile(self,x,y):
        """Threadsafe"""
        
        if self.mode!="r":        
            self.lock.acquire()
            f=self.f
        else:
            if hasattr(self.tls,'f'):
                f=self.tls.f
                assert f!=None
            else:
                #print "Opening file %s for thread %s"%(self.name,threading.current_thread())
                f=open(self.name,"r")
                self.tls.f=f
        self.threads_reading+=1  
        try:
            tx,ty=self.get_tile_number(x,y)
            if tx<0 or tx>=self.sx or ty<0 or ty>=self.sy:
                return None
            pos=20+4*(tx+ty*self.sx)
            #print "Seeking to pos %d in file of size %d"%(pos,self.size)
            f.seek(pos)
            t=f.read(4)
            if len(t)!=4:
                print "Blob not initialized correctly (%d,%d,%d)"%(x,y,self.zoomlevel)
                return None
            p=unpack(">I",t)[0]
            #print "Tile number coords: %d,%d = %d"%(tx,ty,p)
            if p==0:
                print "No tile at position %d,%d, zoomlevel %d"%(x,y,self.zoomlevel)
                return None
            f.seek(p)
            sbuf=f.read(4)
            if len(sbuf)!=4:
                print "Couldn't read tile %d,%d at zoomlevel %d. Offset: %d, filesize: %d (x:%d,y:%d,sx:%d sy:%d)"%(x,y,self.zoomlevel,p,self.size,tx,ty,self.sx,self.sy)
                return None
            s=unpack(">I",sbuf)[0]
            #print "Read offset: %d"%(s,)
            if s>self.size:
                print "Offset too large. Offset: %d, filesize: %d (%d,%d,%d)"%(s,self.size,x,y,self.zoomlevel)
                return None
            if p==0 or s==0:
                print "Zero size image at %d,%d, zoomlevel %d"%(x,y,self.zoomlevel)
                return None
            assert s>0
            #print "Threads reading simultaneously: %d"%(self.threads_reading,)
            png=f.read(s)
            #print "Successfully read %d byte png"%(len(png),)
            return png
        except Exception,cause:
            print "Error reading from blob: %d,%d,%d"%(x,y,self.zoomlevel)
            raise
        finally:
            self.threads_reading-=1  
            if self.mode!="r":
                self.lock.release()
            
        
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
    
if __name__=="__main__":
     b=BlobFile(sys.argv[1])
     t=b.get_tile(int(sys.argv[2]),int(sys.argv[3]))
     w=open(sys.argv[4],"w")
     w.write(t)
     w.close()
     
     
     
