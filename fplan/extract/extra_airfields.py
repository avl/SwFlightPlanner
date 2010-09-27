#encoding=utf8
import fplan.lib.mapper as mapper
extra_airfields=[
    dict(icao="ESVF",
         name=u"Frölunda",
         pos=mapper.to_str(mapper.from_aviation_format("5927.5N01742.4E")),
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
         elev=7),
    dict(icao="EFKG",
         name=u"Kumlinge",
         pos="60.244071,20.803986",
         elev=3)
              
]

