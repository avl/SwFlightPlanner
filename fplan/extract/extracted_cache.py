from fplan.extract.parse_tma import parse_all_tma

airspaces=[]
def get_airspaces():
    global airspaces
    if not airspaces:
        airspaces=parse_all_tma()
    return airspaces
    
