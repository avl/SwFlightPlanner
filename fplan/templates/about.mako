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
<a href="/"><u>Back to start page</u></a>
<table style="height:15%;vertical-align:middle;margin: 0 auto;">
<tr>
<td style="width:100%;text-align:center">
<h1>Flightplanner</h1>
</td>
</tr>
</table>
<table style="height:80%;vertical-align:middle;margin: 0 auto">
<tr>
<td style="width:800px;text-align:left;background:#d0d0ff;border: 1px #808080 solid;padding:2%">

<h2>Who are you?</h2>
My name is Anders Musikka, and I am an enthusiast pilot and programmer.
<br/>
<br/>

<h2>What is this?</h2>
swflightplanner.se is a website to help plan VFR-flights in Sweden (with some support for Finland).
<br/>
<br/>

<h2>Which browsers does it support?</h2>
Firefox 3 and Google Chrome both work. Internet Explorer does, unfortunately, not work for the moment. 

Chrome is free and is easy to download and install: <a href="http://www.google.com/chrome/">Download it now!</a>.
<br/>
<br/>

<h2>What does it cost?</h2>
swflightplanner.se is free for any use. It is open source, and the source code can be found at git://github.com/avl/SwFlightPlanner.git (use the open source tool git to download). I will keep this server running as long as bandwidth-costs do not become excessive.   
<br/>
<br/>
<h2>Is this site reliable?</h2>
Short answer: No.<br/>
Long answer: <a href="#" onclick="document.getElementById('reliable').style.display='block'"><u>Press here!</u></a> 
<div id="reliable" style="display:none">
<p style="font-size:14px">
The airspace data presented by this site is automatically parsed from the PDF-format AIP-documents published by LFV. This parsing process may very well go wrong, in which case the airspace definitions
on the site will be wrong. I feel it is mostly correct, but comparison with an up-to-date map is advised. Also, note that I live in Stockholm, which means I am more likely to find problems with 
airspace definitions near Stockholm. Testers from other parts of the country are most welcome.
</p>
<p>
Note that there is one aspect in which the airspace data is known to be incorrect. The airspace definitions sometimes specify that an airspace follows a nation border. These airspaces are approximated, instead of faithfully following the border. Also, the no-mans-land between Finland and Russia is missing entirely in this program. Also, all Danish airspaces, even those very close to or overlapping Swedish territory, are missing entirely. Yet another limitation is that only the coordinates of holding points are given, not how the holding pattern should be aligned with that point, or if it's a left-hand or right-hand pattern. Also, some holding points are missing. Entry/exit-points to CTRs are wrong for some airports. Always cross-check using the official VAC (Visual Approach Chart).
</p>
<p>
TRA, "Temporary Reserved Airspace", are not present in this application. At time of writing (2011-02-26), these were all above FL095, where clearance is always needed anyway. 
</p>
<p style="font-size:14px">
The software that runs this site has not been tested rigorously (this is an enthusiast project after all). I feel that it usually works as intended. However, as a professional software
engineer with experience in writing and testing high quality software, I fully appreciate that it is has not been tested nearly enough to have caught even the most severe bugs. Use with caution,
and always ask yourself if the data presented by the program is reasonable.   
</p>
<p>
A further limitation is that the weather data is only valid for Sweden. Pressing the "fetch winds" button may give strange results for Finland or Norway.
</p>
<p>
Swflightplanner does calculate times for crossing FIR boundaries, but this routine
only works if you cross at most one FIR-boundary per leg.
</p>
<p>
Geomagnetic database only contains information up to year 2015. Any trips planned after this will
use geomagnetic information valid for 2015.
</p>
</div>
<br/>
<br/>
<h2>Do you want help?</h2>
I thought you'd never ask! I'm more than happy to receive bug reports, both about the software and about the airspace/map/terrain-data! See Contact information below. Developers who wish to experiment with the codebase are also welcome. Lastly, 
I am also very interested in sharing airspace data.  
<br/>
<br/>
<h2>What's with the name?</h2>
I felt that a modern software project should have a name that does not give any hits on google, except hits related to the project. At time of starting the project, the 
word swflightplanner did not give any hits on google. Sw stands for Sweden. I am aware that this name might not stand the test of time, especially since support for Finland has already been added...   
<br/>
<br/>
<h2>Where does the data come from?</h2>
The airspace data (which only covers Sweden and Finland in detail, and with some Danish data) and NOTAMs (which only cover Sweden) are from LFV and Finavia. The basic map is from openstreetmap.org. The terrain elevation data is from NASA.
Magnetic variation/declination data is from "The World Magnetic Model" by National Geophysical Data Center.<br/>

The airspace data was last downloaded from LFV/Finavia at ${c.aipupdate.strftime("%Y-%m-%d %H:%M:%S")} UTC. <br/>
The maps were last updated with this airspace data ${c.mapupdate.strftime("%Y-%m-%d %H:%M:%S")} UTC. 
<br/>
<br/>
<h2>Contact information</h2>
You can contact me at anders.musikka@gmail.com.
<br/>
<br/>
<h2>Why is a site which only works for Sweden written entirely in English?</h2>
Most Swedes know English fairly well, and the site could be of use to visiting pilots who don't speak Swedish. Support for multiple languages may come one day, but it is extra work that was deemed of secondary importance.
Also, the software running the site could in principle support a larger area, if airspace data were available. 
<br/>
<br/>
<h2>How reliable is the optimization function?</h2>
The program contains a function to help select good cruising altitudes.
<br/>
<br/>
This is only available if the "advanced performance model" has been selected in
the aircraft parameters. The reason for not making it available for the simpler
model, is that typically, the difference in economy between different altitudes
is rather small, and trying to find an optimal altitude without knowing how
aircraft performance varies with altitude, is therefore not very reasonable.
<br/>
<br/>
The function will fetch wind information for the altitudes 2000', FL50 and FL100,
and will then use Dijkstra's path-finding algorithm to find the optimum altitude
for each leg. You can choose to optimize for fuel economy (least fuel spent to
destination) and time (getting there quickest). 
<br/>
<br/>
To use the function, you need to figure out a few performance parameters for your
aircraft. All of the information required is in the Pilot Operating Handbook of
typical Piper PA28:s and Cessna 172:s.
<br/>
<br/>

Some limitations of this function:
<ul>

<li>It finds the wind at the midpoint of each leg, and uses this for the entire leg.</li>

<li>It uses the wind at the cruise altitude of each leg, so it does not take into account
that the climb up to cruise altitude will pass through other wind layers.</li>

<li>It is dependent upon having wind information, and this program only has wind
information for Sweden. Also, the wind is only available when the "LHP" (Low Altitude
Forecast) is available from LFV; and it is always just the current prognosis that is used.</li>

<li>
To make really optimal routes, power settings and speeds should be varied 
along the route depending on wind. This would require an even more detailed 
performance model, to the point that validating it way beyond the reach of 
most enthusiasts (such as myself).
</li> 
</ul>


</td>
</tr></table>
Updated 2011-10-27.
<a href="/"><u>Back to start page</u></a> 
</body>
</html>
