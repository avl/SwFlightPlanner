from math import sqrt

worldsize=2000e3 #3000km
playbox=150e3 #150km

route=1300e3 #1800km
crossroute=25e3 #km
tricount=10000
boxcount=5000
boxside=int(sqrt(boxcount))
hgtres=250

def boxsize(zoomlevel):
    return 2600*(2**(13-zoomlevel))

for key,val in globals().items():
    if not key.startswith("_") and type(val) in [int,float]:
        
        print "%s: %s"%(key,val)
        
for zoomlevel in range(9,18):
    boxsize_=boxsize(zoomlevel)
    print "Zoom:",zoomlevel
    print "  Boxsize:",boxsize_/1e3,"km"
    boxcnt=playbox**2/boxsize_**2
    print "  Boxes in playbox:",boxcnt
    print "  Total tex side:",sqrt(boxcnt)*256
    print "  Texturemem:",256*256*2*boxcnt/1e6,"MB"
    print "  Texelsize:",boxsize_/256.0,"m"
    
print "Num heightmap bytes:",route*crossroute/(hgtres**2)*2*2/1e6,"MB"
print "Num heightmap bytes (Download, zipped):",route*crossroute/(hgtres**2)*2/2.0/1e6,"MB"

vertexcount=tricount
vertexobjsize=5*4
triobjsize=5*4
storesize=vertexcount*vertexobjsize+triobjsize*tricount
print "Triangle store size:",storesize



