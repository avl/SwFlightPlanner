from pylons import session



def view_other(user,trip):
    session['current_trip']=trip
    if session['user']==user:
        #Trying to view a trip that we in fact own!
        #Don't start sharing, and cancel any existing sharing.
        if 'tripuser' in session:
            del session['tripuser']
    else:
        session['tripuser']=user
    session.save()
def view_own(trip):
    session['current_trip']=trip
    if 'tripuser' in session:
        del session['tripuser']
    session.save()
def cancel():
    if sharing_active():
        if 'current_trip' in session:
            del session['current_trip']
        if 'tripuser' in session:
            del session['tripuser']
        session.save()
def sharing_active():
    return 'tripuser' in session        
def tripuser():        
    return session.get('tripuser',session['user'])
    


