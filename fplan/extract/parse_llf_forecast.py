#encoding=utf8
import re
import fetchdata

def parse_groundwinds(w):
    for line in w.split('\n'):
        if not line.startswith(u'Område'):
            continue
        area,descr=line.split(':',1)
def parse_area(a,cur_area):
    a=a.strip()
    letter,part=a.split(" ",1)
    assert letter.lower()==cur_area.lower()
    assert part.startswith("DEN ")
    part=part[4:]
    #print 'part:',part
    mapping={
        u'NORRA DELEN':'n',
        u'NORDVÄSTRA DELEN':'nw',
        u'SÖDRA DELEN':'s',
        u'SYDÖSTRA DELEN':'se',
        u'MELLERSTA DELEN':'m',
        u'SYDVÄSTRA DELEN':'sw'
        }
    return letter,mapping[part.strip()]
#    return a.strip()

def parse_winds(w):
    wmap={
        '2000 ft':'2000',
        'FL50':'FL50',
        'FL100':'FL100'
    }
    ret=dict()
    for line in w.split('\n'):        
        line=line.strip()
        if line=="": continue
        #print "Parsing wind str:",line
        altstr,windstr=line.split(':',1)
        #print "Matching:'%s'"%windstr
        hdg,knots,tempsign,temp=re.match(r"(\d{3})/(\d+)([+-])(\d+)",windstr.strip()).groups()
        assert hdg.isdigit()
        temp=int(temp)
        if tempsign=='-':
            temp=-temp
        alt=wmap[altstr]
        ret[alt]=dict(direction=int(hdg),knots=int(knots),temp=temp)
    return ret
            
        
def run(cur_area):     
    data=fetchdata.get_raw_weather_for_area(cur_area)
    weather=dict()
    for prog_str in re.findall(r"<PRE>(.*?)</PRE>",data,re.DOTALL):
        prog_str=prog_str.replace("\xa0"," ")
        prog_str=unicode(prog_str,'latin1')
        if prog_str.count(u"ÖVERSIKT FÖR OMRÅDE"):
            continue
        if prog_str.count(u"Preliminär prognos för morgondagen"):
            continue
        if not prog_str.count(u"PROGNOS FÖR OMRÅDE"):
            continue
        #print prog_str
        #print "===================="
        prog=re.match(ur""".*PROGNOS FÖR OMRÅDE ([^\n]*).*
GÄLLANDE DEN (.*) MELLAN (.*) OCH (.*) UTC.*
Turbulens
(.*)
Isbildning
(.*)
Sikt/Väder/Moln
(.*)
Nollgradersisoterm
(.*)
Vind vid marken
(.*)
Vind och temperatur
(.*)
Lägsta QNH
(.*) hPa.*
"""
            ,prog_str,re.DOTALL)       
        if prog==None:
            print "No match for: "+prog_str
        keys=['area','date','t1','t2','turb','ice','weather','zerotherm','groundwind','wind','qnh']
        print "prog.groups:",len(prog.groups()),"keys:",len(keys)
        assert len(keys)==len(prog.groups())
        d=dict()
        for key,val in zip(keys,prog.groups()):
            d[key]=val
        #print "Area:",parse_area(d['area'])
        #print "Winds:",parse_winds(d['wind'])
        d['shortarea']=parse_area(d['area'],cur_area)
        d['winds']=parse_winds(d['wind'])
        #print m
        #print "================================================================"
        weather[d['shortarea']]=d
    return weather
if __name__=='__main__':
    run('B')
