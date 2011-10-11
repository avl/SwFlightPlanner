import math

def max_tiles(xres,yres,tilesize):
	diag_angle=math.atan2(yres,xres)
	diag_length=math.sqrt(xres**2+yres**2)
	hdiag_length=diag_length/2.0
	
	base=yres
	#b= 180 - 90 - diag_angle
	b=math.pi-math.pi/2-diag_angle
	#maxh/base = sin(b)
	#maxh = sin(b)*base
	maxh=math.sin(b)*base
	print "diag_length:",diag_length
	print "max height:",maxh
	u=int(math.floor((diag_length)/tilesize))+2
	print "diag tiles",u
	v=int(math.floor((maxh)/tilesize))+2
	print "h tiles",v
	print "Tot count:",u*v
	print "Real area:",xres*yres
	print "Tile area:",u*v*tilesize*tilesize
	print "RAM:",u*v*tilesize*tilesize*2/1e6,"MB"
	
