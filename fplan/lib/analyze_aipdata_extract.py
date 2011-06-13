import json
from datetime import datetime

def run():
    f=open("data/aipdata/result.json")
    d=json.load(f)
    now=datetime.utcnow()
    f.close()
    for key,what in d.items():
        when=datetime.utcfromtimestamp(what['date'])
        print "%30s: %s - %s"%(what['what'],now-when,what['result'])


run()
