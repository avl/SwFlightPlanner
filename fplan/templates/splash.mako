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
		<dt><a href="http://www.flygfyren.nu/community/index.php?forums/support-f%C3%B6r-webbapplikation.37/"><b><u>Forum</u></b></a></dt>
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
<big style="background-color:#ff8080">There have been problems with the Android-app-sync function the last few weeks. The problem is being worked on.</big>
</p>
-->
<p><a href="/splash/about">– Free and Open Source flight planning for VFR pilots in Sweden.</a></p>
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

<span style="font-size:150%">Check out the <u><a href="https://play.google.com/store/apps/details?id=se.flightplanner2&hl=en">SwFlightplanner Android-app!</a></u></span>
<br/><br/>
<b>News:</b><br/>
<b>Updated 2014-12-04</b> ANNOUNCEMENT: Data, in this app, for baltic states is not being actively maintained, and will be removed completely in the future.</br />
<b>Updated 2014-12-04: </b>Finnish data has now been updated from a different source. Many thanks to the user who provided this source!<br />
<b>Updated 2014-11-25: </b> Finnish was much older than the program claimed. This was due to a software bug. Baltic data is also likely older than claimed by the program.<br />
<b>Updated 2014-04-25: </b>New feature - import GPX as flight plan. Select "import track", then check "Add as flight plan".<br />
<b>Updated 2013-10-27: </b>SwFlightplanner now contains swedish soaring sectors. For sectors with undefined ceilings, the value UNL is used.<br />
<b>Updated 2013-03-16: </b><a href="www.flygfyren.nu">Flygfyren.nu</a> has agreed to host the support forum for swflightplanner! Posts have been migrated, and links updated. Thank you Flygfyren!<br />
<b>Updated 2012-11-20: </b>Norwegian obstacle information now added.<br />
<b>Updated 2012-09-09: </b>SwFlightplanner now has norwegian airspace! A big thank-you goes out to user Albin for putting in hard work to provide this and the Danish airspace data!<br />
<b>Updated 2012-06-11: </b>SwFlightplanner now uses american GFS forecasts, meaning that wind information is now available around the clock, and in all countries (at least northern hemisphere).<br />
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
