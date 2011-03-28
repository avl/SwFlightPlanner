#encoding=utf8
from datetime import datetime
import fplan.lib.mapper as mapper
import re
from fplan.lib.poly_cleaner import clean_up_polygon

def ey_parse_tma():
    out=[]
    
    def emit(name,coordstr,limits,freqs,date=datetime(2011,03,25)):
        ceiling,floor=limits.split("/")
        def compact(m):
            return "".join(m.groups())
        coordstr=re.sub(ur"(\d{2,3})\s*(\d{2})\s*(\d{2})",compact,coordstr)
        coordstr=re.sub(ur"NM from KNA to ","NM from 545740N 0240519E to",coordstr)
        print coordstr
        tpoints=mapper.parse_coord_str(coordstr,context='lithuania')
        for points in clean_up_polygon(tpoints):
            out.append(
                dict(
                     name=name,
                     floor=floor,
                     ceiling=ceiling,
                     freqs=freqs,
                     points=points,
                     type="TMA"
                     )
            )
    emit(name=u"KAUNAS TMA A",
         limits="FL95/1200 FT MSL",
         freqs=[('Kaunas Approach',124.200)],         
         coordstr=u"""
55 08 31N 023 34 49E - 55 11 01N 024 24 44E -
then according to arc of 18 NM from KNA to 
   54 48 14N 024 30 32E - 54 45 32N 023 36 24E -  
   then 
      according to arc of 20 NM from KNA to 
      55 08 31N 023 34 49E 
         
         """
         )
    
    emit(name=u"KAUNAS TMA B",
         limits="FL95/3000 FT MSL",
         freqs=[('Kaunas Approach',124.200)],         
         coordstr=u"""
55 17 17N 023 30 05E - 55 10 37N 0243903E -
54 48 02N 024 41 20E - 54 41 43N 0242506E -
54 42 39N 024 00 43E - 54 37 30N 0233253E -
54 45 23N 023 22 19E - 55 01 19N 0231617E -
55 17 17N 023 30 05E 
         """
         )
    
    emit(name=u"KAUNAS TMA C",
         limits="FL95/FL65",
         freqs=[('Kaunas Approach',124.200)],         
         coordstr=u"""
55 21 39N 023 16 25E - 55 20 40N 024 38 13E - 
55 10 37N 024 39 03E - 55 17 17N 023 30 05E - 
55 01 19N 023 16 17E - 54 45 23N 023 22 19E - 
54 37 30N 023 32 53E - 54 42 39N 024 00 43E - 
54 41 43N 024 25 06E - 54 35 34N 024 09 26E - 
54 30 12N 023 25 06E - 54 42 48N 023 08 10E - 
55 05 59N 023 02 07E - 55 21 39N 023 16 25E - 
         
         """
         )
    
    emit(name=u"PALANGA TMA A",
         limits="FL95/800 FT MSL",
         freqs=[('Palanga Approach',124.300)],         
         coordstr=u"""
56 09 15N 021 13 40E - 56 07 32N 021 27 21E -
55 41 42N 021 17 07E - 55 46 12N 020 41 00E -
56 04 02N 020 44 52E - Along
the common Latvian/Lithuanian state boundary to
56 09 15N 021 13 40E         
         """
         )
    
    emit(name=u"PALANGA TMA B",
         limits="FL95/2000 FT MSL",
         freqs=[('Palanga Approach',124.300)],         
         coordstr=u"""
56 18 26N 021 33 29E - 55 56 07N 021 54 34E -
55 38 47N 021 38 34E - 55 39 30N 020 31 33E -
55 53 52N 020 19 13E - 56 05 25N 020 29 44E -
56 04 00N 020 40 00E - 56 04 02N 020 44 52E -
55 46 12N 020 41 00E - 55 41 42N 021 17 07E -
56 07 32N 021 27 21E - 56 09 15N 021 13 40E -
Along the common Latvian/
Lithuanian state boundary to 56 18 26N 021 33 29E         
         """
         )
    emit(name=u"PALANGA TMA C",
         limits="FL95/FL65",
         freqs=[('Palanga Approach',124.300)],         
         coordstr=u"""
56 22 11N 021 50 56E - 55 53 54N 022 15 15E -
55 33 35N 021 55 20E - 55 34 28N 020 14 34E -
55 48 35N 020 01 21E - 56 07 36N 020 13 37E -
56 05 25N 020 29 44E - 55 53 52N 020 19 13E -
55 39 30N 020 31 33E - 55 38 47N 021 38 34E -
55 56 07N 021 54 34E - 56 18 26N 021 33 29E -
Along the common Latvian/
Lithuanian state boundary to 56 22 11N 021 50 56E
         """
         )
    
    emit(name=u"ŠIAULIAI TMA",
         limits="FL95/1500 FT MSL",
         freqs=[(u'Šiauliai Tower',120.400)],         
         coordstr=u"""
56 11 05N 023 54 13E - 55 41 43N 024 05 49E -
55 29 20N 023 26 56E - 55 54 05N 022 46 11E -
56 16 11N 023 03 46E - 56 11 05N 023 54 13E
         """
         )
    
    emit(name=u"VILNIUS TMA A",
         limits="FL95/1700 FT MSL",
         freqs=[('Vilnius Approach',120.700)],         
         coordstr=u"""
54 56 33N 024 58 22E - 54 56 02N 025 37 15E -
54 51 33N 025 47 05E - 
Along the common Belarus/Lithuanian state
boundary to 54 15 48N 025 13 46E - 54 29 03N
024 48 07E - 54 56 33N 024 58 22E
         """
         )
        
    emit(name=u"VILNIUS TMA B",
         limits="FL95/3000 FT MSL",
         freqs=[('Vilnius Approach',120.700)],         
         coordstr=u"""
55 10 37N 024 39 03E - 55 13 13N 025 40 59E -
54 51 33N 025 47 05E - 54 56 02N 025 37 15E -
54 56 33N 024 58 22E - 54 29 03N 024 48 07E -
54 15 48N 025 13 46E - 
Along the common Belarus/Lithuanian state
boundary to 54 07 04N 024 46 24E - 54 41 43N
024 25 06E - 54 48 02N 024 41 20E - 55 10 37N
024 39 03E
         """
         )
        
    emit(name=u"VILNIUS TMA C",
         limits="FL95/FL65",
         freqs=[('Vilnius Approach',120.700)],         
         coordstr=u"""
55 20 40N 024 38 13E - 55 28 47N 024 58 40E -
55 27 25N 025 36 53E - 55 13 13N 025 40 59E -
55 10 37N 024 39 03E - 55 20 40N 024 38 13E
         """
         )

    emit(name=u"VILNIUS TMA D",
         limits="FL95/FL65",
         freqs=[('Vilnius Approach',120.700)],         
         coordstr=u"""
54 41 43N 024 25 06E - 54 07 04N 024 46 24E -
54 09 25N 024 24 32E - 54 35 34N 024 09 26E -
54 41 43N 024 25 06E
         """
         )
        
        
        
        
    return out

if __name__=='__main__':
    for space in ey_parse_tma():
        print "space:",space
    