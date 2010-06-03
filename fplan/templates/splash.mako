<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
	"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html style="height:100%;margin:0;padding:0;border:none;">
<head>
	<meta http-equiv="Content-type" content="text/html; charset=UTF-8" />
	<title>Flight Planner</title>
	<meta http-equiv="Content-Language" content="en-us" />
	<link href="/style.css" rel="stylesheet" type="text/css" />
</head>

<title>
Welcome to Flightplanner
</title>

<body style="height:100%;margin:0;padding:0;border:none;">
<script type="text/javascript">
</script>

<table style="height:30%;vertical-align:middle;margin: 0 auto;">
<tr>
<td style="width:100%;text-align:center">
<h1>Welcome to Flightplanner!</h1>
</td>
</tr>
</table>
<table style="height:30%;vertical-align:middle;margin: 0 auto">
<tr>
<td style="width:45%;background:#d0ffd0;border:1px #808080 solid;padding:2%">
<div>
New users:<br/>
<u><a style="font-size:30px" href="${h.url_for(controller="mapview",action="index")}">Start using directly!</a></u><br/>
<br/>
<div style="font-size:12px;color:#808080">
Once in the system, and only if you like, you can select the menu option "profile" in the top right
corner of the screen, and create your own user name. But try the system out first, by
clicking the link above!
</div>
</div>
<br/>
</td>
<td style="width:10%;text-align:center">
Or
</td>
<td style="width:45%;background:#d0d0ff;border: 1px #808080 solid;padding:2%">
<div>
Existing users:<br/>
<form method="POST" action="${h.url_for(controller="splash",action="login")}">
Username:<input name="username" type="text" value="" /><br/>
Password:<input name="password" type="password" value="" /><br/>
<input type="submit" value="Login" name="login"/>
</form>
</div>
<br/>
</td>

</tr></table> 
</body>
</html>