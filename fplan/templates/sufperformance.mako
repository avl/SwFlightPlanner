<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
	"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html style="height:100%;margin:0;padding:0;border:none;">


<head>
	<meta http-equiv="Content-type" content="text/html; charset=UTF-8" />
	<title>SwFlightPlanner</title>
	<meta http-equiv="Content-Language" content="en-us" />
    <link rel="shortcut icon" href="/favicon.png"/>
	<link href="/style.css" rel="stylesheet" type="text/css" />
	<link type="text/css" href="/css/smoothness/jquery-ui-1.8.21.custom.css" rel="Stylesheet" />	
</head>

<body>

<script type="text/javascript" src="/jquery.js"></script>
<script type="text/javascript" src="/json2.js"></script>
<script type="text/javascript" src="/js/jquery-1.7.2.min.js"></script>
<script type="text/javascript" src="/js/jquery-ui-1.8.21.custom.min.js"></script>
<script type="text/javascript" src="/sufperf.js"></script>

<script type="text/javascript">
last_airport_data=${c.defaddata|n};;
cur_runway=null;
searchurl='${c.searchurl|n}';
airport_load_url='${c.airport_load_url}';

</script>

<h1>Prestanda-planering, Swedish Ultraflyers</h1>
<table>
<tr>
<td style="width:50%;height=100%;overflow=auto;vertical-align:top">
<table>
<tr>
<td>Välj flygplan:</td><td><big><select onchange="calc()" id="aircraft">
<option value="SE-VOD">SE-VOD</option>
<option value="SE-VPD">SE-VPD</option>
</select></big></td></tr>

<tr id="custom1"><td>Ban-nummer:</td><td><input onchange="onchangecustom()" style="background-color:#d0ffd0" id="custom_runway" type="text" size="5" /> (exempelvis: 16)</td></tr>
<tr id="custom2"><td>Längd:</td><td><input onchange="onchangecustom()" style="background-color:#d0ffd0"id="custom_runway_length" type="text" size="5" />m (exempelvis: 500)</td></tr>
<tr id="custom3"><td>Inflyttad tröskel:</td><td><input onchange="onchangecustom()" style="background-color:#d0ffd0" id="custom_displaced_threshold" type="text" size="5" />m (exmpelvis: 0, eller 130)</td></tr>
</table>
<span id="changefield"><button onclick="dochangefield()">&nbsp;Hämta Fältdata</button></span>

<h2>Lastning</h2>
<table>
<tr><td>Pilotens vikt:</td><td><input onchange="calc()" type="text" size="4" id="pilot" value="80">kg</td>
<td>Passagerarens vikt:</td><td><input onchange="calc()" type="text" size="4" id="pax">kg</td></tr>
<tr><td>Bakom stolarna:</td><td><input onchange="calc()" type="text" size="4" id="luggage">kg</td>
<td>Bagage under knäna:</td><td><input onchange="calc()" type="text" size="4" id="knee">kg</td></tr> 
<tr><td>Bränsle vänster:</td><td><input onchange="calc()" type="text" size="4" id="leftfuel" value="30">L</td> 
<td>Bränsle höger:</td><td><input onchange="calc()" type="text" size="4" id="rightfuel" value="30">L</td></tr> 

</table>
<h2>Fält</h2>
<table>
<tr>
<td>Vind</td><td><input onchange="calc()" type="text" size="4" id="winddir" value="${c.winddir}"> grader</td><td><input onchange="calc()" type="text" size="4" id="windvel" value="${c.windvel}">knop</td></tr>

<tr><td>Temperatur</td><td><input onchange="calc()" type="text" size="4" id="temperature" value="${c.temp}">C</td>
<td>Höjd</td><td><input onchange="calc()" type="text" size="5" id="elevation" value="30">fot</td></tr>
<tr><td>Motlutning</td><td colspan="4"><input onchange="calc()" type="text" size="5" id="tilt" value="0">%</td></tr>
<tr><td>QNH</td><td><input onchange="calc()" type="text" size="5" id="qnh" value="${c.qnh}">mbar</td></tr>
<tr><td>Kort gräs</td><td><input onchange="calc()" type="checkbox" checked="1" id="shortgrass" onclick="document.getElementById('longgrass').checked=false;"></td>
<td>Långt gräs</td><td><input onchange="calc()" type="checkbox" id="longgrass" onclick="document.getElementById('shortgrass').checked=false;"></td></tr>
<tr><td>Vatten eller snöslask:</td><td><input onchange="calc()" type="checkbox" id="slush"></td><td>Djup:<input onchange="calc()" type="text" size="5" id="slushdepth" />cm</tr>
<tr><td>Tung snö (kramsnö):</td><td><input onchange="calc()" type="checkbox" id="heavysnow"></td><td>Djup:<input onchange="calc()" type="text" size="5" id="snowdepth" />cm</tr>
<tr><td>Pudersnö:</td><td><input onchange="calc()" type="checkbox" id="powder"></td><td>Djup:<input onchange="calc()" type="text" size="5" id="powderdepth" />cm</tr>
<tr><td colspan=2>OBS! På is kan stoppsträckan bli betydligt längre!</td></tr>
</table>



</td>
<td style="width:50%;height=100%;overflow=auto;vertical-align:top">
<b>Beräkningsresultat:</b><button onclick="calc()">Uppdatera</button>

<div id="resultdiv">

</div>

<div id="resultimg">
</div>

</td>
</tr>
</table>
</body>

</html>
