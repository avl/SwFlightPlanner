#encoding=utf8
import re
import fplan.extract.miner as miner
from itertools import izip

def fixup(s):
    def fixer(m):
        return "".join(m.groups())
    return re.sub(ur"(\d{2,3})°(\d{2})’(\d{2})”([NSEW])",fixer,s)
    


def ep_parse_tma():
    pages,date=miner.parse('/_Poland_EP_ENR_2_1_en.pdf',country='ep',usecache=True)
    for nr,page in enumerate(pages):
        #if nr!=1: continue
        print "page",nr
        print page.items
        desigs=page.get_by_regex(ur".*DESIGNATION AND LATERAL.*",re.DOTALL)
        for desig,next in izip(desigs,desigs[1:]+[None]):
            
            
            if next:
                y2=next.y1
            else:
                y2=100
            #print desig
            units=page.get_by_regex_in_rect(ur".*UNIT PROVIDING.*",
                                desig.x2,desig.y1,100,desig.y2,re.DOTALL)
            if len(units)==0: continue
            unit,=units
            vertlim,=page.get_by_regex_in_rect(ur".*VERTICAL LIMITS.*",
                                desig.x2,desig.y1,100,desig.y2,re.DOTALL)
            freq,=page.get_by_regex_in_rect(ur".*FREQUENCY.*",
                                desig.x2,desig.y1,100,desig.y2,re.DOTALL)
            
            areas=page.get_partially_in_rect(50,desig.y1-3,100,desig.y1-0.5)
            #print "partially: <%s>"%(areas,)
            if len(areas)==0:
                #print "Found continuation of area:",area
                pass
            else:
                lines=[]
                for s in reversed(page.get_lines2(areas)):
                    if re.match("\d+ \w{3} 2[01]\d{2}",s):
                        break
                    if s.count("Responsibility boundary within SECTOR"):
                        lines=[] #not real area name
                        break
                    m=re.match("\d+\.?\d*\s*([\w\s]+)\s*$",s,re.UNICODE)
                    if m:
                        lines.append(m.groups()[0])
                        break
                    lines.append(s.strip())
                    
                if len(lines)==0:
                    pass
                    #print "Continuation of area:",area
                else:
                    area=" ".join(lines)
                    #print "areastr:",area 
            print "Looking in ",desig.y2+0.5,y2
            desigs=page.get_partially_in_rect(0,desig.y2+0.5,desig.x2+1,y2-0.8)
            print repr(desigs)
            """
            def clump(desigs):
                out=[]
                y1=1e30
                y2=None
                for desig in desigs:
                    if y2!=None:
                        delta=desig.y1-y2
                        if delta>
                    y1=min(desig.y1,y1)
                    y2=max(desig.y2,y2)
                    out.append(desig.text)
            """     
            last_curvert=None
            last_curunit=None
            last_curfreq=None
            #out=[]
            
            for desig in desigs:
                wholerow=page.get_lines2(page.get_partially_in_rect(0,desig.y1+0.25,100,desig.y2-0.25))
                wholerowstr=" ".join(wholerow)
                if re.match(ur".*\d+\.\d+\s+[\w\s*]+CONTROL\s*AREA\s*$",wholerowstr,re.UNICODE):
                    continue
                if wholerowstr.count("UWAGI/REMARKS"):
                    continue
                if wholerowstr.count("1) Advisory service is not provided."):
                    continue
                
                curvert=page.get_lines2(page.get_partially_in_rect(vertlim.x1+1.0,desig.y1+0.25,vertlim.x2-1,desig.y2-0.25))
                curunit=page.get_lines2(page.get_partially_in_rect(unit.x1+0.5,desig.y1+0.25,unit.x2-0.5,desig.y2-0.25))
                curfreq=page.get_lines2(page.get_partially_in_rect(freq.x1+0.5,desig.y1+0.25,freq.x2-0.5,desig.y2-0.25))
                
                desigtext=desig.text
                desigtext=fixup(desigtext).strip()
                if desigtext=="": continue
                if re.match(ur"^\s*(?:AIRAC)?\s*(?:AMDT)?\s*\d{0,4}\s*$",desigtext):
                    continue
                if len(curvert)==0 and re.match(ur"^POLSKA.*POLISH AIR NAVIGATION SERVICES AGENCY$",desigtext,re.DOTALL):
                    continue
                if desigtext.count("Responsibility boundary within SECTOR"):
                    continue
                print "Area: %s,\n  coords:\n  <%s>\n:  unit: %s\n  freq: %s\n  vert: %s\n\n"%(
                   area,desigtext.replace("\n","\\n"),curunit,curfreq,curvert)
                
                if len(curvert)==0 and re.match("LTMA\s*EPKK",desigtext):
                    continue #strange division for Krakow TMA
                assert (not len(curvert))==(not len(curunit))
                if len(curvert)==0:
                    curvert=last_curvert
                    curunit=last_curunit
                    
                print "fixed upArea: %s,\n  coords:\n  <%s>\n:  unit: %s\n  freq: %s\n  vert: %s\n\n"%(
                   area,desigtext.replace("\n","\\n"),curunit,curfreq,curvert)
                

                last_curvert=curvert
                last_curunit=curunit
                last_curfreq=curfreq
                #delta=0
                #if len(out):
                #    delta=desig.y1-out[-1][0].y2
                #assert (len(curvert)==0) == (len(curunit)==0) == (len(curfreq)==0)
                #if len(curvert)==0:
                #    if delta<2:
                #        out[-1][0].text=out[-1][0].text.strip()+"\n"+desig.text.strip()
                #        out[-1][0].y2=desig.y2
                
                    
                     
                
                                
    
    
    
    
    
    
    
    
    
if __name__=='__main__':
    ep_parse_tma()
    
    