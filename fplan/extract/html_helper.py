def alltextlist(x):
    if x.text:
        s=[x.text]
    else:
        s=[]
    for child in x.getchildren():
        if child.tag.lower() in ['p','br']:
            s.append("\n")
        childitems=alltextlist(child)
        s.extend(childitems)
        if child.tag.lower()=="p":
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

