#encoding=utf8


def get_latest_notam():
    """
    Get a sequence of the last
    """
    return unicode(open("./fplan/extract/notam_sample.html").read(),'latin1')
    


