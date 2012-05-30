#encoding=utf8
import fplan.lib.mapper as mapper
import rwy_constructor

minor_ad_charts={
        u"Frölunda":"http://www.swflightplanner.se:8080/frolunda.jpg"
                     }
extra_airfields=[
    dict(icao="ESVF",
         name=u"Frölunda",
         pos=mapper.to_str(mapper.from_aviation_format("5927.5N01742.4E")),
         runways=rwy_constructor.get_rwys(
                    [
                     dict(pos="59.45891, 17.70657",thr="16"),
                     dict(pos="59.45414, 17.71009",thr="34"),
                     dict(pos="59.45858, 17.70633",thr="07"),
                     dict(pos="59.459128, 17.71045",thr="25"),
                     ]
                    ),
         elev=30),
         
    dict(icao="ZZZZ",
         name=u"Finspång",
         pos=mapper.to_str(mapper.from_aviation_format("5843.990N01536.171E")),
         elev=164),#TODO: Add real elev
    dict(icao="ZZZZ",
         name=u"Motala/Skärstad",
         pos=mapper.to_str(mapper.from_aviation_format("5829.5N01506.2E")),
         elev=338),#TODO: Add real elev
    dict(icao="ZZZZ",
         name=u"Stegeborg",
         pos=mapper.to_str(mapper.from_aviation_format("5826.0N01636.1E")),
         elev=7)
              
]

