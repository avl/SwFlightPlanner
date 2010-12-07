from bsptree import BspTree,BoundingBox


class BBTree(object):
    class TItem(object):
        def __init__(self,bb,payload):
            self.bb=bb
            self.payload=payload
        def __repr__(self):
            return "TItem(%s,%s)"%(self.bb,self.payload)
    class Adapter(object):
        def __init__(self,vec):
            self.vec=vec
            self.val=[]
          
    def overlapping(self,box):
        result=[]
        for bspitem in self.bsp.items_whose_dominating_area_overlaps(box):
            for item in bspitem.val:
                if item.bb.overlaps(box):
                    result.append(item)
        return result
    def __init__(self,items,epsilon):
        itarr=[]
        for item in items:
            bb=item.bb
            itarr.append(BBTree.Adapter((bb.x1,bb.y1)))
            itarr.append(BBTree.Adapter((bb.x2,bb.y2)))
        self.bsp=BspTree(itarr)
        for item in items:
            bb=item.bb.expanded(epsilon)
            dom=self.bsp.find_item_dominating(bb)
            dom.val.append(item)

def selftest():
    Item=BBTree.TItem
    items=[Item(BoundingBox(0,0,1,1),'one'),
           Item(BoundingBox(2,0,3,1),'two'),
           Item(BoundingBox(4,4,20,20),'three')
           ]
    bbt=BBTree(items,0.1)
    assert set([x.payload for x in bbt.overlapping(BoundingBox(0,0,1,1))])==\
        set(['one'])
    assert set([x.payload for x in bbt.overlapping(BoundingBox(-1,-1,10,10))])==\
        set(['one','two','three'])
    assert set([x.payload for x in bbt.overlapping(BoundingBox(19,19,30,30))])==\
        set(['three'])
    print bbt.overlapping(BoundingBox(2,0,3,1))
if __name__=='__main__':
    selftest()
    