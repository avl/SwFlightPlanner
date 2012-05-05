#encoding=utf8
import fplan.extract.fetchdata as fetchdata
import lxml.html
import sys
import fplan.lib.mapper as mapper
import re
from fplan.lib.poly_cleaner import clean_up_polygon
from fplan.extract.html_helper import alltext,alltexts
from datetime import datetime
from ee_common import get_airac_date
    
eer1txt=u"""573311N 0271110E –
then along the EETT FIR boundary to the point 573104N 0272102E –
then along the EETT FIR boundary to the point 592818N 0280236E –
then along the EETT FIR boundary to the point 594519N 0264317E – 595106N 0260442E – 594847N 0260108E – 594300N 0263900E – 593500N 0265200E – 593300N 0273900E – 592500N 0280000E – 592200N 0280400E – 591800N 0275000E – 590000N 0273700E – 584800N 0271600E – 583000N 0272400E – 581200N 0272400E – 575800N 0273300E – 573311N 0271110E"""

firtxt=u"""592818N 0280236E –
Along the common Estonian/X state boundary to 573100N 0272000E –
Along the common Estonian/X state boundary to 575300N 0242200E – 
575228N 0242124E – 575502N 0241540E – 575357N 0241234E – 575357N 0233604E – 574658N 0233855E – 574011N 0233456E – 573538N 0232422E – 573511N 0231051E – 574208N 0225957E – 574650N 0225428E – 575627N 0224227E – 575539N 0223501E – 574645N 0220836E – 574458N 0215458E – 574547N 0215034E – 574712N 0214300E – 575124N 0213848E – 575342N 0213648E – 580700N 0212900E – 582448N 0203834E – 590000N 0210000E – 595300N 0245100E – 595430N 0252000E – 595300N 0255200E – 595200N 0255830E – 593642N 0273812E – 592818N 0280236E
"""
def ee_parse_tma2():
    spaces=[]
    airac_date=get_airac_date()    
    url="/%s/html/eAIP/EE-ENR-2.1-en-GB.html"%(airac_date,)
    parser=lxml.html.HTMLParser()
    data,date=fetchdata.getdata(url,country='ee')
    parser.feed(data)
    tree=parser.close()
    icaos=[]
    def nested(tab):
        if tab==None: return False
        if tab.getparent() is None:
            return False
        #print dir(tab)
        if tab.tag=='table':
            return True
        return nested(tab.getparent())
    for tab in tree.xpath(".//table"):
        print "table alltext:",alltext(tab)
        if nested(tab.getparent()): continue
        firsttr=tab.xpath(".//tr")[0]
        ntext=alltext(firsttr)
        print "firsttr",firsttr
        print "ntext",ntext
        if re.match(ur".*FIR\s*/\s*CTA.*",ntext):
            print "Matches Tallin FIR"
            name='TALLIN FIR'
            points=mapper.parse_coord_str(firtxt,context='estonia')
            floor,ceiling="GND","FL195"
            space={}
            space['name']=name
            space['points']=points
            space['floor']=floor
            space['ceiling']=ceiling
            space['freqs']=[]
            space['icao']='EETT'
            space['type']='FIR'
            space['date']=date
            space['url']=fetchdata.getrawurl(url,'ee')
            spaces.append(space)            
            continue
        else:
            name=ntext.strip()
        space=dict(name=name)
        print "Name",name
        assert space['name'].count("TMA") \
            or space['name'].count("FIR")
        if space['name'].count("FIR"):
            type='FIR'            
        else:
            type="TMA"
        freqs=[]
        points=None
        floor=None
        ceiling=None
        for cand in tab.xpath(".//tr"):
            if len(cand.getchildren())!=2:
                continue
            nom,what=cand.getchildren()            
            whattxt=alltext(what)
            nomtxt=alltext(nom)
            print "nomtxt",nomtxt,"space name",space['name']
            if nomtxt.count("Lateral limits"):
                if space['name'].count("TALLINN TMA 2"):
                    points=mapper.parse_coord_str("""                
                        A circle with radius 20 NM centred on 592448N 0244957E
                        """)
                else:               
                    whattxt=whattxt.replace(
                        "then along the territory dividing line between Estonia and Russia to",
                        "- Along the common Estonian/X state boundary to " 
                        )
                    print "Fixed up",whattxt
                    points=mapper.parse_coord_str(whattxt,context='estonia')
            if nomtxt.count("Vertical limits"):
                floor,ceiling=whattxt.split(" to ")
            if nomtxt.count("Call sign"):
                callsign=whattxt.split("\n")[0]
            if nomtxt.count("freq"):
                freqs.extend(re.findall(ur"\d+\.\d+\s*MHz"))
                
        assert points and floor and ceiling
        space['points']=points
        space['type']=type
        space['floor']=floor
        space['ceiling']=ceiling
        space['freqs']=[]
        space['type']=type
        space['date']=date
        space['url']=fetchdata.getrawurl(url,'ee')
        for freq in freqs:
            space['freqs'].append((callsign,freq))
        spaces.append(space)
    return spaces
    
if __name__=='__main__':
    for space in ee_parse_tma2():
        print "Space:",space