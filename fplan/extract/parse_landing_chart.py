#encoding=utf8
import re
import sys
import math
import cairo
from itertools import izip
import fplan.lib.mapper as mapper
import md5
import fetchdata
import parse
import svg_reader
import numpy

def dist(x,y):
    return math.sqrt((x[0]-y[0])**2+(x[1]-y[1])**2)

def parse_landing_chart(path,country='se'):
    print "Running parse_landing_chart"
    p=parse.Parser(path)
    
    res=[]    
    assert p.get_num_pages()==1
    url=fetchdata.getrawurl(path,country)
    ret=dict()
    ret['url']=url
    page=p.parse_page_to_items(0, donormalize=False)

    for item in page.get_by_regex(ur".*?[\d\.]+\s*°.*"):#
        d=0.1*page.width
        
        degrees,=re.match(ur'.*?([\d\.]+)\s*°.*',item.text).groups()
        #print "Found deg",item,float(degrees)
        for item2 in page.get_by_regex_in_rect(ur".*?[\d\.]+\s*'.*",item.x1-d,item.y1-d,item.x2+d,item.y2+d):
            minutes,=re.match(ur".*?([\d\.]+)\s*'.*",item2.text).groups()
            print "Found %f deg %f min"%(float(degrees),float(minutes))

    return 'oops '
    
    
    svg=svg_reader.parsesvg(path)
    bestarp=None
    scale=4
    w=svg.attrib['width']
    h=svg.attrib['height']
    assert w.endswith("pt")
    w=int(w[:-2])
    assert h.endswith("pt")
    h=int(h[:-2])
    width=int(w)
    height=int(h)
    
    
    
    
    im=cairo.ImageSurface(cairo.FORMAT_RGB24,scale*width,scale*height)
    def zoom(a,b):
        return scale*a,scale*b
    

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
    def dive(elem,out,matrix,isdef,isclip):
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
            dive(child,out,newmatrix,isdef,True)
            
            
                              

        if elem.tag.endswith("}pattern"):
            pass
        elif elem.tag.endswith("}image"):
            if not isdef:
                if isclip:
                    ctx.set_source(cairo.SolidPattern(1,0.0,0,1))
                else:
                    ctx.set_source(cairo.SolidPattern(1,1,1,1))
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
                if isclip:
                    ctx.set_source(cairo.SolidPattern(0,1,0,1))
                else:
                    ctx.set_source(cairo.SolidPattern(1,1,1,1))
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
                if isclip:
                    ctx.set_source(cairo.SolidPattern(0.5,0.5,1,1))
                else:
                    ctx.set_source(cairo.SolidPattern(1,1,1,1))
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
                def lines(xs):
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
                for line in lines(triplets(d.split())):
                    #print "line:",line
                    a,b=line
                    ctx.new_path()
                    sumpos[0]+=a[0]
                    sumpos[1]+=a[1]
                    sumpos[0]+=b[0]
                    sumpos[1]+=b[1]
                    numsum+=2
                    ctx.move_to(*zoom(*a))
                    ctx.line_to(*zoom(*b))
                    #out.append(line)
                    ctx.stroke()
                if isclip and numsum:
                    avgpos=(sumpos[0]/numsum,sumpos[1]/numsum)
                    out.append(avgpos)
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
            dive(child,out,newmatrix,isdef,False)
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
            dive(child,out,newmatrix,isdef,isclip)
    
    
    
    
    out=[]
    dive(svg,out,numpy.identity(3),False,False)


    
    def angle(line):
        (x1,y1),(x2,y2)=line
        dx,dy=(x2-x1,y2-y1)
        return ((180.0/math.pi)*math.atan2(dy,dx))%360.0
    cands=[]
    for arp in page.get_by_regex(ur"ARP"):
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
        cand=min(out,key=lambda x:dist(x,pos))   
        mindist=dist(cand,pos)
        if mindist>=0.05*width:
            continue
        candpos=zoom(*cand)
        
        ctx.set_source(cairo.SolidPattern(1,0.25,0.25,1))
        ctx.new_path()                
        ctx.set_line_width(scale*3)        
        ctx.arc(candpos[0],candpos[1],scale*15,0,2*math.pi)
        ctx.stroke()
        
        ctx.set_source(cairo.SolidPattern(1,1.0,0.0,1))                
        ctx.new_path()
        ctx.set_line_width(scale*3)        
        ctx.arc(zpos[0],zpos[1],scale*15,0,2*math.pi)
        ctx.stroke()

        #for elem in svg.findall(".//{http://www.w3.org/2000/svg}elem"):
        #    print dir(elem)
        #    print elem.attrib
        #    break
        
            #print "elem:",elem.getchildren()
                     
                
        bestarp=arp
        
        
    im.write_to_png("output.png")

    if not bestarp:
        raise Exception("Missing ARP")
    #if nr!=1: continue
    #print "page",nr
    #print page.items    

    return ret



if __name__=='__main__':
    if len(sys.argv)>1:
        icao=sys.argv[1]
    else:
        icao='ESMQ'    
    ret=parse_landing_chart("/AIP/AD/AD 2/%s/ES_AD_2_%s_2_1_en.pdf"%(icao,icao))
    print "returns",ret
