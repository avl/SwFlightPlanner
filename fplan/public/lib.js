

keyhandler=0;
function on_keypress(event)
{
	if (keyhandler!=0)
		return keyhandler(event);
	return false;
}


global_onload=0;
/*Helper to support multiple onload functions easily*/ 
function addLoadEvent(func) { 
	var oldonload = global_onload; 
	if (typeof global_onload != 'function') { 
	    global_onload = func; 
	} else { 
	    global_onload = function() { 
	      if (oldonload) { 
	        oldonload(); 
	      } 
	      func(); 
	    } 
	}
}
function not_enter(event)
{
	if (event.keyCode==13 || event.charCode==13)
		return false;
	return true;
}
	 
/*Belongs to base.mako but loaded here to reduce bw*/
function fixcontentsize()
{
	if (window.innerHeight>300)
	{
		var hh=document.getElementById('content').offsetTop;		
		document.getElementById('content').style.height=''+parseInt(window.innerHeight-2.1*hh)+'px';
	}
}
	 
function force_refresh_on_back_button(selfurl)
{
    var detect=document.getElementById('refreshid');
    if (detect) //either yes or no - otherwise we're on a browser where our reload-on-back trick doesn't work.
    {
        if (detect.value=='yes')
        {
		    window.location.href=selfurl;
        }
        else
        {
            detect.value='yes';
        }
    }
}


