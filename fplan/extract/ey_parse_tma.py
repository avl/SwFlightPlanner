#encoding=utf8
from datetime import datetime
import fplan.lib.mapper as mapper
import re
from fplan.lib.poly_cleaner import clean_up_polygon

def ey_parse_tma():
    out=[]
    
    def emit(name,coordstr,limits,type="TMA",freqs=[],date=datetime(2011,03,25)):
        ceiling,floor=limits.split("/")
        def compact(m):
            return "".join(m.groups())
        coordstr=re.sub(ur"(\d{2,3})\s*(\d{2})\s*(\d{2})",compact,coordstr)
        coordstr=re.sub(ur"NM from KNA to ","NM from 545740N 0240519E to",coordstr)
        print coordstr
        tpoints=mapper.parse_coord_str(coordstr,context='lithuania')
        f1=mapper.parse_elev(floor)
        c1=mapper.parse_elev(ceiling)
        #if c1!='-':
        #    assert c1>f1
        for points in clean_up_polygon(tpoints):
            out.append(
                dict(
                     name=name,
                     floor=floor,
                     ceiling=ceiling,
                     freqs=freqs,
                     points=points,
                     type=type
                     )
            )
    emit(name=u"Vilnius FIR",
         limits="-/GND",
         freqs=[],
         type="FIR",         
         coordstr=u"""
56 20 43N 018 30 23E - 56 04 00N 020 40 00E -
56 04 09N 021 03 52E - 
Along the common Lithuanian/X state boundary to
55 40 50N 026 37 50E - 
Along the common Lithuanian/X state boundary to
53 57 23N 023 30 54E - 
Along the common Lithuanian/X state boundary to 
54 21 48N 022 47 31E - 
Along the common Lithuanian/X state boundary to
55 17 41N 021 17 29E -
55 17 00N 020 57 00E - 56 05 43N 018 01 07E - 56 20 43N 018 30 23E         
         """)

    """
"""

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
        
    
    
    #R:    
        

    emit(name=u"EY TSA 1 (KYVIŠKĖS)",
         limits="4000 FT MSL/1700 FT MSL",
         coordstr=u"""
54 44 41N 025 31 23E - 54 43 09N 025 38 08E -
54 37 59N 025 41 53E - 54 35 16N 025 32 09E -
54 37 03N 025 26 03E - 54 44 41N 025 31 23E         
         """
         )

    emit(name=u"EY TSA 2 (ALEKSOTAS)",
         limits="4000 FT MSL/1200 FT MSL",
         coordstr=u"""
54 53 17N 023 45 47E - 54 53 45N 023 53 35E -
54 52 51N 023 57 25E - 54 49 55N 023 56 51E -
54 48 47N 023 54 15E - 54 48 42N 023 49 28E -
54 49 50N 023 46 09E - 54 53 17N 023 45 47E
         """                  
         )
    
    emit(name=u"EY TSA 5 (MIL)",
         limits="FL130/1500 FT MSL",
         coordstr=u"""
56 11 05N 023 54 13E - 55 41 43N 024 05 49E -
55 29 20N 023 26 56E - 55 54 05N 022 46 11E -
56 16 11N 023 03 46E - 56 11 05N 023 54 13E
         """                  
         )
    
    emit(name=u"EY TSA 6 (POCIŪNAI)",
         limits="FL150/FL65",
         coordstr=u"""
54 41 04N 023 52 02E - 54 42 39N 024 00 43E -
54 42 10N 024 13 28E - 54 37 23N 024 14 01E -
54 35 34N 024 09 26E - 54 33 53N 023 55 11E -
54 41 04N 023 52 02E
         """                  
         )
    
    emit(name=u"KARTENA",
         limits="FL65/GND",
         coordstr=u"""
55 55 12N 021 28 17E - 56 00 00N 021 42 17E -
56 00 00N 022 06 57E - 55 44 02N 022 09 05E -
55 35 09N 021 48 06E - 55 43 06N 021 28 42E -
55 55 12N 021 28 17E
         """                  
         )
    
    emit(name=u"PALUKNYS",
         limits="FL65/GND",
         coordstr=u"""
54 29 14N 024 54 44E -54 27 57N 024 58 51E -
54 16 51N 025 11 44E - 54 08 42N 024 45 26E -
54 24 44N 024 35 38E - 54 29 14N 024 54 44E
         """                  
         )
    
    emit(name=u"ŠEDUVA",
         limits="FL65/GND",
         coordstr=u"""
55 45 12N 023 46 22E -55 53 36N 023 52 54E -
55 44 37N 024 10 30E - 55 33 23N 024 05 50E -
55 38 34N 023 55 50E - 55 45 12N 023 46 22E
         """                  
         )
    
    if 0:      
        emit(name=u"",
         limits="",
         coordstr=u"""

         """                  
         )
    
    
    
        
    return out

if __name__=='__main__':
    for space in ey_parse_tma():
        print "space:",space
    