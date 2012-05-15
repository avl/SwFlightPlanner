from fplan.model import meta,AipHistory
import md5
from datetime import datetime,timedelta
import pickle
import traceback
from copy import deepcopy

def freeze(inp):
    if inp==None:
        return inp
    if type(inp) in [int,float,str,unicode,frozenset,datetime]:
        return inp
    if type(inp)==dict:
        return frozenset([(k,freeze(v)) for k,v in inp.items()])
    if type(inp)==list:
        return tuple([freeze(x) for x in inp])
    if type(inp)==set:
        return frozenset(inp)
    if type(inp)==tuple:
        return tuple(freeze(x) for x in inp)
    print "Type:",type(inp),repr(inp)
    assert 0
def freeze_top(inp):
    out=dict()
    for k,v in inp.items():
        assert type(v) in [list,tuple]
        out[k]=[freeze(x) for x in v]
    return out

def add_aip_history(currdata):    
    bindata=pickle.dumps(currdata,-1)
    new_aipgen=md5.md5(bindata).hexdigest()
    hits=meta.Session.query(AipHistory).filter(AipHistory.aipgen==new_aipgen).all()
    if len(hits):
        return new_aipgen
    
    meta.Session.query(AipHistory).filter(AipHistory.when<(datetime.utcnow()-timedelta(7))).delete()
    aiphist=AipHistory(new_aipgen,datetime.utcnow(),bindata)
    meta.Session.add(aiphist)
    return new_aipgen

def deltify_sub(prev,next):
    #assert type(prev)==frozenset
    #assert type(next)==frozenset
    nextset=set(freeze(next))
    #print "Prev:",repr(prev)
    assert type(prev)==list
    out=[]
    numdelta=0
    killed=set()
    newcurr=[]
    for idx,p in enumerate(prev):
        #print "Prev",idx," ",p
        pkey=freeze(p)
        if not (pkey in nextset):
            out.append(dict(idx=idx,kill=True))
            killed.add(idx)
            numdelta+=1
            continue
        nextset.remove(pkey)
        #print "idx at end of loop",idx
        newcurr.append(p)
    for x in nextset:
        d=dict(x)
        numdelta+=1
        out.append(d)
        newcurr.append(d)
    newcurr.sort(key=lambda x:x['name'].encode('utf8','ignore'))
    return out,numdelta,newcurr
        
def deltify_toplevel(prevs,nexts):
    out=dict()
    numdiff=0
    newcurr=dict()
    for k,v in nexts.items():
        if not k in prevs:            
            delta,numd,nc=deltify_sub([],v)
        else:
            delta,numd,nc=deltify_sub(prevs[k],v)
        numdiff+=numd
        out[k]=delta
        newcurr[k]=nc
    return numdiff,out,newcurr

def mkcksum(newdata):
    m=md5.md5()
    for k in sorted(newdata):
        for v in newdata[k]:
            #print "Checksumming",v['name']
            m.update(v['name'].encode('utf8','ignore'))
    return m.hexdigest()

def sortit(cats):
    for k in cats:
        cats[k].sort(key=lambda x:x['name'].encode('utf8','ignore'))
                
def deltify(user_aipgen,cats):
    try:
        currdata=freeze_top(cats)
    except Exception:
        print traceback.format_exc()
        cats=deepcopy(cats)        
        sortit(cats)
        return True,"",cats,mkcksum(cats)
    theirs=[]
    if user_aipgen!="":
        theirs=meta.Session.query(AipHistory).filter(AipHistory.aipgen==user_aipgen).all()
    if len(theirs)!=1:
        #we don't know what they have now, their aipgen is unknown. Wipe all.
        cats=deepcopy(cats)        
        sortit(cats)
        new_aipgen=add_aip_history(cats)
        return True,new_aipgen,cats,mkcksum(cats)
    their,=theirs
    
    userdata=pickle.loads(their.data)
    
    num_diffs,diffs,newcurrdata=deltify_toplevel(userdata,currdata)
    
    if num_diffs!=0:
        new_aipgen=add_aip_history(newcurrdata)
        return False,new_aipgen,diffs,mkcksum(newcurrdata)
    else:
        return False,user_aipgen,diffs,mkcksum(newcurrdata)



