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
         elev=0),#TODO: Add real elev
              
]