<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
	"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html>
<head>
	<meta http-equiv="Content-type" content="text/html; charset=UTF-8" />
	<title>Flight Planner</title>
	<meta http-equiv="Content-Language" content="en-us" />
	<link href="/style.css" rel="stylesheet" type="text/css" />
</head>


<body>
<a style="color:#ff0000;font-size:12px" href="${h.url_for(controller="notam",action="index")}">&lt;- Back</a>
<pre>
%for line in c.startlines:
${line}
%endfor
</pre>
<a style="color:#ff0000;font-size:12px" href="${h.url_for(controller="notam",action="index")}">&lt;- Back</a>
<pre id="notam" style="background:#00ff00">
%for line in c.midlines:
${line}
%endfor
</pre>
<a style="color:#ff0000;font-size:12px" href="${h.url_for(controller="notam",action="index")}">&lt;- Back</a>
<pre>
%for line in c.endlines:
${line}
%endfor
</pre>










</body>

</html>

