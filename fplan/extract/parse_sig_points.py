import fplan.lib.mapper as mapper
from fplan.lib.mapper import parse_coords,uprint
from parse import Parser

def parse_sig_points():
    p=Parser("/AIP/ENR/ENR 4/ES_ENR_4_4_en.pdf")
    points=[]
    for pagenr in xrange(p.get_num_pages()):
        #print "Processing page %d"%(pagenr,)
        page=p.parse_page_to_items(pagenr)
        lines=page.get_lines(page.get_all_items())
        for line in lines:
            cols=line.split()
            if len(cols)>2:
                coordstr=" ".join(cols[1:3])
                #print cols
                if len(mapper.parsecoords(coordstr))>0:
                    crd=mapper.parsecoord(coordstr)
                    print "Found %s: %s"%(cols[0],crd)
                    points.append(dict(
                        name=cols[0],
                        pos=crd))
    return points

if __name__=='__main__':
    print parse_sig_points()
    
    

