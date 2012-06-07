<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
	"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html>
<head>
	<meta http-equiv="Content-type" content="text/html; charset=UTF-8" />
	<title>Flight Planner</title>
	<meta http-equiv="Content-Language" content="en-us" />
	<link href="/style.css" rel="stylesheet" type="text/css" />
</head>


<body onload="global_onload()" style="overflow:hidden">
<form>
<input type="hidden" name="refreshid" id="refreshid" value="no"/>
</form>

<script type="text/javascript" src="/lib.js"></script>
<script type="text/javascript">
addLoadEvent(fixcontentsize);
</script>


<div id="page-container">

<div id="header">
<div id="left-nav">
	<dl>
		<dt id="nav-map"><a onclick="navigate_to('${h.url_for(controller="mapview",action="index")}')" href="#">Map</a></dt>
		<dt id="nav-flightplan"><a onclick="navigate_to('${h.url_for(controller="flightplan",action="index")}')" href="#">Flightplan</a></dt>
		<dt id="nav-aircraft"><a onclick="navigate_to('${h.url_for(controller="aircraft",action="index")}')" href="#">Aircraft</a></dt>
		<dt id="nav-recordings"><a onclick="navigate_to('${h.url_for(controller="recordings",action="index")}')" href="#">Triplog</a></dt>
		<dt id="nav-customsets"><a onclick="navigate_to('${h.url_for(controller="customsets",action="index")}')" href="#">Userdata</a></dt>
	</dl>
</div>
<div id="right-nav">
	<dl>
    <dt><a onclick="navigate_to('${h.url_for(controller="notam",action="index")}')" href="#">Notam</a></dt>
    <dt id="nav-profile">
    %if not h.real_user():
    ${h.get_username()|n}
    %endif
    %if h.real_user():
    <a onclick="navigate_to('${h.url_for(controller="profile",action="index")}')" href="#">Profile</a>
    %endif    
    </dt>
    %if h.real_user():
    <dt><a onclick="navigate_to('${h.url_for(controller="splash",action="logout")}')" href="#">Logout</a></dt>
    %endif
	</dl>

</div>
</div>

<div id="header-end"></div>
	
<div id="sidebar-a">
</div>
	
<div id="content">


${self.body()}

</div>
	
<div id="footer">
...
</div>

</div>



</body>
</html>
