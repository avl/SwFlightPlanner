
import fplan.extract.miner as miner


def ep_parse_tma():
    pages,date=miner.parse('/_Poland_EP_ENR_2_1_en.pdf',country='ep')
    for nr,page in enumerate(pages):
        print "page",nr
        for item in page.get_by_regex(ur"[.\n]*DESIGNATION AND LATERAL[.\n]*"):
            print "  ",item
        
    
    
    
    
    
    
    
    
    
if __name__=='__main__':
    ep_parse_tma()
    
    