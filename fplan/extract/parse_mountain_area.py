#encoding=utf8
from parse import Parser
import re
import sys
import fplan.lib.mapper as mapper


def parse_mountain_area():
    p=Parser("/AIP/ENR/ENR%201/ES_ENR_1_1_en.pdf")
    alongborder="610213N 0114917E - 632701N 0114917E - 661457N 0141140E - 682200N 0173441E - 683923N 0183004E - 683141N 0194631E - 690945N 0202604E - 683533N 0221411E - 680424N 0233833E - 670159N 0240734E - 663602N 0240455E - "
    areas=[]
    for pagenr in xrange(p.get_num_pages()):
        #print "Processing page %d"%(pagenr,)
        page=p.parse_page_to_items(pagenr)
        lines=page.get_lines(page.get_all_items())
        allofit=" ".join(lines)
        
        allofit=allofit.replace("along the Swedish/Norwegian and Swedish/Finnish border to",alongborder)
        allofit=allofit.replace(u"–","-")
        #print allofit
        coordarea=re.match(r".*Mountainous\s+area\s+of\s+Sweden.{1,10}lateral\s+limits.*?((?:\d+N\s*\d+E\s*-\s*)+).*",allofit)
        if coordarea:
            points=[]
            for lat,lon in re.findall(r"(\d+N)\s*(\d+E)",coordarea.groups()[0]):
                points.append(mapper.parse_coords(lat,lon))
            assert(len(points)>3)
            print "Point:",len(points)
            areas.append(dict(
                    name="Mountainous Area",
                    floor="GND",
                    ceiling="UNL",
                    points=points,
                    type="mountainarea",
                    freqs=[]))
    assert len(areas)==1
    return areas     
            
            
if __name__=='__main__':
    parse_mountain_area()
    
