from copy import copy
class BoundingBox(object):
    def __init__(self,x1,y1,x2,y2):
        self.x1=x1
        self.y1=y1
        self.x2=x2
        self.y2=y2
    def __repr__(self):
        return "BoundingBox(%s,%s,%s,%s)"%(
            self.x1,self.y1,self.x2,self.y2)
    def covers(self,other):
        if (self.x1<=other.x1 and self.x2>=other.x2 and
            self.y1<=other.y1 and self.y2>=other.y2):
            return True
        return False
    def overlaps(self,other):
        if (self.x1<=other.x2 and self.x2>=other.x1 and
            self.y1<=other.y2 and self.y2>=other.y1):
            return True
        return False
    def expanded(self,h):
        return BoundingBox(self.x1-h,self.y1-h,self.x2+h,self.y2+h)
    
def bb_from_mercs(ms):
    x1=1e30
    x2=-1e30
    y1=1e30
    y2=-1e30
    for m in ms:
        x1=min(m[0],x1) 
        x2=max(m[0],x2) 
        y1=min(m[1],y1) 
        y2=max(m[1],y2) 
    return BoundingBox(x1,y1,x2,y2)
def axissorter(startaxis):
    return lambda v:(v.vec[0] if startaxis==0 else v.vec[1])
    
class BspTree(object):
    class Item(object):
        def __init__(self,key,val):
            self.vec=key
            self.val=val
        def __repr__(self):
            return "Item(%s,%s)"%(self.vec,self.val)
    def getall(self):        
        if self.pivot==None:
            assert self.a==None and self.b==None
            return []
        else:
            cnt=[self.pivot.val]
            if self.a:
                cnt+=self.a.getall()
            if self.b:
                cnt+=self.b.getall()
            return cnt
            
    def __init__(self,points,startaxis=0,rec=0):
        #print "BspTtree",rec,id(self)
        self.pivot=None
        if len(points)==0:
            self.pivot=None
            return
        assert len(points)>0
        #if len(points)<=0: return


        points.sort(key=axissorter(startaxis))
        self.mididx=int(len(points)//2)
        self.pivot=points[self.mididx]

        assert self.pivot
        self.axis=startaxis    
        if len(points)==1:
            self.a=self.b=None
            return
        if self.mididx>0:
            self.a=BspTree(points[:self.mididx],(startaxis+1)%2,rec+1)
        else:
            self.a=None
        if self.mididx+1<len(points):
            self.b=BspTree(points[self.mididx+1:],(startaxis+1)%2,rec+1)
        else:
            self.b=None
        assert self.a or self.b
        
        
    def items_whose_dominating_area_overlaps(self,box):        
        curbox=BoundingBox(-1e30,-1e30,1e30,1e30)
        return self.items_whose_dominating_area_overlaps_impl(box,curbox)
    def items_whose_dominating_area_overlaps_impl(self,box,curbox):
        if self.pivot==None: return []
        if not box.overlaps(curbox): return []
        out=[]
        out.append(self.pivot)
        left=copy(curbox)
        right=copy(curbox)        
        if self.axis==0:
            left.x2=self.pivot.vec[0]            
            right.x1=self.pivot.vec[0]    
        else:
            left.y2=self.pivot.vec[1]
            right.y1=self.pivot.vec[1]

        if self.a!=None:
            out.extend(self.a.items_whose_dominating_area_overlaps_impl(box,left))
        if self.b!=None:
            out.extend(self.b.items_whose_dominating_area_overlaps_impl(box,right))
        return out

    
    #finds the lowest (furthest from root) item in the 
    #tree whose two belonging sub-boxes taken together
    #completely cover the given box.
    def find_item_dominating(self,box):
        if self.pivot==None: return None #no items
        curbox=BoundingBox(-1e30,-1e30,1e30,1e30)
        return self.find_item_dominating_impl(box,curbox)

    def find_item_dominating_impl(self,box,curbox):
        if self.pivot==None: return None #no items
        if not curbox.covers(box):
            return None
        left=curbox
        right=copy(curbox)
        if self.axis==0:
            left.x2=self.pivot.vec[0]            
            right.x1=self.pivot.vec[0]
        else:
            left.y2=self.pivot.vec[1]
            right.y1=self.pivot.vec[1]    
        leftdom=None
        rightdom=None
        if self.a!=None: leftdom=self.a.find_item_dominating_impl(box,left)
        if self.b!=None: rightdom=self.b.find_item_dominating_impl(box,left)

        if leftdom!=None: return leftdom
        if rightdom!=None: return rightdom
        return self.pivot

    def verify(self,bb):
        if bb==None:
            bb=BoundingBox(-1e30,-1e30,1e30,1e30)
        pivotvec=self.pivot.vec
        if not (pivotvec[0]>=bb.x1-1e-4 and pivotvec[0]<=bb.x2+1e-4 and
            pivotvec[1]>=bb.y1-1e-4 and pivotvec[1]<=bb.y2+1e-4):
            raise Exception("pivotvec %s not within limits %s"%(pivotvec,bb))
        if self.axis==0:
            bb1=bb.clone()
            bb1.x2=pivotvec[0]
            bb2=bb.clone()
            bb2.x1=pivotvec[0]
        else:
            bb1=bb.clone()
            bb1.y2=pivotvec[1]
            bb2=bb.clone()
            bb2.y1=pivotvec[1]

        if self.a!=None: self.a.verify(bb1)
        if self.b!=None: self.b.verify(bb2)
        

    def findall(self,x1,y1,x2,y2,items):
        assert self.pivot!=None
        #if self.pivot==None: return  #no items

        pivotvec=self.pivot.vec

        if (pivotvec[0]>=x1 and pivotvec[0]<x2 and
            pivotvec[1]>=y1 and pivotvec[1]<y2):
            items.append(self.pivot)
            
        epsilon=1e-3
        if self.axis==0:
            pivotval=pivotvec[0]
            if self.a!=None:
                if x1-epsilon<=pivotval:
                    self.a.findall(x1, y1, x2, y2, items);
                else:
                    pass#Log.i("fplan","Ignoring left subtree of pivot "+pivotvec);
            if self.b!=None:
                if pivotval-epsilon<=x2:
                    self.b.findall(x1, y1, x2, y2, items);
                else:
                    pass#Log.i("fplan","Ignoring right subtree of pivot "+pivotvec);                    
        else:
            pivotval=pivotvec[1]
            if self.a!=None:
                if y1-epsilon<=pivotval:
                    self.a.findall(x1, y1, x2, y2, items);
                else:
                    pass#Log.i("fplan","Ignoring lower subtree of pivot "+pivotvec);                    
            if self.b!=None:
                if pivotval-epsilon<=y2:
                    self.b.findall(x1, y1, x2, y2, items)
                else:
                    pass#Log.i("fplan","Ignoring upper subtree of pivot "+pivotvec);                                        
        return    
    def findall_in_bb(self,b):
        if self.pivot==None: return []  #no items
        items=[]
        self.findall(b.x1,b.y1,b.x2,b.y2,items)
        return items
def selftest():
    def zp(xs):
        return [BspTree.Item(x,None) for x in xs]
    bsp=BspTree(zp([(0,0),(10,0),(10,10),(20,0),(30,10)]))
    items=[]
    bsp.findall(15,-5,25,5,items)
    print "Items:",items

    

if __name__=='__main__':
    selftest()

