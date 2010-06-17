import re
from difflib import Differ,SequenceMatcher

def parse_notam(html):
    return "\n".join(pre for pre in re.findall(u"<pre>(.*?)</pre>",html,re.DOTALL))

def diff_notam(a,b):
    print "Diffing a,b: \n%s\n--------\n%s"%(a[:100],b[:100])
    seq = SequenceMatcher(lambda x: x.isspace(),a.splitlines(1),b.splitlines(1))
    for opcode in seq.get_opcodes():
        print "op",opcode

if __name__=='__main__':
    d1=parse_notam(unicode(open("./fplan/extract/notam_sample.html").read(),'latin1'))
    d2=parse_notam(unicode(open("./fplan/extract/notam_sample2.html").read(),'latin1'))
    diff_notam(d1,d2)


