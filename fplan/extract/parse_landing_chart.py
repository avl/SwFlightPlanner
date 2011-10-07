#encoding=utf8
import re
import StringIO
import sys
import math
import cairo
import pickle
from itertools import izip
import fplan.lib.mapper as mapper
import md5
import fetchdata
import parse
import svg_reader
import numpy
import numpy.linalg as linalg
import os
import Image
from fplan.lib.blobfile import BlobFile
def diff(x,y):
    return (x[0]-y[0],x[1]-y[1])
def dist(x,y):
    return math.sqrt((x[0]-y[0])**2+(x[1]-y[1])**2)
def cartesian(xs,ys):
    for x in xs:
        for y in ys:
            yield x,y
            
def chop_up(inputfile,outputfile,level):
    im=Image.open(inputfile)
    w,h=im.size
    fac=1<<level
    w/=fac
    h/=fac
    print "Size",w,h    
    limitx2=256*(int((w+255)/256))
    limity2=256*(int((h+255)/256))
    blob=BlobFile(outputfile,0,
            0,0,limitx2,limity2,'w')
    for x in xrange(0,limitx2,256):
        for y in xrange(0,limity2,256):
            view=im.crop((fac*x,fac*y,fac*(x+256),fac*(y+256)))
            view=view.resize((256,256),Image.ANTIALIAS)
            view.save("tmp/temp%d_%d_%d.png"%(level,x,y))
            io=StringIO.StringIO()
            view.save(io,'png')
            io.seek(0)
            pngdata=io.read()
            blob.add_tile(x,y,pngdata)
    blob.close()
    pass
            
def parse_landing_chart(path,arppos,icao,country='se'):
    print "Running parse_landing_chart"
    p=parse.Parser(path)
    arppos=mapper.from_str(arppos)
    res=[]    
    assert p.get_num_pages()<=2
    url=fetchdata.getrawurl(path,country)
    ret=dict()
    ret['url']=url
    data,nowdate=fetchdata.getdata(path,country=country,maxcacheage=7200)
    cksum=md5.md5(data).hexdigest()
    ret['checksum']=cksum
    page=p.parse_page_to_items(0, donormalize=False)
    ret['width']=page.width
    ret['height']=page.height
    width=page.width
    height=page.height
    scale=2048.0/min(width,height)
    width*=scale
    height*=scale
    width=int(width+0.5)
    height=int(height+0.5)
    
    ret['render_width']=width
    ret['render_height']=height
    
    tmppath=os.path.join(os.getenv("SWFP_DATADIR"),"adcharts")
    if not os.path.exists(tmppath):
        os.makedirs(tmppath)
    assert len(icao)==4
    outpath=os.path.join(tmppath,icao+".png")
    def render(inputfile,outputfile):
        r="pdftoppm -f 0 -l 0 -scale-to-x %d -scale-to-y %d -png -freetype yes -aa yes -aaVector yes %s >%s"%(
                  width,height,inputfile,outputfile)
        print "rendering",r
        assert 0==os.system(r)
    ret['image']=icao+".png"
    fetchdata.getcreate_derived_data_raw(
                path,outpath,render,"png")
    
    outpath2=os.path.join(tmppath,icao+"2.png")
    def greyscale(input,output):
        assert 0==os.system("convert -define png:color-type=0 -depth 8 -type grayscale %s %s"%(input,output))
    
    fetchdata.getcreate_local_data_raw(
                outpath,outpath2,greyscale)
 

    assert country=='se'
    assert icao.startswith("ES") 
    blobname=icao
    ckpath=os.path.join(tmppath,"%s.cksum"%(blobname,))
    if os.path.exists(ckpath):
        os.unlink(ckpath)
    for level in xrange(5):
        hashpath=os.path.join(tmppath,"%s-%d.bin"%(blobname,level))
        fetchdata.getcreate_local_data_raw(
                    outpath2,hashpath,lambda input,output:chop_up(input,output,level))    
    ret['blobname']=blobname
    
    print "Writing cksum",ckpath,cksum
    open(ckpath,"w").write(cksum)
    return ret

def purge_old(chartblobnames,country="se"):
    def find(filename):
        for chart in chartblobnames:
            if filename.startswith(chart): return True
        return False
    assert country=="se"
    tmppath=os.path.join(os.getenv("SWFP_DATADIR"),"adcharts")
    for fname in list(os.listdir(tmppath)):
        if not find(fname):
            path=os.path.join(tmppath,fname)
            os.unlink(path)
            print "Removing file",fname
        else:
            print "Keeping",fname
            
    

def get_chart(blobname,level,version):
    tmppath=os.path.join(os.getenv("SWFP_DATADIR"),"adcharts")
    blobpath=os.path.join(tmppath,"%s-%d.bin"%(blobname,level))
    ckpath=os.path.join(tmppath,"%s.cksum"%(blobname,))    
    return open(blobpath).read(),open(ckpath).read()
def get_chart_png(adimg):
    tmppath=os.path.join(os.getenv("SWFP_DATADIR"),"adcharts",adimg)
    return open(tmppath).read()
    
def get_timestamp(blobname,level):
    tmppath=os.path.join(os.getenv("SWFP_DATADIR"),"adcharts")
    path=os.path.join(tmppath,"%s-%d.bin"%(blobname,level))
    return os.path.getmtime(path)

"""
def legacystuff():    
    svg=svg_reader.parsesvg(path,0)
    bestarp=None
    scale=4
    def zoom(a,b):
        return scale*a,scale*b
    assert svg.attrib['viewBox'].startswith("0 0")
    w=svg.attrib['width']
    h=svg.attrib['height']
    assert w.endswith("pt")
    w=float(w[:-2])
    assert h.endswith("pt")
    h=float(h[:-2])
    width=(w)
    height=(h)
    
    
    
    
    
    cache=False
    write_cache=True
    if not cache or not os.path.exists("pickled_ac_chart_"+icao):
        im=cairo.ImageSurface(cairo.FORMAT_RGB24,int(scale*width+1),int(scale*height+1))
        
    
        def parse_transform(s):
            #print "Matching",s
            coords,=re.match(ur"^matrix\((.*)\)$",s).groups()
            d=[float(num) for num in coords.split(',')]
            assert len(d)==6
            mat=numpy.matrix([
                     [d[0],d[2],d[4]],
                     [d[1],d[3],d[5]],
                     [0,0,1]
                     ])
            #print "parsed %s as %s"%(s,mat)
            return mat
            
                
        ctx=cairo.Context(im)
        ctx.set_line_width(scale)
        lookup=dict()
        def dive(elem,sights,matrix,isdef,isclip):
            if elem.tag.count("defs"):
                isdef=True
            #print "Parsing tag",elem.tag
            #if elem.tag.count("symbol"):
            #    return
            #if elem.tag.count("glyph"):
            #    return
            #if elem.tag.count("pattern"):
            #    return
            if 'transform' in elem.attrib:
                #print "Matrix before",matrix
                assert not 'patternTransform' in elem.attrib
                newmatrix=matrix*parse_transform(elem.attrib['transform'])
            elif 'patternTransform' in elem.attrib:
                #print "Matrix before",matrix
                assert not 'transform' in elem.attrib
                newmatrix=matrix*parse_transform(elem.attrib['patternTransform'])
                #print "Matrix after",matrix
            else:
                newmatrix=matrix
            if "id" in elem.attrib:
                lookup[elem.attrib['id']]=elem
                
            def trans(pos,matrix):
                as_m=numpy.matrix([[pos[0]],[pos[1]],[1]])
                #print "Matrix:",matrix
                ret=matrix*as_m
                t=ret[0,0],ret[1,0]
                #if dist(pos,t)>10:
                #    print "Transformed ",pos,"into",t
                return t
            if 'clip-path' in elem.attrib:
                #"url(#clip2309)"
                #print "Interpreting clip path: <%s>"%(elem.attrib['clip-path'],)
                targetid,=re.match(r"^url\(#(.*)\)$",elem.attrib['clip-path']).groups()
                child=lookup[targetid]
                dive(child,sights,newmatrix,isdef,True)
                
                
                                  
    
            if elem.tag.endswith("}pattern"):
                pass
            elif elem.tag.endswith("}image"):
                if not isdef:
                    ctx.set_source(cairo.SolidPattern(1,0.0,0,1))
                    x=float(elem.attrib.get('x',0))
                    y=float(elem.attrib.get('y',0))
                    #print "Drawing image at",x,y
                    width=float(elem.attrib['width'])
                    height=float(elem.attrib['height'])
                    ps=[(x,y),(x+width,y),(x+width,y+height),(x,y+height)
                        ]
                    ps2=[]
                    for p in ps:
                        ps2.append(zoom(*trans(p,newmatrix)))
                    if isclip:
                        print "image",x,y,width,height
                    for a,b in zip(ps2,[ps2[-1]]+ps2[:-1]):
                        x1,y1=a
                        x2,y2=b
                        ctx.move_to(x1,y1)
                        ctx.line_to(x2,y2)
                        ctx.stroke()
                        #ctx.rectangle(*(zoom(x,y)+zoom(width,height)))                     
            elif elem.tag.endswith("}rect"):
                if not isdef:
                    ctx.set_source(cairo.SolidPattern(0,1,0,1))
                    x=float(elem.attrib.get('x',0))
                    y=float(elem.attrib.get('y',0))
                    width=float(elem.attrib['width'])
                    height=float(elem.attrib['height'])
                    ps=[(x,y),(x+width,y),(x+width,y+height),(x,y+height)
                        ]
                    ps2=[]
                    for p in ps:
                        ps2.append(zoom(*trans(p,newmatrix)))
                    if isclip:
                        print "rect",x1,y1,x2,y2
                    for a,b in zip(ps2,[ps2[-1]]+ps2[:-1]):
                        x1,y1=a
                        x2,y2=b
                        ctx.new_path()
                        ctx.set_line_width(scale*3)                
                        ctx.move_to(x1,y1)
                        ctx.line_to(x2,y2)
                        ctx.stroke()
                        ctx.set_line_width(scale)
                        #ctx.rectangle(*(zoom(x,y)+zoom(width,height)))
            elif elem.tag.endswith("path"):
                if not isdef:
                    #print "Found path:",elem,elem.attrib            
                    ctx.set_source(cairo.SolidPattern(0.5,0.5,1,1))
                    d=elem.attrib['d']
                    def triplets(xs):
                        what=None
                        coords=[]
                        for x in xs:
                            if x.isalpha():
                                if what:
                                    yield (what,tuple(coords))
                                what=x
                                coords=[]
                            else:
                                coords.append(float(x))
                        if what:
                            yield (what,tuple(coords))
                    def getlines(xs):
                        last=None
                        first=None
                        for what,coords in xs:
                            if what=='Z' or what=='z':
                                assert len(coords)==0
                                if first:
                                    yield trans(last,newmatrix),trans(first,newmatrix)
                                last=None
                                first=None
                                continue
                            if last!=None:
                                if what=='L':
                                    assert len(coords)==2
                                    yield trans(last,newmatrix),trans(coords,newmatrix)
                                if what=='l':
                                    assert len(coords)==2
                                    coords=(last[0]+coords[0],last[1]+coords[1])
                                    yield trans(last,newmatrix),trans(coords,newmatrix)
                                
                            last=coords[-2:]
                            if not first:first=last
                    #for kind,pos in triplets(d.split()):
                    #    print kind,pos
                    sumpos=[0,0]
                    numsum=0
                    lines=sights.setdefault('lines',[])
                    crosshair=sights.setdefault('crosshair',[])
                    for line in getlines(triplets(d.split())):
                        #print "line:",line                                    
                        a,b=line
                        x1,y1=a
                        x2,y2=b
                        if dist(a,b)>5 and (abs(y1-y2)<2 or abs(x1-x2)<2):
                            lines.append(line)
                        ctx.new_path()
                        sumpos[0]+=a[0]
                        sumpos[1]+=a[1]
                        sumpos[0]+=b[0]
                        sumpos[1]+=b[1]
                        numsum+=2
                        ctx.move_to(*zoom(*a))
                        ctx.line_to(*zoom(*b))
                        #sights.append(line)
                        ctx.stroke()
                    if isclip and numsum:
                        avgpos=(sumpos[0]/numsum,sumpos[1]/numsum)
                        crosshair.append(avgpos)
                else:
                    pass
            elif elem.tag.endswith("}use"):
                #print elem.attrib
                idname=elem.attrib['{http://www.w3.org/1999/xlink}href']
                assert idname.startswith("#")
                idname=idname[1:]
                child=lookup[idname]
                if 'x' in elem.attrib:
                    x=float(elem.attrib['x'])
                    y=float(elem.attrib['y'])
                else:
                    x=y=0
                usematrix=numpy.matrix([
                         [1,0,x],
                         [0,1,y],
                         [0,0,1]
                         ])
                newmatrix=usematrix*newmatrix
                dive(child,sights,newmatrix,isdef,False)
            elif (elem.tag.endswith("}g") or 
                elem.tag.endswith("}svg") or 
                elem.tag.endswith("}defs") or 
                elem.tag.endswith("}symbol") or 
                elem.tag.endswith("}mask") or 
                elem.tag.endswith("}clipPath")): 
                pass
            else:
                #print "Unknown tag",elem.tag
                raise Exception("Unknown tag: %s"%(elem.tag,))
            for child in elem.getchildren():                    
                dive(child,sights,newmatrix,isdef,isclip)
        sights=dict()
        dive(svg,sights,numpy.identity(3),False,False)
        if write_cache:
            pickle.dump(sights,open("pickled_ac_chart_"+icao,"w"))
        im.write_to_png("output.png")
    else:
        sights=pickle.load(open("pickled_ac_chart_"+icao))   
        
    
    
    
    crosshair=sights['crosshair']
    lines=sights['lines']
    
    def get_crosshairs_near(pos,cutoff):
        #OK, the problem is that the crosshair isn't really crossing, just nearly.
        #This is a tricky one.
        for hair in crosshair:
            yield hair
        px1=pos[0]-cutoff
        py1=pos[1]-cutoff
        px2=pos[0]+cutoff
        py2=pos[1]+cutoff
        for line1 in lines:
            #horiz
            (x1,y1),(x2,y2)=line1
            if abs(y1-y2)>0.1:continue    
            hx1=min(x1,x2);hy=min(y1,y2)  
            hx2=max(x1,x2);  
            if hx1<px1 or hx2>px2 or hy<py1 or hy>py2: continue 
            print "Considering horiz line",line1
            for line2 in lines:
                #vert
                (x1,y1),(x2,y2)=line2
                if abs(x1-x2)>0.1:continue
                vx=min(x1,x2);vy1=min(y1,y2)  
                vy2=max(y1,y2)                  
                if vx<px1 or vx>px2 or vy1<py1 or vy2>py2: continue 
                print "Considering vert line",line2
                if vx>=hx1 and vx<=hx2:
                    if hy>=vy1 and hy<=vy2:
                        print "--- THey do cross"
                        yield (vx,hy)                 
                
            
                
        
    
    constraints=[]
    for item in page.get_by_regex(ur".*?[\d\.]+\s*°.*"):#
        d=0.1*page.width        
        degrees,=re.match(ur'.*?([\d\.]+)\s*°.*',item.text).groups()
        degrees=float(degrees)
        #print "Found deg",item,float(degrees)
        for item2 in page.get_by_regex_in_rect(ur".*?[\d\.]+\s*'.*",item.x1-d,item.y1-d,item.x2+d,item.y2+d):
            minutes,=re.match(ur".*?([\d\.]+)\s*'.*",item2.text).groups()
            minutes=float(minutes)
            print "Found %f deg %f min"%(float(degrees),float(minutes))
            cands=[]
            def tr(x,y):
                x*=1.0/page.width
                y*=1.0/page.height
                return (width*x,height*y)                
            parselongitude=(degrees>=10.0 and degrees<=25.0)
            parselatitude=(degrees>=50.0 and degrees<=80.0)
            print "Parselat/lon",parselatitude,parselongitude
            for line in lines:
                d=min([dist(a,b) for a,b in cartesian(
                        [line[0],line[1]],
                        [tr(item.x1,item.y1),tr(item.x2,item.y2),tr(item2.x1,item2.y1),tr(item2.x2,item2.y2)])])
                if d>width/20: continue
                print "Checked line: %s, d: %s"%(line,d)
                (x1,y1),(x2,y2)=line
                isvert=abs(x1-x2)<2
                ishoriz=abs(y1-y2)<2
                print "Short d: ",d,"isvert/Horiz:",isvert,ishoriz
                if parselongitude and isvert:
                    cands.append((d,0.5*(x1+x2),(0.5*(x1+x2),0.5*(y1+y2))))
                if parselatitude and ishoriz:
                    cands.append((d,0.5*(y1+y2),(0.5*(x1+x2),0.5*(y1+y2))))
            if not cands:continue
            bestcand=min(cands,key=lambda cand:cand[0])
            d,coord,point=bestcand
            decdeg=float(degrees)+float(minutes)/60.0
            if parselatitude:constraints.append(dict(latitude=decdeg,y=coord,point=point))
            if parselongitude:constraints.append(dict(longitude=decdeg,x=coord,point=point))
            
    
    angles=[]
    A=[]
    B=[]
    Ah=[]
    Bh=[]
    for constraint in constraints:
        if 'latitude' in constraint: 
            point=constraint['point']
            decdeg=constraint['latitude']
            if point[0]>width/8: continue
            for o in constraints:
                if not 'latitude' in o: continue
                opoint=o['point']
                if abs(opoint[1]-point[1])<height/15 and opoint[0]>width/2:
                    if abs(decdeg-o['latitude'])<1e-3:
                        odecdeg=o['latitude']                
                        break               
            else:
                print "NOthing matches",constraint
                continue
            if dist(point,opoint)<width/2:
                continue
            print "Found clue",point,opoint,decdeg,odecdeg
            A.append((point[0],point[1],1))
            Ah.append([decdeg]) 
            A.append((opoint[0],opoint[1],1))
            Ah.append([odecdeg]) 
            delta=diff(opoint,point)
            a=(180.0/math.pi)*math.atan2(delta[1],delta[0])
        if 'longitude' in constraint: 
            point=constraint['point']
            decdeg=constraint['longitude']
            if point[1]>height/8: continue
            for o in constraints:
                if not 'longitude' in o: continue
                opoint=o['point']                
                if abs(opoint[0]-point[0])<width/15 and opoint[1]>height/2:
                    if abs(decdeg-o['longitude'])<1e-3:
                        odecdeg=o['longitude']                
                        break            
            else:
                print "NOthing matches",constraint
                continue
            if dist(point,opoint)<width/2:
                continue
            print "Found clue",point,opoint,decdeg,odecdeg
            B.append((point[0],point[1],1))
            Bh.append([decdeg])
            B.append((opoint[0],opoint[1],1))
            Bh.append([odecdeg])
            delta=diff(opoint,point)
            a=(180.0/math.pi)*math.atan2(delta[1],delta[0])-90
        print "ANGLE:",a,"deg"
        angles.append(a)
            
    
    
    print 
    #print constraints
    #sys.exit(0)
    def angle(line):
        (x1,y1),(x2,y2)=line
        dx,dy=(x2-x1,y2-y1)
        return ((180.0/math.pi)*math.atan2(dy,dx))%360.0
    cands=[]
    curbestarpdist=None
    
    def find_arps(page):
        for arp in page.get_by_regex(ur"\bARP\b"):
            yield arp
        for a in page.get_by_regex(ur"\bA\b"):
            print "got A",a
            for r in page.get_by_regex_in_rect(ur"\bR\b",a.x1-100,a.y1-100,a.x2+100,a.y2+100):
                print "got R",r
                for p in page.get_by_regex_in_rect(ur"\bP\b",r.x1-100,r.y1-100,r.x2+100,r.y2+100):
                    print "got P",p
                    yield a
        
    for arp in find_arps(page):
        print "Got arp"
        print arp.x1,arp.y1
        pos=(arp.x1,arp.y1)
        x=arp.x1
        y=arp.y1
        x*=1.0/page.width
        y*=1.0/page.height
        pos=(width*x,height*y)
        zpos=zoom(*pos)
        #ctx.circle()
        cand=min(get_crosshairs_near(pos,150),key=lambda x:dist(x,pos))
        
        mindist=dist(cand,pos)
        if mindist>=0.05*width:
            continue
        middist=dist(cand,(0.5*width,0.5*height))
        print "Cand arp pixel",cand
        
        if not cache:
            #Pos of crosshairs
            candpos=zoom(*cand)
            ctx.set_source(cairo.SolidPattern(1,0.25,0.25,0.5))
            ctx.new_path()                
            ctx.set_line_width(scale*3)        
            ctx.arc(candpos[0],candpos[1],scale*15,0,2*math.pi)
            ctx.stroke()
            
            #Pos of ARP-text
            ctx.set_source(cairo.SolidPattern(1,1.0,0.0,0.5))                
            ctx.new_path()
            ctx.set_line_width(scale*3)        
            ctx.arc(zpos[0],zpos[1],scale*15,0,2*math.pi)
            ctx.stroke()
    
        #for elem in svg.findall(".//{http://www.w3.org/2000/svg}elem"):
        #    print dir(elem)
        #    print elem.attrib
        #    break
        
            #print "elem:",elem.getchildren()
        
        if bestarp==None or middist<curbestarpdist:             
            curbestarpdist=middist
            bestarp=cand
        
        

    #if not bestarp:
    #    raise Exception("Missing ARP")
    if bestarp:
        print "arppos",arppos,"bestarp",bestarp
        assert type(arppos)==tuple
        A.append((bestarp[0],bestarp[1],1))
        Ah.append([arppos[0]])
        B.append((bestarp[0],bestarp[1],1))
        Bh.append([arppos[1]])
    else:
        print "No ARP found"
        raise Exception("No arp")
        
    def solve_and_check(A,Ah,B,Bh):
        Am=numpy.matrix(A)
        Amh=numpy.matrix(Ah)
        Bm=numpy.matrix(B)
        Bmh=numpy.matrix(Bh)
        print "Am,Amh",Am,Amh
        Ar,Aresidue=linalg.lstsq(Am,Amh)[0:2]
        Br,Bresidue=linalg.lstsq(Bm,Bmh)[0:2]
        print "Aresidue",Aresidue
        print "Bresidue",Bresidue
        print "Ar:",Ar
        print "Br:",Br
        A11,A12,Tx=Ar.transpose()[0].tolist()[0]
        A21,A22,Ty=Br.transpose()[0].tolist()[0]
        mA=numpy.matrix([[A11,A12],[A21,A22]])
        T=numpy.matrix([[Tx],[Ty]])
        print "A:",A,type(A)
        for m,mh in zip(A,Ah):
            print "m:",m,"mh:",mh        
            x,y,one=m
            deg=mh[0]
            X=numpy.matrix([[x],[y]])        
            Y=mA*X+T
            lat,lon=Y[0,0],Y[1,0]
            print "Mapped lat",lat,"correct",deg
            if not (deg-lat)<0.05*1.0/60.0:
                return False
        for m,mh in zip(B,Bh):
            print "m:",m,"mh:",mh        
            x,y,one=m
            deg=mh[0]
            X=numpy.matrix([[x],[y]])        
            Y=mA*X+T
            lat,lon=Y[0,0],Y[1,0]
            print "Mapped lon",lon,"correct",deg
            if not (deg-lon)<0.05*1.0/60.0:
                return False
        return mA,T
    res=solve_and_check(A,Ah,B,Bh)
    if not res:
        for idx in xrange(len(A)):
            tA=A[:idx]+A[idx+1:]
            tAh=Ah[:idx]+Ah[idx+1:]
            res=solve_and_check(tA,tAh,B,Bh)
            if res:break
        if not res:
            for idx in xrange(len(B)):
                tB=B[:idx]+B[idx+1:]
                tBh=Bh[:idx]+Bh[idx+1:]
                res=solve_and_check(A,Ah,tB,tBh)
                if res:break
        if not res:
            im.write_to_png("output.png")            
            raise Exception("Couldn't solve system, even if discounting 1 outlier")
        pass
    mA,T=res
            
                 
    print "mA:",mA
    print "T:",T
    for x in [0,width]:
        for y in [0,height]:
            X=numpy.matrix([[x],[y]])
            print "A dim",mA.shape
            print "X dim",X.shape
            Y=mA*X+T
            print "Screen coordinates",X,"correspond to latlon",Y
    
    
    Ai=linalg.inv(mA)
    
    print "Ai",Ai
    #A*X + T = Y
    #A*X     = (Y-T)
    #X     = Ai*(Y-T)
    where=Ai*(numpy.matrix(arppos).transpose()-T)
    print "ARP center is at latlon",arppos,"which is pixels",where
    
    if not cache:
        ctx.set_source(cairo.SolidPattern(0,1.0,0.0,1))                
        ctx.new_path()
        ctx.set_line_width(scale*3)
        x,y=zoom(where[0,0],where[1,0])
        print "Drawing arc at x,y",x,y        
        ctx.arc(x,y,scale*15,0,2*math.pi)
        ctx.stroke()
        im.write_to_png("output.png")
    #if nr!=1: continue
    #print "page",nr
    #print page.items    

    return ret

"""

if __name__=='__main__':
    if len(sys.argv)>1:
        cur_icao=sys.argv[1]
    else:
        cur_icao='ESMQ'    
    arppos=mapper.parse_coords("564108N","0161715E")
    ret=parse_landing_chart("/AIP/AD/AD 2/%s/ES_AD_2_%s_2_1_en.pdf"%(cur_icao,cur_icao),icao=cur_icao,arppos=arppos)
    print "returns",ret
