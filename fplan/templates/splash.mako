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
<table style="height:30%;vertical-align:middle;margin: 0 auto;">
<tr>
<td style="width:100%;text-align:center">
<h1>Welcome to SwFlightPlanner (BETA)!</h1>
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

<b>Updated 2012-03-18: </b>Added some Estonian airspace information.<br />
<b>Updated 2012-03-17: </b>The NOTAM fetch script was broken recently, fixed now, but only for Sweden.<br />
<b>Updated 2011-11-01: </b>Now support for automatically calculating optimum cruise altitudes. See <a href="/splash/about"><u>"about"</u></a> and use with caution..<br />
<b>Updated 2011-10-11: </b>Support for Internet Explorer! The site is now tested using IE6, although later versions should also work.<br />
<b>Updated 2011-10-02: </b>AIP SUP 38/2011 contained some invisible white text on white background, which threw off our parser. The problem has been fixed, but a few android map downloads failed on Saturday because of this.<br />
<b>Updated 2011-08-27: </b>
New version! New features include: Automatic determination of variation (magnetic declination), a new optional advanced
aircraft performance model for more accurate fuel consumption figures, a 'forgot password' feature, and a few minor 
improvements. If there are bugs, I really do want to know! Write in the forum, send me mail! 
<br />
<b>Updated 2011-03-14: </b>Some support for Danish airspace. The data is old, however.<br />
<b>Updated 2010-10-09: </b>Support for creating complete ATS flightplans which can be copy-pasted to www.aro.lfv.se.<br />
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
