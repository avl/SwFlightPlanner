from pyshapemerge2d import Line2,Vertex,Polygon,vvector

def axissorter(startaxis):
    return lambda v:v.x if startaxis==0 else v.y
    
class BspTree(object):
    def __init__(self,points,startaxis=0):
        if len(points)<=0: return
        self.points=list(points)
        self.points.sort(key=axissorter(startaxis))
        self.mididx=len(self.points)/2
        self.pivot=points[mididx]
        if self.mididx>0:
            self.a=BspTree(self.points[:self.mididx],(startaxis+1)%2)
        else:
            self.a=None
        if self.mididx+1<len(self.mididx):
            self.b=BspTree(self.points[self.mididx+1:],(startaxis+1)%2)
        else:
            self.b=None
    def items_whose_dominating_area_overlaps(box):        
        curbox=BoundingBox(-1e30,-1e30,1e30,1e30)
        return items_whose_dominating_area_overlaps_impl(box,curbox)
    def items_whose_dominating_area_overlaps_impl(box,curbox):
        if pivot==None: return []
        if not box.overlaps(curbox): return []
        out=[]
        out.append(pivot)
        left=curbox.clone()
        right=curbox.clone()        
        if axis==0:
            left.x2=pivot.vec().getx()            
            right.x1=pivot.vec().getx()    
        else:
            left.y2=pivot.vec().gety()
            right.y1=pivot.vec().gety()

        if a!=None:
            out.extend(a.items_whose_dominating_area_overlaps_impl(box,left))
        if b!=None:
            out.extend(b.items_whose_dominating_area_overlaps_impl(box,right,out))
        return out

    
    #finds the lowest (furthest from root) item in the 
    #tree whose two belonging sub-boxes taken together
    #completely cover the given box.
    def find_item_dominating(box):
        if pivot==None: return None #no items
        curbox=BoundingBox(-1e30,-1e30,1e30,1e30)
        return find_item_dominating_impl(box,curbox)

    def find_item_dominating_impl(box,curbox):
        if not curbox.covers(box):
            return None
        left=curbox
        right=curbox.clone()
        if axis==0:
            left.x2=pivot.vec().getx()            
            right.x1=pivot.vec().getx()
        else:
            left.y2=pivot.vec().gety()
            right.y1=pivot.vec().gety()    
        leftdom=None
        rightdom=None
        if a!=None: leftdom=a.find_item_dominating_impl(box,left)
        if b!=None: rightdom=b.find_item_dominating_impl(box,left)

        if leftdom!=None: return leftdom
        if rightdom!=None: return rightdom
        return pivot

    def verify(bb):
        if bb==None:
            bb=BoundingBox(-1e30,-1e30,1e30,1e30)
        pivotvec=pivot.vec()
        if not (pivotvec.getx()>=bb.x1-1e-4 and pivotvec.getx()<=bb.x2+1e-4 and
            pivotvec.gety()>=bb.y1-1e-4 and pivotvec.gety()<=bb.y2+1e-4):
            raise Exception("pivotvec %s not within limits %s"%(pivotvec,bb))
        if axis==0:
            bb1=bb.clone()
            bb1.x2=pivotvec.getx()
            bb2=bb.clone()
            bb2.x1=pivotvec.getx()
        else:
            bb1=bb.clone()
            bb1.y2=pivotvec.gety()
            bb2=bb.clone()
            bb2.y1=pivotvec.gety()

        if a!=None: a.verify(bb1)
        if b!=None: b.verify(bb2)
        

    def findall(x1,y1,x2,y2):
        items=[]
        if pivot==None: return [] #no items
        pivotvec=pivot.vec()
        if (pivotvec.getx()>=x1 and pivotvec.getx()<x2 and
            pivotvec.gety()>=y1 and pivotvec.gety()<y2):
            items.add(pivot)

        epsilon=1e-3
        if axis==0:
            pivotval=pivotvec.getx()
            if a!=None:
                if x1-epsilon<=pivotval:
                    a.findall(x1, y1, x2, y2, items);
                else:
                    pass#Log.i("fplan","Ignoring left subtree of pivot "+pivotvec);
            if b!=null:
                if pivotval-epsilon<=x2:
                    b.findall(x1, y1, x2, y2, items);
                else:
                    pass#Log.i("fplan","Ignoring right subtree of pivot "+pivotvec);                    
        else:
            pivotval=pivotvec.gety()
            if a!=null:
                if y1-epsilon<=pivotval:
                    a.findall(x1, y1, x2, y2, items);
                else:
                    pass#Log.i("fplan","Ignoring lower subtree of pivot "+pivotvec);                    
            if b!=null:
                if pivotval-epsilon<=y2:
                    b.findall(x1, y1, x2, y2, items)
                else:
                    pass#Log.i("fplan","Ignoring upper subtree of pivot "+pivotvec);                                        
    def findall(b):
        return findall(b.x1,b.y1,b.x2,b.y2)


