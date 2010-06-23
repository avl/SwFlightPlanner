#encoding=utf8
import fplan.extract.fetch_notams as fetch_notams
from notam_db_update import notam_db_update_impl
from fplan.model import *
from datetime import datetime

def lines(s):
    out=[]
    for l in s.splitlines(1):
        out.append(l.strip())
    return out 

def test_notam_db_update():        
    try:    
        notam1=u"""<pre>
            AIS FIR INFORMATION           ISSUED 100610 1738   SFI008 PAGE 1(25)
            
            Test Windturbine constructed at position
            59N018E
            
            Temporary restriction area north stockholm
            100601-100701</pre>
        """
        notam_db_update_impl(notam1)
        notam2=u"""<pre>
            AIS FIR INFORMATION           ISSUED 100610 1739   SFI008 PAGE 1(25)
            
            Test Windturbine constructed at position
            59N018E
            
            Temporary restriction area north stockholm
            100601-100701

ESSA/STOCKHOLM
            A new item which has appeared
            100801-100901</pre>
        """
        notam_db_update_impl(notam2)
        
        notams=list(meta.Session.query(Notam).order_by(Notam.ordinal).all())
        #print "Loaded notams:",notams
        assert notams[0].ordinal==1
        assert notams[1].ordinal==2    
        assert notams[0].issued==datetime(2010,6,10,17,38,00)
        #print "Issued [1] = %s"%(notams[1].issued,)
        assert notams[1].issued==datetime(2010,6,10,17,39,00)
        #print "Notam 0 items: %s"%(notams[0].items,)
        assert len(notams[0].items)==2
        assert notams[0].items[0].appearnotam==1
        assert notams[0].items[0].appearline==3
        assert notams[0].items[0].category==None
        assert lines(notams[0].items[0].text)==lines("Test Windturbine constructed at position\n59N018E")
        assert notams[0].items[1].appearnotam==1
        assert notams[0].items[1].appearline==6
        assert lines(notams[0].items[1].text)==lines("Temporary restriction area north stockholm\n100601-100701")

        #print notams[1].items
        assert len(notams[1].items)==1
        assert notams[1].items[0].appearnotam==2
        assert notams[1].items[0].appearline==10
        assert notams[1].items[0].category=='ESSA/STOCKHOLM'
        assert lines(notams[1].items[0].text)==lines("A new item which has appeared\n100801-100901")
        
        notam3=u"""<pre>
            AIS FIR INFORMATION           ISSUED 100610 1739   SFI008 PAGE 1(25)
            
            Test Windturbine constructed at position
            59N018E
            
            Temporary restriction area north stockholm
            Changed!
            
ESSA/STOCKHOLM
            A new item which has appeared
            100801-100901</pre>
        """
        notam_db_update_impl(notam3)
        notams=list(meta.Session.query(Notam).order_by(Notam.ordinal).all())
        assert len(notams)==3
        last=notams[2]
        assert len(last.items)==1
        assert lines(last.items[0].text)==lines("Temporary restriction area north stockholm\nChanged!")
        assert lines(last.items[0].prev.text)==lines("Temporary restriction area north stockholm\n100601-100701")
        
        notam4=u"""<pre>
            AIS FIR INFORMATION           ISSUED 100610 1739   SFI008 PAGE 1(25)
            
            Test Windturbine constructed at position
            59N018E
                    
ESSA/STOCKHOLM
            A new item which has appeared
            100801-100901</pre>
        """
        notam_db_update_impl(notam4)
        notams=list(meta.Session.query(Notam).order_by(Notam.ordinal).all())
        assert len(notams)==4
        last=notams[-1]
        assert len(last.items)==0
        assert len(last.removeditems)==1
        assert lines(last.removeditems[0].text)==lines("Temporary restriction area north stockholm\nChanged!")
        
        
        notam5=u"""<pre>
            AIS FIR INFORMATION           ISSUED 100610 1739   SFI008 PAGE 1(25)
            
            Test Windturbine constructed at position
            59N018E
                    
ESSB/STOCKHOLM
            A new item which has appeared
            100801-100901</pre>
        """
        notam_db_update_impl(notam5)
        notams=list(meta.Session.query(Notam).order_by(Notam.ordinal).all())
        assert len(notams)==5
        last=notams[-1]
        assert len(last.items)==1
        assert len(last.removeditems)==1
        assert lines(last.items[0].text)==lines("A new item which has appeared\n100801-100901")
        assert lines(last.removeditems[0].text)==lines("A new item which has appeared\n100801-100901")
        assert last.items[0].category=="ESSB/STOCKHOLM"
        assert last.removeditems[0].category=="ESSA/STOCKHOLM"

        #Notam download where nothing had changed:    
        notam6=u"""<pre>
            AIS FIR INFORMATION           ISSUED 100610 1739   SFI008 PAGE 1(25)
            
            Test Windturbine constructed at position
            59N018E
                    
ESSB/STOCKHOLM
            A new item which has appeared
            100801-100901</pre>
        """
        notam_db_update_impl(notam6)
        notams=list(meta.Session.query(Notam).order_by(Notam.ordinal).all())
        assert len(notams)==5

        notam6b=u"""<pre>
            AIS FIR INFORMATION           ISSUED 100610 1740   SFI008 PAGE 1(25)
            
            Test Windturbine constructed at position
            59N018E
                    
ESSB/STOCKHOLM
            A new item which has appeared
            100801-100901</pre>
        """
        notam_db_update_impl(notam6b)
        notams=list(meta.Session.query(Notam).order_by(Notam.ordinal).all())
        assert len(notams)==6
        assert len(notams[-1].items)==0
        assert len(notams[-1].removeditems)==0    
    finally:
        meta.Session.rollback()

def test_on_real_data():
    notam_db_update_impl(unicode(open("./fplan/extract/notam_sample.html").read(),'latin1'))
    notam_db_update_impl(unicode(open("./fplan/extract/notam_sample2.html").read(),'latin1'))
    notam_db_update_impl(unicode(open("./fplan/extract/notam_sample3.html").read(),'latin1'))
    notam_db_update_impl(unicode(open("./fplan/extract/notam_sample4.html").read(),'latin1'))
    notam_db_update_impl(unicode(open("./fplan/extract/notam_sample5.html").read(),'latin1'))
    notams=list(meta.Session.query(Notam).order_by(Notam.ordinal).all())
    for item in notams[-1].items:
        print item
        
    
    
