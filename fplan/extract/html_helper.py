def alltextlist(x):
    s=[]
    if x.tag.lower() in ['p']:
        s.append("\n")
    if x.text:
        s.append(x.text)
    if x.tag.lower() in ['br']:
        s.append("\n")        
    for child in x.getchildren():
        childitems=alltextlist(child)
        s.extend(childitems)
    if x.tag.lower() in ['p']:
        s.append("\n")
    if x.tail:    
        s.append(x.tail)
    return s
def alltext(x):
    l=alltextlist(x)
    return (" ".join(l)).strip()
def alltexts(xs):
    out=[]
    for x in xs:
        l=alltextlist(x)
        out.append((" ".join(l)).strip())
    return out

