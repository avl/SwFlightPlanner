#encoding=utf8
import re
import fplan.extract.miner as miner
from itertools import izip
import fplan.lib.mapper as mapper
import md5

def fixup(s):
    def fixer(m):
        return "".join(m.groups())
    return re.sub(ur"(\d{2,3})°(\d{2})[’'](\d{2}\.?\d*)[”\"']{1,2}([NSEW])",fixer,s)
    
def parsealt(astr):
    fl,meter,feet=re.match(ur"(?:FL\s*(\d+)\s*C?|(?:(\d+)\s*m)?\s*(?:\(?\s*(\d+)\s*ft\s*\)?)?\s*(?:AMSL)?)",astr).groups()
    if fl:
        return "FL%03d"%(int(fl))
    if feet:
        return "%d ft MSL"%(int(feet),)
    if meter:
        feet=float(meter)/0.3048
        return "%d ft MSL"%(int(feet+0.999),)
    raise Exception("Unparseable altitude: %s"%(astr,))

def ep_parse_tma():
    spaces=[]
    pages,date=miner.parse('/_Poland_EP_ENR_2_1_en.pdf',
                           country='ep',usecache=True,
                           maxcacheage=86400*7
                           )
    
    
    
    for nr,page in enumerate(pages):
        #if nr!=1: continue
        #print "page",nr
        #print page.items
        desigs=page.get_by_regex(ur".*DESIGNATION AND LATERAL.*",re.DOTALL)
        for desig,next in izip(desigs,desigs[1:]+[None]):
            
            
            
            if nr==0:
                #FIR
                
                uwagi=page.get_by_regex_in_rect(ur".*UWAGI\s*/\s*REMARKS.*",
                                0,desig.y2,100,100,re.DOTALL)[0]
                coords=page.get_lines2(page.get_partially_in_rect(
                        0,desig.y2+0.5,desig.x2+10,uwagi.y1-0.5))
                
                raw="\n".join(coords)
                #print "Raw:\n",raw
                d=md5.md5(raw.encode('utf8')).hexdigest()
                assert d=="f336800a8183f1360415d2afef38e9ae"
                #print "Md5-digest",d
#/further along the state border to the point 54°36’14.03”N 019°24’15.02”E -

                raw=fixup(u"""
54°27’28.03”N 019°38’24.05”E -
54°36’14.03”N 019°24’15.02”E -
55°50’58.98”N 017°32’52.80”E -
54°54’58.84”N 015°51’52.92”E -
54°55’00.00”N 015°08’07.00”E -
/from this point the arc of 30 km radius centred at point 55°04’04”N 014°44’48”E -
54°55’00”N 014°21’27”E - 
54°07’38”N 014°15’17”E -
54°07’34”N 014°12’05”E -
53°59’16”N 014°14’32”E -
53°55’40”N 014°13’34”E -
<hack_longway_around_border>/further along the state border to the point 542615N 0194751E
                """)
                
                ##print "rw:",raw 
                fir=mapper.parse_coord_str(raw,context='poland')
                fir_context=[fir]#In principle, a FIR could consist of multiple non-overlapping regions. In this case, the list here would contain more than one list of points
                #print fir
                #sys.exit(1)
                
                spaces.append(                            
                    dict(
                         points=fir,
                         name="WARSZAWA FIR",
                         floor="GND",
                         ceiling="-",
                         freqs=[]
                         ))
                continue

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
                    if re.match(ur"\s*AIP\s*POLAND\s*",s):
                        #not real area.
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
                    print "Continuation of area:",area
                else:
                    area=" ".join(lines)
                    #print "areastr:",area 
            print "Parsing area",area            
            uwagis=page.get_by_regex_in_rect(ur".*UWAGI/REMARKS.*",
                            0,desig.y2+1,100,100,re.DOTALL)
            if len(uwagis):
                y2=uwagis[0].y1-0.1
                print "uwagi-start",y2
            else:
                if next:
                    y2=next.y1
                    print "next.y1",next.y1
                else:
                    y2=100
                    print "end of page",100
            #print desig
            units=page.get_by_regex_in_rect(ur".*UNIT PROVIDING.*",
                                desig.x2,desig.y1,100,desig.y2,re.DOTALL)
            if len(units)==0: continue
            unit,=units
            vertlim,=page.get_by_regex_in_rect(ur".*VERTICAL LIMITS.*",
                                desig.x2,desig.y1,100,desig.y2,re.DOTALL)
            freq,=page.get_by_regex_in_rect(ur".*FREQUENCY.*",
                                desig.x2,desig.y1,100,desig.y2,re.DOTALL)
            
            #print "Looking in ",desig.y2+0.5,y2
            desigs=page.get_partially_in_rect(0,desig.y2+0.5,desig.x2+1,y2-0.8)
            #print "desigs,",repr(desigs)
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
            #last_curfreq=None
            #out=[]
            
            raws=[]
            for sub in desigs:
                wholerow=page.get_lines2(page.get_partially_in_rect(0,sub.y1+0.25,100,sub.y2-0.25))
                wholerowstr=" ".join(wholerow)
                print "Parse:<%s>"%(sub,)
                if re.match(ur".*\d+\.\d+\s+[\w\s*]+CONTROL\s*AREA\s*$",wholerowstr,re.UNICODE):
                    continue
                if wholerowstr.count("UWAGI/REMARKS"):
                    continue
                if wholerowstr.count("1) Advisory service is not provided."):
                    continue
                
                curvert=page.get_lines2(page.get_partially_in_rect(vertlim.x1+1.0,sub.y1+0.25,vertlim.x2-1,sub.y2-0.25))
                curunit=page.get_lines2(page.get_partially_in_rect(unit.x1+0.5,sub.y1+0.25,unit.x2-0.5,sub.y2-0.25))
                curfreq=page.get_lines2(page.get_partially_in_rect(freq.x1+0.5,sub.y1+0.25,freq.x2-0.5,sub.y2-0.25))
                
                desigtext=sub.text
                desigtext=fixup(desigtext).strip()
                if desigtext=="": continue
                if re.match(ur"^\s*(?:AIRAC)?\s*(?:AMDT)?\s*\d{0,4}\s*$",desigtext):
                    continue
                if len(curvert)==0 and re.match(ur"^POLSKA.*POLISH AIR NAVIGATION SERVICES AGENCY$",desigtext,re.DOTALL):
                    continue
                if desigtext.count("Responsibility boundary within SECTOR"):
                    continue
                #print "Area: %s,\n  coords:\n  <%s>\n:  unit: %s\n  freq: %s\n  vert: %s\n\n"%(
                #   area,desigtext.replace("\n","\\n"),curunit,curfreq,curvert)
                
                if len(curvert)==0 and re.match("LTMA\s*EPKK",desigtext):
                    continue #strange division for Krakow TMA
                    
                #print "fixed upArea: %s,\n  coords:\n  <%s>\n:  unit: %s\n  freq: %s\n  vert: %s\n\n"%(
                #   area,desigtext.replace("\n","\\n"),curunit,curfreq,curvert)
                coords=[]
                lines=desigtext.split("\n")
                subname=lines[0].strip()
                foundheader=False
                if len(curvert)==0:
                    #this is continuation of a previous item
                    foundheader=True
                if area.count("RMZ"):
                    foundheader=True #it doesn't have a header
                for line in lines[1:]:
                    print "fh:",foundheader,"Parsed single line:",repr(line)
                    line=line.strip()
                    if not line: continue
                    if line.endswith("points:"):
                        foundheader=True
                        continue
                    if foundheader:
                        if line.endswith("E"):
                            line+=" - "
                        coords.append(line)
                raw=" ".join(coords)
                def s(x):
                    return x.replace(" ",ur"\s*")
                #raw=re.sub(s(ur"Linia łącząca następujące punkty : / The line joining the following points :? "),               #           "",raw)
                
                print "raw area:<%s>"%(repr(raw),)
                
                
                points=mapper.parse_coord_str(raw,context="poland",fir_context=fir_context)

                if len(curvert)==0:
                    lastspace=spaces[-1]
                    assert len(curunit)==0
                    assert len(curfreq)==0
                    lastspace['points'].extend(points)
                else:                    
                    #print "Raw curvert:",repr(curvert)
                    ceiling,floor=[parsealt(x.strip()) for x in curvert]
                    
                    name=area+" "+subname
                    spaces.append(                            
                        dict(
                             points=points,
                             name=name,
                             floor=floor,
                             ceiling=ceiling,
                             freqs=[]
                             ))
                #last_curfreq=curfreq
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
    
    