<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
	"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html>
<head>
	<meta http-equiv="Content-type" content="text/html; charset=UTF-8" />
	<title>Flight Planner</title>
	<meta http-equiv="Content-Language" content="en-us" />
	<link href="/style.css" rel="stylesheet" type="text/css" />
</head>


<body onload="global_onload()">

<script type="text/javascript" src="/lib.js"></script>
<script type="text/javascript">
addLoadEvent(fixcontentsize);
</script>


<div id="page-container">

<div id="header">
<div id="left-nav">
	<dl>
		<dt id="nav-map"><a href="/mapview/index">Map</a></dt>
		<dt id="nav-flightplan"><a href="/flightplan/index">Flightplan</a></dt>
	</dl>

</div>
<div id="right-nav">
	<dl>
		<dt id="nav-profile"><a href="#">Profile</a></dt>
		<dt id="nav-settings"><a href="#">Settings</a></dt>
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
