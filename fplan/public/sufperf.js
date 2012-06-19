
/*
JSON.stringify(your_object, null, 2);

To convert a JSON string to a JS object, use JSON.parse:

var your_object = JSON.parse(json_text);

*/

function stepto(dest)
{
	for(var i=1;i<=3;++i)
	{
		var stepe=document.getElementById('step'+i);
		if (i!=dest)
			stepe.style.display='none';
		else
			stepe.style.display='block';
	}
}
function initial_load()
{
	
	update_runway_selector();
	calc();
	
	for(var i=1;i<=3;++i)
	{
		for(var j=1;j<=2;++j)
		{
			var nave=document.getElementById('step'+i+'nav'+j);
			temp='<div style="width:100%;">'+
				'<div style="width:30%;float:left;text-align:center;">';
			if (i!=1)
				temp+='<button onclick="stepto('+(i-1)+')">&lt;&lt;</button>';
			else
				temp+='&nbsp;';
			temp+='</div>'+
				'<div style="width:30%;float:left;text-align:center;">';
			if (j==1)
				temp+='Steg '+i+' av 3';
			else
				temp+='&nbsp;';
			temp+='</div>'+
				'<div style="width:30%;float:left;text-align:center;">';
			if (i!=3)
				temp+='<button onclick="stepto('+(i+1)+')">&gt;&gt;</button>';
			else
				temp+='<button onclick="calc()">Beräkna!</button>';
			temp+='</div>'+		
				'</div>';
				
			nave.innerHTML=temp;
		}
	}
}

$(document).ready(initial_load)

function myParseFloat(x)
{
	if (x)
		return parseFloat(x);
	return 0.0; 
}

function myParseFloat2(x)
{
	if (x!='')
		return parseFloat(x);
	return null; 
}

function show_custom()
{	
	hide_change_ad('Eget');
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
				threshold:myParseFloat($('#custom_displaced_threshold')[0].value),
				obstacle_dist:myParseFloat($('#custom_obstacle_dist')[0].value),
				obstacle_height:myParseFloat($('#custom_obstacle_height')[0].value),
				threshold_height:myParseFloat2($('#custom_threshold_height')[0].value),
				safety_factor:myParseFloat2($('#custom_safety_factor')[0].value)
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
   			alert('Finns ingen flygplats med det namnet i programmets databas. Skriv in baninformation manuellt i fälten ovan.');
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
function unhidecustom456()
{
	document.getElementById('custom4').style.display='table-row';
	document.getElementById('custom5').style.display='table-row';
	document.getElementById('custom6').style.display='table-row';
	document.getElementById('custom7').style.display='table-row';
	document.getElementById('custom_obstacle_dist').focus();
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
  runway_length=rwy.runway_length;
  runway_threshold=rwy.threshold;
  rwyhdg=rwy.rwyhdg;
  
  if (!last_airport_data.iscustom)
  {
	  $('#custom_runway')[0].value=runway;
	  $('#custom_runway_length')[0].value=parseInt(rwy.runway_length+0.5);
	  $('#custom_displaced_threshold')[0].value=parseInt(rwy.threshold+0.5);
	  $('#custom_obstacle_dist')[0].value='';
	  $('#custom_obstacle_height')[0].value='';
	  $('#custom_threshold_height')[0].value='';
	  $('#custom_safety_factor')[0].value='';
  }
  

  var pilot_kg=myParseFloat(document.getElementById('pilot').value);
  var pax_kg=myParseFloat(document.getElementById('pax').value);
  var luggage_kg=myParseFloat(document.getElementById('luggage').value);
  var knee_kg=myParseFloat(document.getElementById('knee').value);
  var left_fuel_kg=myParseFloat(document.getElementById('leftfuel').value)*0.73;
  var right_fuel_kg=myParseFloat(document.getElementById('rightfuel').value)*0.73;
  
  

  var tot_kg=pilot_kg+pax_kg+luggage_kg+knee_kg+left_fuel_kg+right_fuel_kg+plane_kg;

  if (tot_kg>600) {myalert("Det här programmet kan inte ens räkna på ett så överlastat flygplan.");return;}
  if (tot_kg<200) {myalert("Orimliga vikt-värden.");return;}

  var moments=126*plane_kg+163*(left_fuel_kg+right_fuel_kg)+643*(pilot_kg+pax_kg)+1023*luggage_kg+100*knee_kg;
  var center=moments/tot_kg;
  
  var tot_kg_dry=pilot_kg+pax_kg+luggage_kg+knee_kg+plane_kg;
  var moments_dry=126*plane_kg+643*(pilot_kg+pax_kg)+1023*luggage_kg+100*knee_kg;
  var center_dry=moments_dry/tot_kg_dry;
  
  
  var performance_kg=tot_kg;
  if (performance_kg<nominal_kg)
    performance_kg=nominal_kg;
  var overload=performance_kg/nominal_kg;
  var overload2=tot_kg/nominal_kg;

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
  var isice=document.getElementById('ice').checked;
  var iswetgrass=document.getElementById('wetgrass').checked;
  var isslush=document.getElementById('slush').checked;
  var slushdepth=myParseFloat(document.getElementById('slushdepth').value);
  var isheavysnow=document.getElementById('heavysnow').checked;
  var snowdepth=myParseFloat(document.getElementById('snowdepth').value);
  var ispowder=document.getElementById('powder').checked;
  var powderdepth=myParseFloat(document.getElementById('powderdepth').value);
  
  var winddir=myParseFloat(document.getElementById('winddir').value);
  var windvel=myParseFloat(document.getElementById('windvel').value);

  if (slushdepth>10) {myalert("För djupt slasklager.");return;}
  if (snowdepth>10) {myalert("För djup snö.");return;}
  if (powderdepth>20) {myalert("För djup snö.");return;}

  if (qnh<700) {myalert("QNH måste vara större än 700.");return;}
  if (qnh>1200) {myalert("QNH måste vara mindre än 1200.");return;}
  if (elev<-2000) {myalert("Höjd över havet utanför tillåtet område.");return;}
  if (elev>9500) {myalert("Höjd över havet utanför tillåtet område.");return;}
  if (temp<-60) {myalert("Temperatur utanför tillåtet område.");return;}
  if (temp>80) {myalert("Temperatur utanför tillåtet område.");return;}

  if (tilt<-10) {myalert("Angivet värde för lutning är utanför det här programmets förmåga.");return;}
  if (tilt>2) {myalert("Max 2% motlut tillåtet.");return;}

  if (windvel>40) {myalert("Det här programmet kan inte räkna med starkare vindar än 40kt.");return;}
  if (windvel<0) {myalert("Negativ vind inte tillåten.");return;}
  
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
  
  	
  	
  var landing_threshold_height=15.0;
  var flare_shortening=1.0;
  var avg_flare_speed=43*1.852/3.6;
  
  
  var base_landing_distance=267;
  var orig_landing_distance=267;
  var landing_roll=152;
  var obstacle_altitude=null;
  var threshold_start_altitude=15;
  var nominal_15m_drop_time=(base_landing_distance-landing_roll)/avg_flare_speed;
  //var drop_time=nominal_15m_drop_time*(landing_threshold_height/15);
  var dropspeed=(avg_flare_speed-windcomp*1.852/3.6);
  var dropdist15=dropspeed*nominal_15m_drop_time;
  var dropratio=15/5.0;
  if (dropdist15>5.0)
	  dropratio=15.0/dropdist15;
  
  
  if (windcomp>0)
  	base_landing_distance*=1.0-0.01*windcomp;
  if (windcomp<0)
  	base_landing_distance*=1.0-0.04*windcomp;
  
  var safe_factor=1.43;
  if (rwy.safety_factor!=null)
  {
	  safe_factor=1+rwy.safety_factor/100.0;
  }
  
  
  	
  if (eff_press_factor>1)
  	base_landing_distance*=1.0+(Math.sqrt(eff_press_factor)-1)
    
  var base_start_distance=264;
  var orig_start_distance=base_start_distance;
  var start_roll=86;
  
  if (isshortgrass) base_start_distance*=1.1;
  if (islonggrass) base_start_distance*=1.5;
  if (isice) base_landing_distance*=1.5;
  if (iswetgrass) base_landing_distance*=1.2;
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
  var climb_performance_mps=climb_performance/196.850394;
  
  
  var time_min_to_300=(300.0-49.2)/climb_performance;
  var time_sec_to_300=time_min_to_300*60.0;
  var climb_speed_ms=120/3.6-windcomp*1.852/3.6;
  if (climb_speed_ms<1) climb_speed_ms=1.0;

  if (tilt>0)
  {
  	base_start_distance*=1.0+(tilt)*0.05;
  }
  if (tilt<0)
  	base_landing_distance*=1.0+(-tilt)*0.08;
 
  if (overload>1)
  {
	  base_start_distance*=overload; 
	  base_landing_distance*=overload;
  }
  if (overload2<1)
  {
	  var underload=1-overload2;
	  base_start_distance*=(1-1.0*underload); 
	  base_landing_distance*=(1-0.5*underload);
	  
  }
  
  
  start_roll*=(base_start_distance/orig_start_distance);
  var obstacle_start_altitude=null;
  if (rwy.threshold_height!=null)
  {
	  landing_threshold_height=rwy.threshold_height;
	  flare_shortening=landing_threshold_height/15.0;
	  //var flare_part=landing_roll/orig_landing_distance;
  }
  if (rwy.obstacle_dist)
  {
	  obstacle_altitude=landing_threshold_height+(rwy.obstacle_dist+rwy.threshold)*dropratio;
	  
	  var dist_to_obst=((rwy.runway_length+rwy.obstacle_dist)-base_start_distance)
	  var time_to_obst=dist_to_obst/climb_speed_ms;
	  obstacle_start_altitude=15+time_to_obst*climb_performance_mps;

	  /*
	  
	  var x1=base_start_distance;
	  var y1=15;
	  var x2=
	  */
  }
  
  landing_roll*=(base_landing_distance/orig_landing_distance);
  
  base_landing_distance=landing_roll+(base_landing_distance-landing_roll)*flare_shortening;

  //alert('base_landing: '+base_landing_distance+" roll: "+landing_roll);
  
  
  //landing_roll*=flare_shortening;
  
  
  var horizontal_distance_to_300=base_start_distance+climb_speed_ms*time_sec_to_300;  

    imgout=document.getElementById('resultimg');
    

	output=document.getElementById('resultdiv');
	var startcol='#ffffff';
	var landcol='#ffffff';
	if (base_start_distance>=available_takeoff)
		startcol='#ff8080';
	if (safe_factor*base_landing_distance>=available_landing)
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
	obst_str="";
	if (obstacle_altitude)
	{
		var obst_color='#ffffff';
		if (obstacle_altitude-10<rwy.obstacle_height)
			obst_color='#ffff40';
		if (obstacle_altitude<rwy.obstacle_height)
			obst_color='#ff8080';
		obst_str='Flyghöjd vid hinder, landning: <span style="background-color:'+obst_color+'">'+parseInt(obstacle_altitude+0.5)+'m (Hinder: '+rwy.obstacle_height+'m)</span> <br/>'+
				'Vid start: '+obstacle_start_altitude+"<br/>";
	}
	output.innerHTML="<table>"+
		"<tr><td></td><td>Erforderligt:</td><td>Tillgängligt:</td></tr>"+
	    "<tr><td>Start:</td><td style=\"background:"+startcol+"\">"+parseInt(base_start_distance)+"m</td><td>"+parseInt(available_takeoff+0.25)+"m </td></tr>"+
	    "<tr><td>Landning:</td><td style=\"background:"+landcol+"\">"+parseInt(safe_factor*base_landing_distance)+"m</td><td>"+parseInt(available_landing+0.25)+"m </td></tr>"+
	    "</table><br/>"+
		'Vindkomposant: '+parseInt(Math.abs(windcomp)+0.5)+'kt '+windwhat+' '+parseInt(Math.abs(windside)+0.5)+'kt sidvind'+" "+windleftright+"<br/>"+
		'Överlast: '+isoverload+"<br/>"+
		obst_str+
		'Tyngdpunkt: <span style="background:'+center_color+'">'+loadcenter_str+"</span><br/>"+
		'Tyngdpunkt utan bränsle: <span style="background:'+center_color_dry+'">'+loadcenter_dry_str+"</span>";


    imgout.innerHTML=''+
    	'<table><tr><td><b>Start</b></td><td><b>Landning</b></td></tr><tr><td>Från ovan:<br/><img src="/sufperformance/getmap?data='+encodeURIComponent(
    	JSON.stringify(
    		{ad:last_airport_data,
    		 perf:{start:base_start_distance,land:base_landing_distance,name:runway,start_roll:start_roll,landing_roll:landing_roll,start300:horizontal_distance_to_300,safe_factor:safe_factor},
    		 what:'start'
    		}
    		))+'" />'+
    		'<br/>Från sidan:<br/><img src="/sufperformance/getmapside?data='+encodeURIComponent(
    		    	JSON.stringify(
    		    		{ad:last_airport_data,
    		    		 perf:{start:base_start_distance,land:base_landing_distance,name:runway,start_roll:start_roll,landing_roll:landing_roll,start300:horizontal_distance_to_300,safe_factor:safe_factor,
    		    			 	runway_length:runway_length,runway_threshold:runway_threshold,threshold_altitude:threshold_start_altitude,
    		    			 	obst_height:rwy.obstacle_height,obst_dist:rwy.obstacle_dist,obst_alt:obstacle_start_altitude},
    		    		 what:'start'
    		    		}
    		    		))+'" />'+	    		
    	'</td><td>'+
    	'Från ovan:<br/><img src="/sufperformance/getmap?data='+encodeURIComponent(
    	JSON.stringify(
    		{ad:last_airport_data,
    		 perf:{start:base_start_distance,land:base_landing_distance,name:runway,start_roll:start_roll,landing_roll:landing_roll,start300:horizontal_distance_to_300,safe_factor:safe_factor},
    		 what:'landing'
    		}
    		))+'" />'+
		'<br/>Från sidan:<br/><img src="/sufperformance/getmapside?data='+encodeURIComponent(
    	JSON.stringify(
    		{ad:last_airport_data,
    		 perf:{start:base_start_distance,land:base_landing_distance,name:runway,start_roll:start_roll,landing_roll:landing_roll,start300:horizontal_distance_to_300,safe_factor:safe_factor,
    			 	runway_length:runway_length,runway_threshold:runway_threshold,threshold_altitude:landing_threshold_height,
    			 	obst_height:rwy.obstacle_height,obst_dist:rwy.obstacle_dist,obst_alt:obstacle_altitude},
    		 what:'landing'
    		}
    		))+'" />'+
    		'</td></tr></table>';
    		
		
}
