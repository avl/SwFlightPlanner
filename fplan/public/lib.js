

keyhandler=0;
function on_keypress(event)
{
	if (keyhandler!=0)
		return keyhandler(event);
	return false;
}

libhook=false;
function register_foldedlink_hook(hook)
{
	libhook=hook;
}
libshownlinks=[];
function show_foldedlink(id)
{
	function complete()
	{
		var elem=document.getElementById(id);
		var links=elem.childNodes[0];
		var payload=elem.childNodes[1];
		links.style.display='none';
		payload.style.display='block';
		libshownlinks.push(id);
	}
	if (libhook!=false)
		libhook(complete);
	else
		complete();
}
function hide_foldedlinks()
{
	function hide(id)
	{
		var elem=document.getElementById(id);
		if (elem!=null)
		{
			var links=elem.childNodes[0];
			var payload=elem.childNodes[1];		
			links.style.display='block';
			payload.style.display='none';
		}
	}
	libshownlinks.map(hide);
	libshownlinks=[];
}
libdirty=false;
function getisdirty()
{
	return libdirty;
}
function setnotdirty()
{
	libdirty=false;
}
function setdirty()
{
	if (libdirty==true)
		return;
	libdirty=true;
	hide_foldedlinks();
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


