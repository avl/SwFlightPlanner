#encoding=utf8
from parse import Parser
import re
import sys
import fplan.lib.mapper as mapper


def parse_mountain_area():
    p=Parser("/AIP/ENR/ENR%201/ES_ENR_1_1_en.pdf")
    #alongborder="610213N 0114917E - 632701N 0114917E - 661457N 0141140E - 682200N 0173441E - 683923N 0183004E - 683141N 0194631E - 690945N 0202604E - 683533N 0221411E - 680424N 0233833E - 670159N 0240734E - 663602N 0240455E - "
    areas=[]
    for pagenr in xrange(p.get_num_pages()):
        #print "Processing page %d"%(pagenr,)
        page=p.parse_page_to_items(pagenr)
        lines=page.get_lines(page.get_all_items())
        allofit=" ".join(lines)
        
        allofit=allofit.replace(u"along the Swedish/Norwegian and Swedish/Finnish border to",
                                    u"Along the common X/Y state boundary to"                                
                                )
        allofit=allofit.replace(u"–","-")
        
        coordarea=re.match(ur".*Mountainous\s+area\s+of\s+Sweden.{1,10}lateral\s+limits(.*?)AIRAC.*",allofit)
        if coordarea:
            points=[]
            txt,=coordarea.groups()
            print "area:<",txt,">"
            points=mapper.parse_coord_str(txt,context="sweden")
            assert(len(points)>3)
            print "Point:",len(points)
            areas.append(dict(
                    name="Mountainous Area",
                    floor="GND",
                    ceiling="UNL",
                    points=points,
                    type="mountainarea",
                    freqs=[]))
    print len(areas)
    assert len(areas)==1
    return areas     
            
            
if __name__=='__main__':
    parse_mountain_area()
    
