<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
	"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html style="height:100%;margin:0;padding:0;border:none;">

<head>
	<meta http-equiv="Content-type" content="text/html; charset=UTF-8" />
	<title>SwFlightPlanner</title>
	<meta http-equiv="Content-Language" content="en-us" />
    <link rel="shortcut icon" href="/favicon.png"/>
	<link href="/style.css" rel="stylesheet" type="text/css" />
</head>

<body style="height:100%;margin:0;padding:0;border:none;">

<div id="left-nav">
	<dl>
		<dt><a href="http://swflightplanner.se:8080/phpBB3"><b><u>Forum</u></b></a></dt>
		<dt><a href="/splash/about"><b><u>About/FAQ</u></b></a></dt>
	</dl>
</div>
<table>
<tr><td>&nbsp;</td>
</tr>
</table>
<table style="height:25%;vertical-align:middle;margin: 0 auto;">
<tr>
<td style="width:100%;text-align:center">
<p>Welcome to</p>
<table>
<tr><td>
<img src="/bigicon.png" />
</td>
<td>&nbsp;</td>
<td>
<h1>SWFlightplanner</h1>
</td></tr>
</table>
<!--
<p>
<big style="background-color:#ff8080">Still some problems when zooming in on map,<br/> problem expected to be completely resolved<br/> by early morning 31st of May.</big>
</p>
-->
<p><a href="/splash/about">– Free flight planning for VFR pilots in Sweden.</a></p>
%if c.browserwarningheader:
<div style="font-size:20px;border-width:1px    ">${c.browserwarningheader|n}</div>
<div style="font-size:15px;">${c.browserwarning|n}</div>
%endif
</td>
</tr>
</table>
<table style="height:30%;vertical-align:middle;margin: 0 auto">
<tr>
<td style="width:45%;background:#d0ffd0;border:1px #808080 solid;padding:2%">
<div>
New users:<br />
<u><a style="font-size:30px" href="${h.url_for(controller="mapview",action="index")}">Start using immediately!</a></u><br />
<br />
<div style="font-size:12px;color:#808080">
Once in the system, and only if you like, you can select the menu option "Create User" in the top right
corner of the screen, and create your own user name. But try the system out first, by
clicking the link above!
</div>
</div>
<br />
</td>
<td style="width:10%;text-align:center">
Or
</td>
<td style="width:45%;background:#d0d0ff;border: 1px #808080 solid;padding:2%">
<div>
Existing users:<br />
<form method="post" action="${h.url_for(controller="splash",action="login")}">
Username:<input name="username" title="Your username, which could be your email address or some arbitrary name: it's what you chose when registering." type="text" value="" /><br />
Password:<input name="password" title="The password you entered when you registered this user." type="password" value="" /><br />
%if c.expl:
<div style="background:#ffc0c0">
${c.expl}
</div>
%endif
<input type="submit" value="Login" name="login"/>
<input type="submit" value="Forgot Password" name="forgot"/>
</form>
</div>
<br />
</td>

</tr></table>


<table style="height:30%;margin: 0 auto">
<tr>
<td style="width:75%;text-align:center;padding:2%;font-size:12px">

<span style="font-size:150%">Check out the <u><a href="https://play.google.com/store/apps/details?id=se.flightplanner&hl=en">SwFlightplanner Android-app!</a></u></span>
<br/><br/>
<b>News:</b><br/>
<b>Problem 2012-05-30: </b>All map information except Swedish aerodromes and their control zones were lost. The problem occurred ca 11:45Z, and was fixed 19:27Z, with problems when zooming in far on main map expected to persist until early morning 2012-05-31. Android app only affected if synced between 11:45Z and 19:27Z..<br />
<b>Updated 2012-05-10: </b>A larger map. The map now includes all of Europe and a bit more. <b>Airspace data is still only for Sweden and some of its neighbors!</b><br />
<b>Updated 2012-04-13: </b>TAF and METAR now shown when clicking on airfields (in the right margin).<br />
<b>Updated 2012-03-18: </b>Added some Estonian airspace information.<br />
<b>Updated 2010-08-25: </b>Airport data graciously provided by <a href="http://www.flygkartan.se/">www.flygkartan.se</a> -
the place to find and review airports in Sweden.<br />
<br />
This site uses <a href="http://en.wikipedia.org/wiki/HTTP_cookie">cookies</a> to store <a href="http://en.wikipedia.org/wiki/Unique_identifier">unique</a> session identifiers.<br />
<a href="/splash/about"><u>About this site</u></a>.<br/>
<div style="font-size:10px">${c.mem}M free</div> 
</td>
</tr></table> 
 
</body>
</html>
