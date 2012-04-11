from fplan.model import AipHistory,meta
from fplan.model import meta,AipHistory
import pickle

def freeze(inp):
    if type(inp) in [int,float,str,unicode]:
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
    for k,v in inp:
        assert type(v) in [list,tuple]
        out[k]=[freeze(x) for x in v]
    return out

def add_aip_history(currdata):
    last=meta.Session.query(AipHistory).sorted(sa.desc_(AipHistory.aipgen)).limit(1).all()
    if len(last)!=1:
        lastgen=0
    else:
        thelast,=last
        lastgen=thelast.aipgen
    aiphist=AipHistory(lastgen+1,pickle.dumps(currdata,-1))
    meta.Session.add(aiphist)
    return lastgen+1

def deltify_sub(prev,next):
    #assert type(prev)==frozenset
    #assert type(next)==frozenset
    nextset=set(freeze(next))
    assert type(prev)==list
    out=[]
    numdelta=0
    for idx,p in enumerate(prev):
        print "Prev",idx," ",p
        pkey=freeze(p)
        if not (pkey in nextset):
            out.append(dict(idx=idx,kill=True))
            numdelta+=1
            continue
        nextset.remove(pkey)
        print "idx at end of loop",idx
    idx+=1
    for x in nextset:
        d=dict(x)
        print "Used idx for new",idx
        idx+=1
        numdelta+=1
        out.append(d)
    return out,numdelta
        
def deltify_toplevel(prevs,nexts):
    out=dict()
    numdiff=0
    
    for k,v in nexts.items():
        if not k in prevs:            
            delta,numd=deltify_sub(frozenset([]),v)
        else:
            delta,numd=deltify_sub(prevs[k],v)
        numdiff+=numd
        out[k]=delta
    return numdiff,out

def deltify(user_aipgen,cats):
    try:
        currdata=freeze_top(cats)
    except:
        return True,-1,cats
    
    theirs=meta.Session.query(AipHistory).filter(AipHistory.aipgen==user_aipgen).all()
    if len(theirs)!=1:
        #we don't know what they have now, their aipgen is unknown. Wipe all.        
        new_aipgen=add_aip_history(currdata)
        return True,new_aipgen,cats
    their,=theirs
    
    userdata=pickle.loads(their.data)
    
    num_diffs,diffs=deltify_toplevel(userdata,currdata)
    
    if num_diffs!=0:
        new_aipgen=add_aip_history(currdata)
        return False,new_aipgen,diffs
    else:
        return False,user_aipgen,diffs



