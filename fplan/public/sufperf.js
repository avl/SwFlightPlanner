
/*
JSON.stringify(your_object, null, 2);

To convert a JSON string to a JS object, use JSON.parse:

var your_object = JSON.parse(json_text);

*/

function initial_load()
{
	
	update_runway_selector();
	calc();
}

$(document).ready(initial_load)

function myParseFloat(x)
{
	if (x)
		return parseFloat(x);
	return 0.0; 
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


function update_runway_selector()
{
	var best_runway=null;
	var best_runway_off=10000;
	$.each(last_airport_data['runways'], function(index,val) {
		var off=Math.abs(val.rwyhdg-myParseFloat(document.getElementById('winddir').value));
		if (off>10 && off<95)
			off-=10;
		if (off>180) off=Math.abs(off-360);
		if (off<best_runway_off)
		{
			best_runway_off=off;
			best_runway=val.name;
		}
	});
	cur_runway=best_runway;
	if (!($('#runway')[0]))
		return;
	var select = $('#runway');

	$('option', select).remove();
	var options = select.prop('options');
	$.each(last_airport_data['runways'], function(index,val) {
		    options[options.length] = new Option(val.name, val.name);
		    if (best_runway==val.name)
		    	options[options.length-1].selected=true;
			});			
	

}
function do_load_ad(){
	var sf=document.getElementById('tags');
	$.getJSON(airport_load_url,{name:sf.value}, function(data) {
		last_airport_data=data;
		update_runway_selector();
		calc();
				
	});
	hide_change_ad(sf.value);	

};
function onchangecustom()
{
	var che=document.getElementById('changefield');
	che.innerHTML='<button onclick="dochangefield()">Hämta Fältdata</button>';
	
	var decadeg=$('#custom_runway')[0].value;
	last_airport_data={
		runways:[{
				name:decadeg,
				rwyhdg:myParseFloat(decadeg)*10,
				runway_length:myParseFloat($('#custom_runway_length')[0].value),
				threshold:myParseFloat($('#custom_displaced_threshold')[0].value)
				}		
			],
	    iscustom:true
	}
	var select = $('#runway');
	$('option', select).remove();
	
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
  	 $.getJSON(searchurl,{term:sf.value}, function(data) {
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
		'<button onclick="click_search()">Välj</button>';
	var sf=document.getElementById('tags');
	sf.focus();
	$( "#tags" ).autocomplete({			
		source: searchurl
	});
	$( "#tags" ).keypress(function(e){
      if(e.which == 13 || e.which==9){
      	click_search();
       }
      });
	
	
	
	
}
function hide_change_ad(newname)
{
	$('#tags').autocomplete('destroy');
	var che=document.getElementById('changefield');
	che.innerHTML='Laddat '+newname+'. Välj Bana:'+
	'<select onchange="calc()" id="runway">'+
	'</select>'+
	'<br/><button onclick="dochangefield()">Hämta Fältdata</button>';
	

}

function myalert(msg)
{
    imgout=document.getElementById('resultimg');
    imgout.innerHTML="";    
	output=document.getElementById('resultdiv');
	output.innerHTML="<div style=\"background-color:#ffc000\"><big>"+msg+"</big></div>";

}

function ipol(x,x1,x2,y1,y2)
{
	var ratio=(x-x1)/(x2-x1);
	return y1+(y2-y1)*ratio;
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
  
  
  var runway=null;
  if (last_airport_data.iscustom)
	  runway=document.getElementById('custom_runway').value;
  else
  {
	  runwaye=document.getElementById('runway');
	  if (runwaye)
		  runway=runwaye.value;
	  else
		  runway=cur_runway;
  }
  
  available_takeoff=0;
  available_landing=0;
  
  rwy=get_runway(runway);
  available_takeoff=rwy.runway_length;
  available_landing=rwy.runway_length-rwy.threshold;
  rwyhdg=rwy.rwyhdg;
  
  if (!last_airport_data.iscustom)
  {
	  $('#custom_runway')[0].value=runway;
	  $('#custom_runway_length')[0].value=parseInt(rwy.runway_length+0.5);
	  $('#custom_displaced_threshold')[0].value=parseInt(rwy.threshold+0.5);
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
  	
  var climb_performance=6.2*196.850394;
  if (effective_elev>0 && effective_elev<1000)
  	climb_performance=ipol(effective_elev,0.0,1000.0,6.2*196.85039,5.9*196.85039);
  else 
  {
    if (effective_elev>=1000 && effective_elev<2000)
  	  climb_performance=ipol(effective_elev,1000.0,2000.0,5.9*196.85039,5.2*196.85039);
    else
   	  climb_performance=5.2*196.850394;
  }
  var time_min_to_300=(300.0-49.2)/climb_performance;
  var time_sec_to_300=time_min_to_300*60.0;
  var climb_speed_ms=120/3.6;
  var horizontal_distance_to_300=climb_speed_ms*time_sec_to_300;  

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

	output.innerHTML="<table>"+
		"<tr><td></td><td>Erforderligt:</td><td>Tillgängligt:</td></tr>"+
	    "<tr><td>Start:</td><td style=\"background:"+startcol+"\">"+parseInt(base_start_distance)+"m</td><td>"+parseInt(available_takeoff+0.25)+"m </td></tr>"+
	    "<tr><td>Landning:</td><td style=\"background:"+landcol+"\">"+parseInt(1.43*base_landing_distance)+"m</td><td>"+parseInt(available_landing+0.25)+"m </td></tr>"+
	    "</table><br/>"+
		'Vindkomposant: '+parseInt(Math.abs(windcomp)+0.5)+'kt '+windwhat+' '+parseInt(Math.abs(windside)+0.5)+'kt sidvind'+" "+windleftright+"<br/>"+
		'Överlast: '+isoverload+"<br/>"+
		'Tyngdpunkt: <span style="background:'+center_color+'">'+loadcenter_str+"</span><br/>"+
		'Tyngdpunkt utan bränsle: <span style="background:'+center_color_dry+'">'+loadcenter_dry_str+"</span>";


    imgout.innerHTML=''+
    	'<table><tr><td><b>Start</b></td><td><b>Landning</b></td></tr><tr><td><img src="/sufperformance/getmap?data='+encodeURIComponent(
    	JSON.stringify(
    		{ad:last_airport_data,
    		 perf:{start:base_start_distance,land:base_landing_distance,name:runway,start_roll:start_roll,landing_roll:landing_roll,start300:base_start_distance+horizontal_distance_to_300},
    		 what:'start'
    		}
    		))+'" /></td><td>'+
    	'<img src="/sufperformance/getmap?data='+encodeURIComponent(
    	JSON.stringify(
    		{ad:last_airport_data,
    		 perf:{start:base_start_distance,land:base_landing_distance,name:runway,start_roll:start_roll,landing_roll:landing_roll,start300:base_start_distance+horizontal_distance_to_300},
    		 what:'landing'
    		}
    		))+'" /></td></tr></table>';
    		
		
}
