modifiable_cols=[];

function get(idx,wcol)
{
	var vid='fplanrow'+idx+wcol;
	var e=document.getElementById(vid);
	if (e==null)
		alert('Null:'+vid);
	if (e.value=='')
		return 0.0;			
	return e.value;
}
function getf(idx,wcol)
{
	return parseFloat(get(idx,wcol));
}
function gete(idx,wcol)
{
	var vid='fplanrow'+idx+wcol;
	var e=document.getElementById(vid);
	return e;
}


/*
function fetch_acparams()
{
	function ac_cb(req)
	{
		if (req.responseText!='')
		{
			var ac=evalJSONRequest(req);
			for(var i=0;i<ac.length;++i)
			{
				var tas=gete(i,'TAS');
				tas.value=''+ac[i].toFixed(1);
    			on_updaterow(i,'all');
			}
		}	
	}
	var ace=document.getElementById('curaircraft');
	var params={};	
	var alts='';
	for(var i=0;i<num_rows-1;++i)
	{
	    if (i!=0) alts+=',';
	    //FIXME: Filter out any ',' from alt field
	    alts+=gete(i,'Alt').value;
	}
	params['alts']=alts;
	params['tripname']=tripname;
	params['aircraft']=ace.value;
	var def=doSimpleXMLHttpRequest(fetchacurl,params);
	def.addCallback(ac_cb);
}
*/


function fetch_winds()
{
	function weather_cb(req)
	{	
		if (req.responseText!='')
		{
			weather=evalJSONRequest(req);
			for(var i=0;i<weather.length;++i)
			{
				var w=gete(i,'W');
				var v=gete(i,'V');
				w.value=weather[i][0];
				v.value=weather[i][1];
    			on_updaterow(i,'all');
			}
		}	
	}
	var params={};	
	var alts='';
	for(var i=0;i<num_rows-1;++i)
	{
	    if (i!=0) alts+=',';
	    /*FIXME: Filter out any ',' from alt field*/
	    alts+=gete(i,'Alt').value;
	}
	params['alts']=alts;
	params['tripname']=tripname;
	var def=doSimpleXMLHttpRequest(fetchweatherurl,params);
	def.addCallback(weather_cb);
}

function save_data(cont)
{
	function save_data_cb(req)
	{	
		if (req.responseText=='ok')
		{
			if (cont!=null)
				cont();		
		}
		else
		{
			alert('Error:'+req.responseText);
		}
	}
	
	var params={};
	for(var i=0;i<num_rows-1;i++)
	{
        for(var j=0;j<modifiable_cols.length;++j)
        {
            var wh=modifiable_cols[j];
            var val=get(i,wh);
            params[wh+'_'+i]=val;
        }	    
	}			

	for(var i=0;i<num_rows;i++)
	{
        var alt=document.getElementById('wpalt'+i).value;
        params['wpalt'+i]=alt;            
    }
	params['tripname']=tripname;
	var def=doSimpleXMLHttpRequest(saveurl,
		params);
	def.addCallback(save_data_cb);
}


function format_time(time_hours)
{
	var time_whole_hours=parseInt(Math.floor(time_hours));
	var time_minutes=60.0*(time_hours-time_whole_hours);
	var time_i=parseInt(time_minutes);
	if (time_i>=60) time_i=59;
	var time_s=''+time_i;
	if (time_i<10)
		time_s='0'+time_s;
	return ''+time_whole_hours+'h'+time_s+'m';
}

function on_updaterow(idx,col)
{

	var next=0;
	if (col=='all' || col=='TAS' || col=='W' || col=='V')
	{
		var tas=getf(idx,'TAS');
		var tt=getf(idx,'TT');
		var wind=getf(idx,'W');
		var windvel=getf(idx,'V');
		var variation=getf(idx,'Var');
		var dev=getf(idx,'Dev');
		var pi=3.14159265;
		var f=1.0/(180.0/pi);
		var wca=0;
		var GS=0;

		var winddir=(wind+180) - tt;
		var windx=Math.cos(winddir*f)*windvel;
		var windy=Math.sin(winddir*f)*windvel;
		if (windy>tas || -windy>tas)
		{
			if (windy>tas)
				wca=-90;
			else
				wca=90;
			GS=0;
		}
		else
		{
			if (-windx<tas)
			{
				wca=-Math.asin(windy/tas)/f;
				
				var tas_x=Math.cos(wca*f)*tas;
				var tas_y=Math.sin(wca*f)*tas;
				GS = Math.sqrt((tas_x+windx)*(tas_x+windx)+(tas_y+windy)*(tas_y+windy));
			}
			else
			{
				wca=0;
				GS=0;
			}			
		}		
		/* True = Air + Wind -> Air = True - Wind*/
		var wcae=gete(idx,'WCA');
		if (wca>0)
			wcae.value='+'+wca.toFixed(0);
		else
			wcae.value=''+wca.toFixed(0);
		
		var gse=gete(idx,'GS');
		gse.value=GS.toFixed(0);
		next=1;	
	}
	if (next || col=='TAS' || col=='W' || col=='V' || col=='Var' || col=='Dev')
	{
		var tt=getf(idx,'TT');
		var wca=getf(idx,'WCA');
		var var_=getf(idx,'Var');
		var dev=getf(idx,'Dev');
		var ch=gete(idx,'CH');
		ch.value=parseInt(0.5+tt+wca-var_-dev)%360;
	}	
	if (next || col=='TAS' || col=='W' || col=='V' || col=='Var' || col=='Dev')
	{
		var gs=getf(idx,'GS');
		var D=getf(idx,'D');
		var time=gete(idx,'Time');
		if (gs>0.0)
		{
			time_hours=D/gs;
			time.value=format_time(time_hours);
			idx2time_hours[idx]=time_hours;
		}
		else
		{
			time.value="-";
			idx2time_hours[idx]=1e30;
		}
		
		
	}
	var hour_sum=0;
	for(var i=0;i<num_rows-1;++i)
	{
		hour_sum+=idx2time_hours[i];
	}
	var e=document.getElementById('tottime');
	if (hour_sum<1e10)
		e.value=format_time(hour_sum);
	else
		e.value="-";

	return;	
}
function fpaddwaypoint(pos,name,rowdata,altitude)
{
	searchpopup=0;

	
	var tab=document.getElementById('flightplantable');
	if (rowdata==null)
	{
		rowdata=[];
		for(var i=0;i<fpcolnum;++i)
			rowdata.push('');
	}
	var idx=0;
	if (tab.rows.length==1)
		idx=0;
	else
		idx=(tab.rows.length-1)/2;
	var elem=tab.insertRow(-1);
	waypointalthelp='Optional altitude for waypoint. Can be left blank. Set this to terrain height for any landings en-route.';
	elem.innerHTML='<td colspan="'+fpcolnum+'">#'+idx+': <input title="Name of waypoint. Go to map-screen to change." readonly="1" type="text" name="name'+idx+'" value="'+name+'"/>'+
	    '<span title="'+waypointalthelp+'">Waypoint Alt:</span><input title="'+waypointalthelp+'" type="text" id="wpalt'+idx+'" name="alt'+idx+'" value="'+altitude+'"/></td>';

	if (rowdata!=null && rowdata.length>0)
	{
		var elem=tab.insertRow(-1);
		var s='';
		for(var i=0;i<rowdata.length;++i)
		{			
			var ro='';
			var wh=fpcolshort[i];
			if (wh=='TT' || wh=='D' || wh=='GS' || wh=='CH' || wh=='Time' || wh=='WCA')
			{  
				ro='readonly="1"';
			}
			else
			{
				ro='onkeypress="return not_enter(event)"';
			    modifiable_cols.push(wh);
			}
			s=s+'<td><input '+ro+' id="fplanrow'+idx+fpcolshort[i]+'" onkeyup="on_updaterow('+idx+',\''+fpcolshort[i]+'\');"  onchange="on_updaterow('+idx+',\''+fpcolshort[i]+'\');" size="'+fpcolwidth[i]+'" title="'+fpcoldesc[i]+' '+fpcolextra[i]+'" type="text" name="row'+i+''+fpcolshort[i]+'" value="'+rowdata[i]+'"/></td>\n';		
		}
		elem.innerHTML=s;
	}
}
idx2time_hours=[];

function fpmain_init()
{
	for(var i=0;i<num_rows-1;++i)
		idx2time_hours.push(0);
	for(var i=0;i<num_rows-1;++i)
	{	
		on_updaterow(i,'all');
	}
}





