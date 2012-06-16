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
<script type="text/javascript">

/*
JSON.stringify(your_object, null, 2);

To convert a JSON string to a JS object, use JSON.parse:

var your_object = JSON.parse(json_text);

*/

$(document).ready(calc)

function myParseFloat(x)
{
	if (x)
		return parseFloat(x);
	return 0.0; 
}

function hide_custom()
{
	$('#custom1')[0].style.display='none';
	$('#custom2')[0].style.display='none';
	$('#custom3')[0].style.display='none';
}
function show_custom()
{	
	hide_change_ad('Eget');
	$('#custom1')[0].style.display='table-row';
	$('#custom2')[0].style.display='table-row';
	$('#custom3')[0].style.display='table-row';
	$('#custom_runway')[0].focus();	
	onchangecustom();
}

function add_own()
{
	show_custom();
}
	
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
last_airport_data={"runways": [{"rwyhdg": 159.40875420296877, "available_landing": 567.6524938370329, "available_takeoff": 567.6524938370329, "name": "16"}, {"rwyhdg": 339.4117857811595, "available_landing": 567.6524938370329, "available_takeoff": 567.6524938370329, "name": "34"}, {"rwyhdg": 75.35455789727928, "available_landing": 241.48423673047128, "available_takeoff": 241.48423673047128, "name": "07"}, {"rwyhdg": 255.358106306855, "available_landing": 241.48423673047128, "available_takeoff": 241.48423673047128, "name": "25"}], "physical": [[{"pos": "59.45891, 17.70657", "name": "16"}, {"pos": "59.45414, 17.71009", "name": "34"}], [{"pos": "59.45858, 17.70633", "name": "07"}, {"pos": "59.459128, 17.71045", "name": "25"}]]}

function hide_change_ad(newname)
{
	$('#tags').autocomplete('destroy');
	var che=document.getElementById('changefield');
	che.innerHTML=''+newname+'<button onclick="dochangefield()">Byt fält</button>';
	hide_custom();

}
function update_runway_selector()
{
	var select = $('#runway');
	$('option', select).remove();
	var options = select.prop('options');
	$.each(last_airport_data['runways'], function(index,val) {
		    options[options.length] = new Option(val.name, val.name);
			});			

}
function do_load_ad(){
	var sf=document.getElementById('tags');
	$.getJSON('${c.airport_load_url}',{name:sf.value}, function(data) {
		last_airport_data=data;
		update_runway_selector();
		calc();
				
	});
	hide_change_ad(sf.value);

};
function onchangecustom()
{
	var decadeg=$('#custom_runway')[0].value;
	last_airport_data={
		runways:[{
				name:decadeg,
				rwyhdg:myParseFloat(decadeg)*10,
				available_takeoff:myParseFloat($('#custom_takeoff_length')[0].value),
				available_landing:myParseFloat($('#custom_landing_length')[0].value)
				}		
			]
	}
	
	update_runway_selector();
	calc();
  	    	  
}
function get_runway(runwayname)
{
	for(var i=0;i<last_airport_data.runways.length;++i)
	{
		rwy=last_airport_data.runways[i];
		if (rwy.name==runwayname)
			return rwy;
	}
	return null;
}
function click_search()
{
	var sf=document.getElementById('tags');
  	 $.getJSON('${c.searchurl}',{term:sf.value}, function(data) {
   		if (data==null || data.length==0)
   		{ 
   			alert('Finns ingen flygplats med det namnet i programmets databas. Använd knappen "Lägg till eget".');
   			return;
   		}
   		else
   		{
   			sf.value=data[0];
   		}
   		do_load_ad();
   	 });
}
function dochangefield()
{
	var che=document.getElementById('changefield');
	che.innerHTML='<div class="ui-widget">'+
		'<label for="tags">Fältets namn:</label>'+	
		'<input id="tags">'+
		'<button onclick="click_search()">Välj</button>&nbsp;eller <button onclick="add_own()">Lägg till eget</button>';
	var sf=document.getElementById('tags');
	sf.focus();
	$( "#tags" ).autocomplete({			
		source: '${c.searchurl|n}'
	});
	$( "#tags" ).keypress(function(e){
      if(e.which == 13 || e.which==9){
      	click_search();
       }
      });
	
	
	
	
}

function myalert(msg)
{
    imgout=document.getElementById('resultimg');
    imgout.innerHTML="";    
	output=document.getElementById('resultdiv');
	output.innerHTML="<div style=\"background-color:#ffc000\"><big>"+msg+"</big></div>";

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
  available_landing=0;
  
  if (last_airport_data!=null)
  {
      rwy=get_runway(runway);
  	  available_takeoff=rwy.available_takeoff;
  	  available_landing=rwy.available_landing;
  	  rwyhdg=rwy.rwyhdg;
  }
  else
  {
	  if (runway=='16')
	  {
	  	available_takeoff=550;
	  	available_landing=550;
	  	rwyhdg=160;  
	  }
	  if (runway=='34')
	  {
	  	available_takeoff=550;
	  	available_landing=550;  
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
  
  var tot_kg_dry=pilot_kg+pax_kg+luggage_kg+knee_kg+plane_kg;
  var moments_dry=126*plane_kg+643*(pilot_kg+pax_kg)+1023*luggage_kg+100*knee_kg;
  var center_dry=moments_dry/tot_kg_dry;
  
  
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
  var windside=Math.sin((winddir-rwyhdg)/(180.0/Math.PI))*windvel;
  windwhat='motvind';
  if (windcomp<0)
  	windwhat='medvind';
  var windleftright='';
  if (windside<-1)
  	windleftright='(vänster)';
  if (windside>1)
  	windleftright='(höger)';
  
  
  //var clock=parseInt(Math.floor(((winddir-rwyhdg)/(360/12))+0.5));
  //if (clock<0) clock+=12;
  //if (clock==0) clock=12;
  
  	
  	
    
  
  var base_landing_distance=267;
  var orig_landing_distance=267;
  var landing_roll=152;
  
  if (windcomp>0)
  	base_landing_distance*=1.0-0.01*windcomp;
  if (windcomp<0)
  	base_landing_distance*=1.0-0.04*windcomp;
  	
  if (eff_press_factor>1)
  	base_landing_distance*=1.0+(Math.sqrt(eff_press_factor)-1)
    
  var base_start_distance=264;
  var orig_start_distance=base_start_distance;
  var start_roll=86;
  
  if (isshortgrass) base_start_distance*=1.1;
  if (islonggrass) base_start_distance*=1.5;
  if (isslush)
  {
  	if (!slushdepth) 
  		{myalert("Du måste skriva in slaskdjup");return;}
  	base_start_distance*=1.0+0.2*slushdepth;
  }
  if (isheavysnow)
  {
  	if (!snowdepth) {myalert("Du måste skriva in snödjup");return;}
  	base_start_distance*=1.0+0.1*snowdepth;
  }
  if (ispowder)
  {
  	if (!powderdepth) {myalert("Du måste skriva in pudersnödjup");return;}
  	base_start_distance*=1.0+0.05*powderdepth;
  }
  if (temp>15)
  	base_start_distance*=1.0+(temp-15)*0.01;
  	
  var effective_elev=elev+alt;
  if (effective_elev>0)
  	base_start_distance*=1.0+(effective_elev/1000.0)*0.2;
  	
  

  if (tilt>0)
  {
  	base_start_distance*=1.0+(tilt)*0.05;
  }
  if (tilt>2 || tilt<-2)
  {
  	myalert('Varning - maximal lutning är 2%');
  	return;
  }
  if (tilt<0)
  	base_landing_distance*=1.0+(-tilt)*0.08;
 
  base_start_distance*=overload; 
  base_landing_distance*=overload;
  
  
  start_roll*=(base_start_distance/orig_start_distance);
  landing_roll*=(base_landing_distance/orig_landing_distance);
  
  

    imgout=document.getElementById('resultimg');
    

	output=document.getElementById('resultdiv');
	var startcol='#ffffff';
	var landcol='#ffffff';
	if (base_start_distance>=available_takeoff)
		startcol='#ff8080';
	if (1.43*base_landing_distance>=available_landing)
		landcol='#ff8080';
	var isoverload='Nej';
	if (overload>1)
		isoverload="Ja, med "+parseInt(tot_kg-nominal_kg)+"kg ("+parseInt(100*(overload-1))+"%)";
		
	var center_color='#ffffff';
	if (center<237 || center>355.5)
		center_color='#ff8080';
	var loadcenter_str=''+parseInt(center)+'mm (mellan 237mm och 355.5mm är okay)';

	var center_color_dry='#ffffff';
	if (center_dry<237 || center_dry>355.5)
		center_color_dry='#ff8080';
	var loadcenter_dry_str=''+parseInt(center_dry)+'mm (mellan 237mm och 355.5mm är okay)';

	output.innerHTML=\
		"<table>"+
		"<tr><td></td><td>Erforderligt:</td><td>Tillgängligt:</td></tr>"+
	    "<tr><td>Start:</td><td style=\"background:"+startcol+"\">"+parseInt(base_start_distance)+"m</td><td>"+parseInt(available_takeoff+0.25)+"m </td></tr>"+\
	    "<tr><td>Landning:</td><td style=\"background:"+landcol+"\">"+parseInt(1.43*base_landing_distance)+"m</td><td>"+parseInt(available_landing+0.25)+"m </td></tr>"+
	    "</table><br/>"+
		'Vindkomposant: '+parseInt(Math.abs(windcomp)+0.5)+'kt '+windwhat+' '+parseInt(Math.abs(windside)+0.5)+'kt sidvind'+" "+windleftright+"<br/>"+\
		'Överlast: '+isoverload+"<br/>"+
		'Tyngdpunkt: <span style="background:'+center_color+'">'+loadcenter_str+"</span><br/>"+\
		'Tyngdpunkt utan bränsle: <span style="background:'+center_color_dry+'">'+loadcenter_dry_str+"</span>";


    imgout.innerHTML=\
    	'<table><tr><td><b>Start</b></td><td><b>Landning</b></td></tr><tr><td><img src="/sufperformance/getmap?data='+encodeURIComponent(
    	JSON.stringify(
    		{ad:last_airport_data,
    		 perf:{start:base_start_distance,land:base_landing_distance,name:runway,start_roll:start_roll,landing_roll:landing_roll},
    		 what:'start'
    		}
    		))+'" /></td><td>'+
    	'<img src="/sufperformance/getmap?data='+encodeURIComponent(
    	JSON.stringify(
    		{ad:last_airport_data,
    		 perf:{start:base_start_distance,land:base_landing_distance,name:runway,start_roll:start_roll,landing_roll:landing_roll},
    		 what:'landing'
    		}
    		))+'" /></td></tr></table>';
    		
		
}
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
<tr>
<td>Fält:</td><td id="cur_field"><span id="changefield">${c.field}&nbsp;<button onclick="dochangefield()">&nbsp;Byt fält</button></span></td>
</tr>

<tr id="custom1" style="display:none"><td>Ban-nummer:</td><td><input onchange="onchangecustom()" style="background-color:#d0ffd0" id="custom_runway" type="text" size="5" /> (exempelvis: 16)</td></tr>
<tr id="custom2" style="display:none"><td>Tillgängligt för start:</td><td><input onchange="onchangecustom()" style="background-color:#d0ffd0"id="custom_takeoff_length" type="text" size="5" />m (exempelvis: 650)</td></tr>
<tr id="custom3" style="display:none"><td>Tillgängligt för landning:</td><td><input onchange="onchangecustom()" style="background-color:#d0ffd0" id="custom_landing_length" type="text" size="5" />m (exempelvis: 550)</td></tr>
</table>

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

<td>Bana</td><td>
<select onchange="calc()" id="runway">
<option value="16">16</option>
<option value="34">34</option>
<option value="07">07</option>
<option value="25">25</option>
</select>
</td></tr>
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
