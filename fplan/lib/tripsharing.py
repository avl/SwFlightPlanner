from pylons import session



def view_other(user,trip):
    session['current_trip']=trip
    session['tripuser']=user
    session.save()
def view_own(trip):
    session['current_trip']=trip
    del session['tripuser']
    session.save()
def cancel():
    if sharing_active():
        del session['current_trip']
        del session['tripuser']
        session.save()
def sharing_active():
    return 'tripuser' in session        
def tripuser():        
    return session.get('tripuser',session['user'])
    


