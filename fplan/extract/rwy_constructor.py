import re




def get_rwys(thresholds):
    rwys=[]
    def split(thr):
        num,side=re.match(ur"(\d{2})([LRCM]?)",thr.strip()).groups()
        return int(num),side
    def find_or_add(threshold):
        curnum,curside=split(threshold['thr'])
        if curside=='L':
            matchsides=['R']
        elif curside=='R':
            matchsides=['L']
        elif curside in ['C','M']:
            matchsides=['C','M']
        elif curside=='':
            matchsides=['',None]
        else:
            raise Exception("Internal error in rwy-analyzer")
        matchnums=[(curnum+18)%36]
        if matchnums[0]==0:
            matchnums.append(36)
        for rwy in rwys:
            if len(rwy['ends'])==2: continue
            for end in list(rwy['ends']):
                endnum,endside=split(end['thr'])                
                if endnum in matchnums and endside in matchsides:
                    rwy['ends'].append(threshold)
                    return
        rwys.append(dict(ends=[threshold]))
         
                    
                
    for threshold in thresholds:
        find_or_add(threshold)
            
    return rwys
    
