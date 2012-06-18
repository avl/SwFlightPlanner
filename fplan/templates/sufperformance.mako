<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
	"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html style="height:100%;margin:0;padding:0;border:none;">


<head>
	<meta http-equiv="Content-type" content="text/html; charset=UTF-8" />
	<title>SwFlightPlanner</title>
	<meta http-equiv="Content-Language" content="en-us" />
    <link rel="shortcut icon" href="/favicon.png"/>
	<link href="/style2.css" rel="stylesheet" type="text/css" />
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

<div class="tabcontainer" style="float:left">
<div id="step1" class="tab">
<div id="step1nav1"></div>

<h2 class="centertitle">Fält och Flygplan</h2>

<table class="settingtab">
<tr>
<td class="key">Välj flygplan:</td><td><big><select onchange="calc()" id="aircraft">
<option value="SE-VOD">SE-VOD</option>
<option value="SE-VPD">SE-VPD</option>
</select></big></td></tr>

<tr id="custom1"><td class="key">Ban-nummer:</td><td><input name="custom_runway" onchange="onchangecustom()" id="custom_runway" type="text" size="5" /> (exempelvis: 16)</td></tr>
<tr id="custom2"><td class="key">Längd:</td><td><input name="custom_runway_length" onchange="onchangecustom()" id="custom_runway_length" type="text" size="5" />m (exempelvis: 500)</td></tr>
<tr id="custom3"><td class="key">Inflyttad tröskel:</td><td><input name="custom_displaced_threshold" onchange="onchangecustom()" id="custom_displaced_threshold" type="text" size="5" />m (exmpelvis: 0, eller 130)</td></tr>
<tr style="display:none" id="custom4"><td class="key">Avstånd bana-hinder:</td><td><input name="custom_obstacle_dist" onchange="onchangecustom()" id="custom_obstacle_dist" type="text" size="5" />m (ej obligatorisk)</td></tr>
<tr style="display:none" id="custom5"><td class="key">Höjd hinder:</td><td><input name="custom_obstacle_height" onchange="onchangecustom()" id="custom_obstacle_height" type="text" size="5" />m (ej obligatorisk)</td></tr>
<tr style="display:none" id="custom6"><td class="key">Tröskelhöjd:</td><td><input name="custom_threshold_height" onchange="onchangecustom()" id="custom_threshold_height" value="15" type="text" size="5" />m (minst 15m)</td></tr>
<tr style="display:none" id="custom7"><td class="key">Säkerhetsfaktor:</td><td><input name="custom_safety_factor" onchange="onchangecustom()" id="custom_safety_factor" value="43" type="text" size="5" />% (Vid landning, minst 43%)</td></tr>
<tr><td colspan="2" class="key"><span id="changefield"><button onclick="dochangefield()">&nbsp;Hämta Fältdata</button></span></td></tr>
</table>
<button onclick="unhidecustom456()">Visa Avancerade Val</button>
<div id="step1nav2"></div>

</div>


<div id="step2" class="tab" style="display:none">
<div id="step2nav1"></div>
<h2 class="centertitle">Lastning</h2>
<table class="settingtab">
<tr><td class="key">Pilotens vikt:</td><td><input name="pilot" onchange="calc()" type="text" size="4" id="pilot" value="80">kg</td></tr>
<tr><td class="key">Passagerarens vikt:</td><td><input name="pax" onchange="calc()" type="text" size="4" id="pax">kg</td></tr>
<tr><td class="key">Bakom stolarna:</td><td><input name="luggage" onchange="calc()" type="text" size="4" id="luggage">kg</td></tr>
<tr><td class="key">Bagage under knäna:</td><td><input name="knee" onchange="calc()" type="text" size="4" id="knee">kg</td></tr> 
<tr><td class="key">Bränsle vänster:</td><td><input name="leftfuel" onchange="calc()" type="text" size="4" id="leftfuel" value="30">L</td></tr>
<tr><td class="key">Bränsle höger:</td><td><input name="rightfuel" onchange="calc()" type="text" size="4" id="rightfuel" value="30">L</td></tr> 
</table>
<div id="step2nav2"></div>
</div>

<div id="step3" class="tab" style="display:none;">
<div id="step3nav1"></div>
<h2 class="centertitle">Fält-Egenskaper</h2>
<table class="settingtab">
<tr>
<td>Vind</td><td><input onchange="calc()" type="text" size="4" id="winddir" value="${c.winddir}"> grader</td><td><input onchange="calc()" type="text" size="4" id="windvel" value="${c.windvel}">knop</td></tr>

<tr><td>Temperatur</td><td><input name="temperature" onchange="calc()" type="text" size="4" id="temperature" value="${c.temp}">C</td></tr>
<tr><td>Höjd</td><td><input name="elevation" onchange="calc()" type="text" size="5" id="elevation" value="30">fot</td></tr>
<tr><td>Motlutning</td><td colspan="4"><input  name="tilt" onchange="calc()" type="text" size="5" id="tilt" value="0">%</td></tr>
<tr><td>QNH</td><td><input onchange="calc()" name="qnh" type="text" size="5" id="qnh" value="${c.qnh}">mbar</td></tr>
<tr><td>Kort gräs</td><td><input onchange="document.getElementById('longgrass').checked=false;calc()" name="shortgrass" type="checkbox" checked="1" id="shortgrass"></td></tr>
<tr><td>Långt gräs</td><td><input onchange="document.getElementById('shortgrass').checked=false;calc()" name="longgrass" type="checkbox" id="longgrass" ></td></tr>
<tr><td>Gräset är blött</td><td><input onchange="calc()" name="wetgrass" type="checkbox" id="wetgrass"></td></tr>
<tr><td>Vatten eller snöslask:</td><td><input onchange="calc()" name="slush" type="checkbox" id="slush"></td><td><input onchange="calc()" type="text" size="5" id="slushdepth" />cm</tr>
<tr><td>Tung snö (kramsnö):</td><td><input onchange="calc()" name="heavysnow" type="checkbox" id="heavysnow"></td><td><input onchange="calc()" type="text" size="5" id="snowdepth" />cm</tr>
<tr><td>Pudersnö:</td><td><input onchange="calc()" type="checkbox" name="powder" id="powder"></td><td><input onchange="calc()" type="text" size="5" id="powderdepth" />cm</tr>

<tr><td>Våt is</td><td><input onchange="document.getElementById('wetgrass').checked=false;calc()" name="ice" type="checkbox" id="ice"></td></tr>

</table>

<div id="step3nav2"></div>

</div>

</div>

<div class="tabcontainer" style="float:right">
<b>Beräkningsresultat:</b>

<div id="resultdiv">

</div>

<div id="resultimg">
</div>

</div>
</body>
</html>
