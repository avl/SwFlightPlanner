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
<script type="text/javascript" src="/js/jquery-1.7.2.min.js"></script>
<script type="text/javascript" src="/js/jquery-ui-1.8.21.custom.min.js"></script>
<script type="text/javascript">

	
function findPos(obj) {
	var curleft = curtop = 0;

	if (obj.offsetParent) {
		do {
			curleft += obj.offsetLeft;
			curtop += obj.offsetTop;			
		} while (obj = obj.offsetParent);
	}
	
	return [curleft,curtop];
}
last_airport_data=null;

function do_load_ad(){
	var sf=document.getElementById('tags');
	$.getJSON('${c.airport_load_url}',{name:sf.value}, function(data) {
		last_airport_data=data;
		var select = $('#runway');
		$('option', select).remove();
		var options = select.prop('options');
		$.each(data['runways'], function(index,val) {
			    options[options.length] = new Option(val.name, val.name);
				});				
	});
};

function dochangefield()
{
	var che=document.getElementById('changefield');
	che.innerHTML='<div class="ui-widget">'+
		'<label for="tags">Tags: </label>'+	
		'<input id="tags">'+
		'<button onclick="do_load_ad()">Sök</button>&nbsp;<button>Lägg till eget</button>';
	var sf=document.getElementById('tags');
	sf.focus();
	$( "#tags" ).autocomplete({			
		source: '${c.searchurl|n}'
	});
	$( "#tags" ).change(do_load_ad);
	
	
	
}
function myParseFloat(x)
{
	if (x)
		return parseFloat(x);
	return 0.0; 
}
function calc()
{
  var ac_sel=document.getElementById('aircraft');
  if (ac_sel.value=='SE-VOD')
  {
  	plane_kg=290.0;
    nominal_kg=475.0;
  }
  else
  {
    plane_kg=275.0;
    nominal_kg=450.0;
  }
  
  var runway=document.getElementById('runway').value;
  
  available_takeoff=0;
  if (runway=='16')
  {
  	available_takeoff=750;
  	available_landing=550;
  	rwyhdg=160;  
  }
  if (runway=='34')
  {
  	available_takeoff=750;
  	available_landing=750;  
  	rwyhdg=340;  
  }
  if (runway=='07')
  {
  	available_takeoff=430;
  	available_landing=430-130;  
  	rwyhdg=70;  
  }
  if (runway=='25')
  {
  	available_takeoff=430;
  	available_landing=430;  
  	rwyhdg=250;  
  }
  

  var pilot_kg=myParseFloat(document.getElementById('pilot').value);
  var pax_kg=myParseFloat(document.getElementById('pax').value);
  var luggage_kg=myParseFloat(document.getElementById('luggage').value);
  var knee_kg=myParseFloat(document.getElementById('knee').value);
  var left_fuel_kg=myParseFloat(document.getElementById('leftfuel').value)*0.73;
  var right_fuel_kg=myParseFloat(document.getElementById('rightfuel').value)*0.73;

  var tot_kg=pilot_kg+pax_kg+luggage_kg+knee_kg+left_fuel_kg+right_fuel_kg+plane_kg;
  
  var moments=126*plane_kg+163*(left_fuel_kg+right_fuel_kg)+643*(pilot_kg+pax_kg)+1023*luggage_kg+100*knee_kg;
  var center=moments/tot_kg;
  
  
  var performance_kg=tot_kg;
  if (performance_kg<nominal_kg)
    performance_kg=nominal_kg;
  var overload=performance_kg/nominal_kg;

  var temp=myParseFloat(document.getElementById('temperature').value);
  var elev=myParseFloat(document.getElementById('elevation').value);
  var tilt=myParseFloat(document.getElementById('tilt').value);
  var qnh=myParseFloat(document.getElementById('qnh').value);
  
	var L=0.0065;
	var T0=288.15;
	var g=9.80665;
	var M=0.0289644;
	var R=8.31447;        
	var alt_m=-(T0*( Math.pow( qnh/1013 , (L*R/(g*M)) )-1))/L;
	var alt=alt_m/0.3048;
	
  var eff_press_factor = 1013/qnh*((273+temp)/(273+15));
  //alert('eff density:'+eff_press_factor);
  
  var isshortgrass=document.getElementById('shortgrass').checked;
  var islonggrass=document.getElementById('longgrass').checked;
  var isslush=document.getElementById('slush').checked;
  var slushdepth=myParseFloat(document.getElementById('slushdepth').value);
  var isheavysnow=document.getElementById('heavysnow').checked;
  var snowdepth=myParseFloat(document.getElementById('snowdepth').value);
  var ispowder=document.getElementById('powder').checked;
  var powderdepth=myParseFloat(document.getElementById('powderdepth').value);
  
  var winddir=myParseFloat(document.getElementById('winddir').value);
  var windvel=myParseFloat(document.getElementById('windvel').value);
  
  var windcomp=Math.cos((winddir-rwyhdg)/(180.0/Math.PI))*windvel;
  windwhat='motvind';
  if (windcomp<0)
  	windwhat='(=medvind)';
    
  var base_landing_distance=267;
  
  if (windcomp>0)
  	base_landing_distance*=1.0-0.01*windcomp;
  if (windcomp<0)
  	base_landing_distance*=1.0-0.04*windcomp;
  	
  	
  if (eff_press_factor>1)
  	base_landing_distance*=1.0+(Math.sqrt(eff_press_factor)-1)
    
  var base_start_distance=264;
  if (isshortgrass) base_start_distance*=1.1;
  if (islonggrass) base_start_distance*=1.5;
  if (isslush)
  {
  	if (!slushdepth) {alert("Du måste skriva in slaskdjup");return;}
  	base_start_distance*=1.0+0.2*slushdepth;
  }
  if (isheavysnow)
  {
  	if (!snowdepth) {alert("Du måste skriva in snödjup");return;}
  	base_start_distance*=1.0+0.1*snowdepth;
  }
  if (ispowder)
  {
  	if (!powderdepth) {alert("Du måste skriva in pudersnödjup");return;}
  	base_start_distance*=1.0+0.05*powderdepth;
  }
  if (temp>15)
  	base_start_distance*=1.0+(temp-15)*0.01;
  	
  var effective_elev=elev+alt;
  if (elev>0)
  	base_start_distance*=1.0+(effective_elev/1000.0)*0.2;
  	
  

  if (tilt>0)
  {
  	base_start_distance*=1.0+(tilt)*0.05;
  }
  if (tilt>2 || tilt<-2)
  	alert('Varning - maximal lutning är 2%');
  if (tilt<0)
  	base_landing_distance*=1.0+(-tilt)*0.08;
 
  base_start_distance*=overload; 
	output=document.getElementById('resultdiv');
	var startcol='#ffffff';
	var landcol='#ffffff';
	if (base_start_distance>=available_takeoff)
		startcol='#ff8080';
	if (base_landing_distance>=available_landing)
		landcol='#ff8080';
	var isoverload='Nej';
	if (overload>1)
		isoverload="Ja, med "+parseInt(tot_kg-nominal_kg)+"kg ("+parseInt(100*(overload-1))+"%)";
		
	var center_color='#ffffff';
	if (center<237 || center>355.5)
		center_color='#ff8080';
	var loadcenter_str=''+parseInt(center)+'mm (mellan 237mm och 355.5mm är okay)';
		
	output.innerHTML=\
		"<table>"+
		"<tr><td></td><td>Erforderligt:</td><td>Tillgängligt:</td></tr>"+
	    "<tr><td>Start:</td><td style=\"background:"+startcol+"\">"+parseInt(base_start_distance)+"m</td><td>"+available_takeoff+"m </td></tr>"+\
	    "<tr><td>Landning:</td><td style=\"background:"+landcol+"\">"+parseInt(1.43*base_landing_distance)+"m</td><td>"+available_landing+"m </td></tr>"+
	    "</table><br/>"+
		'Tryckhöjd: '+parseInt(effective_elev)+" fot <br/>"+\
		'Vindkomposant: '+parseInt(windcomp)+'kt '+windwhat+"<br/>"+\
		'Överlast: '+isoverload+"<br/>"+
		'Tyngdpunkt: <span style="background:'+center_color+'">'+loadcenter_str+"</span>";
}
</script>
<h1>Prestanda-planering, Swedish Ultraflyers</h1>

<table>
<tr>
<td>Välj flygplan:</td><td><select id="aircraft">
<option value="SE-VOD">SE-VOD</option>
<option value="SE-VPD">SE-VPD</option>
</select></td>
<td>Fält:</td><td id="cur_field"><span id="changefield">${c.field}<button onclick="dochangefield()">Byt fält</button></span></td>
</tr>
</table>
<h2>Lastning</h2>
<table>
<tr><td>Pilotens vikt:</td><td><input type="text" size="4" id="pilot" value="80">kg</td>
<td>Passagerarens vikt:</td><td><input type="text" size="4" id="pax">kg</td></tr>
<tr><td>Bagagerum bakom stolarna:</td><td><input type="text" size="4" id="luggage">kg</td>
<td>Bagage under knäna:</td><td><input type="text" size="4" id="knee">kg</td></tr> 
<tr><td>Bränsle vänster:</td><td><input type="text" size="4" id="leftfuel" value="30">L</td> 
<td>Bränsle höger:</td><td><input type="text" size="4" id="rightfuel" value="30">L</td></tr> 

</table>
<h2>Fält</h2>
<table>
<tr>

<td>Bana</td><td>
<select id="runway">
<option value="16">16</option>
<option value="34">34</option>
<option value="07">07</option>
<option value="25">25</option>
</select>
</td></tr>
<tr>
<td>Vind</td><td><input type="text" size="4" id="winddir" value="${c.winddir}"> grader</td><td><input type="text" size="4" id="windvel" value="${c.windvel}">knop</td></tr>

<tr><td>Temperatur</td><td><input type="text" size="4" id="temperature" value="${c.temp}">C</td>
<td>Höjd</td><td><input type="text" size="5" id="elevation" value="30">fot</td></tr>
<tr><td>Motlutning</td><td colspan="4"><input type="text" size="5" id="tilt" value="0">%</td></tr>
<tr><td>QNH</td><td><input type="text" size="5" id="qnh" value="${c.qnh}">mbar</td></tr>
<tr><td>Kort gräs</td><td><input type="checkbox" id="shortgrass" onclick="document.getElementById('longgrass').checked=false;"></td>
<td>Långt gräs</td><td><input type="checkbox" id="longgrass" onclick="document.getElementById('shortgrass').checked=false;"></td></tr>
<tr><td>Vatten eller snöslask:</td><td><input type="checkbox" id="slush"></td><td>Djup:<input type="text" size="5" id="slushdepth" />cm</tr>
<tr><td>Tung snö (kramsnö):</td><td><input type="checkbox" id="heavysnow"></td><td>Djup:<input type="text" size="5" id="snowdepth" />cm</tr>
<tr><td>Pudersnö:</td><td><input type="checkbox" id="powder"></td><td>Djup:<input type="text" size="5" id="powderdepth" />cm</tr>

</table>

<button onclick="calc()">Beräkna</button>

<h2>Beräkningsresultat:</h2>

<div id="resultdiv">
Tryck på beräkna-knappen ovan!
</div>


</body>

</html>
