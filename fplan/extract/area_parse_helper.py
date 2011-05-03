import re
from fplan.lib.mapper import parse_coord_str

def find_areas(page):
    areastarts=sorted(
        list(page.get_by_regex(r".*?\d{4,6}[NS].*"))+
        list(page.get_by_regex(r".*?\d{5,7}[EW].*"))
        ,
        key=lambda x:(x.y1,x.x1))
    print "Found %d area-lines on page"%(len(areastarts),)
    print areastarts
    if len(areastarts)==0: return
    idx=0
    cury=None
    while True:
        firstdiff=None
        process=[]
        miny=None
        maxy=None
        while idx<len(areastarts):
            process.append(areastarts[idx])            
            cury=areastarts[idx].y1

            if miny==None or maxy==None:
                miny=cury
                maxy=cury
            miny=min(areastarts[idx].y1,miny)
            maxy=max(areastarts[idx].y2,maxy)
            
            
            #print "Diff:",diff,"firstdiff:",firstdiff,"delta:",diff-firstdiff if diff!=None and firstdiff!=None else ''
            idx+=1
            if idx<len(areastarts):
                diff=areastarts[idx].y1-cury
                if diff!=0:
                    if firstdiff==None: firstdiff=diff
                #print "Diff:",diff
                if diff>6.0: 
                    #print "Diff too big"
                    break
                if firstdiff and diff>1.35*firstdiff: 
                    #print "bad spacing",diff,1.5*firstdiff
                    break
        #print "Determined that these belong to one area:",process
        if len(process):
            alltext="\n".join(page.get_lines(process))
            print "<%s>"%(alltext,)
            anyarea=re.findall(r"((?:\d{4,6}[NS]\s*\d{5,7}[EW])+)",alltext,re.DOTALL|re.MULTILINE)
            print "Matching:"
            print anyarea
            if not len(anyarea): continue
            if len(re.findall(r"\d{4,6}[NS]\s*\d{5,7}[EW]",anyarea[0]))>=3:
                coords=parse_coord_str(anyarea[0].strip(),filter_repeats=True)
                #print "AREA:"
                #print coords
                #print "===================================="
                coordfontsize=process[0].fontsize
                areaname=None
                for item in reversed(sorted(page.get_partially_in_rect(0,0,100,process[0].y1),key=lambda x:(x.y1,x.x1))):
                    if item.text.strip()=="": continue
                    #print "fontsize",item.fontsize,item.text,"y1:",item.y1
                    if item.fontsize>process[0].fontsize or item.bold>process[0].bold or item.italic>process[0].italic:
                        assert item.y1!=None
                        miny=min(item.y1,miny)
                        print "Found name: <%s>. Fonts: %d, %d, Fontsize: %s, old fontsize: %s"%(item.text,item.font,process[0].font,item.fontsize,process[0].fontsize)
                        prevx1=item.x1
                        revname=[]
                        for nameitem in reversed(sorted(page.get_partially_in_rect(0,item.y1+0.01,item.x2,item.y2-0.01),key=lambda x:(x.x1))):
                            if prevx1-nameitem.x2>3.0:
                                break
                            revname.append(nameitem.text.strip())                                
                        areaname=" ".join(reversed(revname))
                        break                    
                yield (areaname,coords,dict(y1=miny,y2=maxy))
        if idx>=len(areastarts): break            

