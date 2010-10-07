modifiable_cols=[];
dirty=0;
in_prog=0;

function choose_aircraft()
{
    function chooseac()
    {
        var f=document.getElementById('chooseaircraftform');
        f.submit();        
    }
    save_data(chooseac);
}

function do_save()
{
    if (dirty)
    {
        function finish_save()
        {					    
        }
        save_data(finish_save);	    
    }
}

function makedirty()
{
    if (!dirty)
    {
        var e=document.getElementById('printablelink');
        e.innerHTML='<span onclick="do_save()" onmouseover="do_save()" style="cursor:pointer">Printable</span>';
    }
    dirty=1;    
}

function get(id,wcol)
{
	var vid='fplanrow'+id+wcol;
	var e=document.getElementById(vid);
	if (e==null)
	{   
	    alert(id+','+wcol+','+vid);
	}
	if (e.value=='')
		return 0.0;			
	return e.value;
}
function getf(id,wcol)
{
	var pf=parseFloat(get(id,wcol));
	if (pf==NaN)
	    pf=0.0;
	return pf;
}
function gete(id,wcol)
{
	var vid='fplanrow'+id+wcol;
	var e=document.getElementById(vid);
	return e;
}




function fetch_winds()
{
	function weather_cb(req)
	{	
		if (req.responseText!='')
		{
			weather=evalJSONRequest(req);
			for(var i=0;i<weather.length;++i)
			{
				var w=gete(fpid[i],'W');
				var v=gete(fpid[i],'V');
				if (''+weather[i][0]!='NaN' && weather[i][0]!='')
				{
			        w.value=parseInt(parseFloat(weather[i][0]));
			        v.value=parseInt(parseFloat(weather[i][1]));
        			on_updaterow(fpid[i],i,'all');
        		}
			}
        	dirty=1;
        	do_save();
		}	
	}
	var params={};	
	var alts='';
	for(var i=0;i<num_rows-1;++i)
	{
	    if (i!=0) alts+=',';
	    /*FIXME: Filter out any ',' from alt field*/
	    alts+=gete(fpid[i],'Alt').value;
	}
	params['alts']=alts;
	params['tripname']=tripname;
	var def=doSimpleXMLHttpRequest(fetchweatherurl,params);
	def.addCallback(weather_cb);
}

function parsealt(what)
{
    what=''+what;
    if (what.replace(/\s/g,'')=='')
    	return what;
    if (what.substring(what.length-2,100)=='ft')
        what=what.substring(0,what.length-2);
    if (!isNaN(parseFloat(what.substring(2,100))))
    {
        return what;
    }
    if (what.substring(0,2)=='FL')
    {
        if (!isNaN(parseFloat(what.substring(2,100))))
        {
            return what;
        }
    }    
    return 0;
}

function save_data(cont)
{
    if (in_prog)
        return;
    in_prog=1;
	function save_data_cb(req)
	{	
	    in_prog=0;
		if (req.responseText=='ok')
		{
		    if (!dirty)
		    {
                var e=document.getElementById('printablelink');
                e.innerHTML='<a href="'+printableurl+'"><u>Printable</u></a>';		    
			    if (cont!=null)
				    cont();		
		    }
		}
		else
		{
			alert('Error:'+req.responseText);
		}
	}
	dirty=0;
	var params={};
	for(var i=0;i<num_rows-1;i++)
	{
        for(var j=0;j<modifiable_cols.length;++j)
        {
            var wh=modifiable_cols[j];
            var val;
            if (wh!='Alt')       
                val=getf(fpid[i],wh);
            else
            {
                val=parsealt(get(fpid[i],wh));
            }
            params[wh+'_'+fpid[i]]=val;
        }	    
	}			
    function add(what)
    {
	    var e=document.getElementById(what);
	    if (e)
            params[what]=e.value;
    }
	for(var i=0;i<num_rows;i++)
	{
	    add('date_of_flight_'+fpid[i]);
	    add('departure_time_'+fpid[i]);
	    add('fuel_'+fpid[i]);
	    add('persons_'+fpid[i]);
    }
    
	params['tripname']=tripname;
	params['realname']=document.getElementById('realname').value;
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
function get_wp_clock(id)
{
    //return ''+time_hours;
    var e=document.getElementById('departure_time_'+id);
    var val=e.value;
    if (val.length<2)
        return null;
    var c=[val.substring(0,2),0]
    c=e.value.split(":");
    if (c.length<=1)
    {
        if (val.length==4)
            c=[val.substring(0,2),val.substring(2,4)];
    }

    var hour=c[0]
    var minutes=0;
    if (c.length>1)
        minutes=c[1];
    return parseFloat(hour)+parseFloat(minutes)/60.0;    
}
function format_clock(hours)
{    
    //var hours=parseFloat(time_hours)+parseFloat(hour)+parseFloat(minutes)/60.0;    
	var totmin=parseInt(hours*60.0);
	var mins=totmin%60;
	if (mins<10)
	    min_str='0'+mins;
	else
	    min_str=''+mins;
	var hours=parseInt(Math.floor(totmin/60))%24;
	if (hours<10)
	    hour_str='0'+hours;
	else
	    hour_str=''+hours;
	return ''+hour_str+':'+min_str;
}

function on_updaterow(id,idx,col)
{
    on_updaterow_impl(id,idx,col);
    update_clocks();
}
function on_updaterow_impl(id,idx,col)
{
	var next=0;
	if (col=='all' || col=='TAS' || col=='W' || col=='V')
	{
		var tas=getf(id,'TAS');
		var tt=getf(id,'TT');
		var wind=getf(id,'W');
		var windvel=getf(id,'V');
		var variation=getf(id,'Var');
		var dev=getf(id,'Dev');
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
		var wcae=gete(id,'WCA');
		if (wca>0)
			wcae.value='+'+wca.toFixed(0);
		else
			wcae.value=''+wca.toFixed(0);
		
		var gse=gete(id,'GS');
		gse.value=GS.toFixed(0);
		next=1;	
	}
	if (next || col=='TAS' || col=='W' || col=='V' || col=='Var' || col=='Dev')
	{
		var tt=getf(id,'TT');
		var wca=getf(id,'WCA');
		var var_=getf(id,'Var');
		var dev=getf(id,'Dev');
		var ch=gete(id,'CH');
		ch.value=parseInt(0.5+tt+wca-var_-dev)%360;
		next=1;
	}	
	if (next || col=='TAS' || col=='W' || col=='V' || col=='Var' || col=='Dev' || col=='Clock')
	{
		var gs=getf(id,'GS');
		var D=getf(id,'D');
		var time=gete(id,'Time');
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
function update_clocks()
{
    var partsum=get_wp_clock(firstwaypointid);
    for(var i=0;i<num_rows-1;++i)
    {
        var id=fpid[i];
        //alert(document.getElementById('landingrow'+id).innerHTML);
        if (document.getElementById('departure_time_'+id)!=null)
        {
            var t=get_wp_clock(id);
            if (t!=null)
                partsum=t;
        }
        else
        {
            //alert('no find: departure_time_'+id);
        } 
       
        partsum+=idx2time_hours[i];
	    var clocke=gete(id,'Clock');
	    clocke.value=format_clock(partsum);				
	}

}
function toggle_landing(id,idx)
{
    var toggle=document.getElementById('landhere'+id);
    var subform=document.getElementById('departure_time'+id);
    if (toggle.checked)
    {
        if (!subform)
        {
        	var landingrow=document.getElementById('landingrow'+id);
        	var s=format_empty_landingrow(id,idx);
        	landingrow.innerHTML=s;
        }
    }
    else
    {
    	var landingrow=document.getElementById('landingrow'+id);
    	landingrow.innerHTML='';        
    }
}
function format_empty_landingrow(id,idx)
{
    return '<td colspan="'+fpcolnum+'"><table>'+
            '<tr><td>Takeoff date: </td><td><input size="10" type="text" onchange="makedirty()" id="date_of_flight_'+id+'" value=""/>(YYYY-MM-DD)</td></tr>'+
            '<tr><td>Estimated takeoff time (UTC): </td><td><input size="5" type="text" onchange="makedirty();on_updaterow('+id+','+idx+',\'Clock\');" id="departure_time_'+id+'" value=""/>(HH:MM)</td></tr>'+
            '<tr><td>Fuel at takeoff: </td><td><input size="4" type="text" onchange="makedirty()" id="fuel_'+id+'" value=""/>(L)</td>'+
            '<tr><td>Persons on board: </td><td><input size="4" type="text" onchange="makedirty()" id="persons_'+id+'" value=""/></td></tr>'+
        	'</table></td>';
}
function fpaddwaypoint(id,idx,pos,name,rowdata,altitude,stay)
{
	searchpopup=0;

	
	var tab=document.getElementById('flightplantable');
	if (rowdata==null)
	{
		rowdata=[];
		for(var i=0;i<fpcolnum;++i)
			rowdata.push('');
	}
	var landelem=null;
	var elem=tab.insertRow(-1);
	if (rowdata!=null && rowdata.length>0)
	{
		landelem=tab.insertRow(-1);
	}
	var landherechecked='';
	if (stay.length>0)
	{
	    landherechecked=' checked="checked" ';
	}
	landherehelp='Check this if you wish to land at this point. A landing is always assumed at the end of the journey, you can not make a plan that ends in the air.';
	if (idx!=0 && idx!=num_rows-1)
    	landheres='&nbsp;<span title="'+landherehelp+'"><input '+landherechecked+' onchange="toggle_landing('+id+','+idx+')" title="'+landherehelp+'" type="checkbox" id="landhere'+id+'"/>Land here</span>';
    else 
        landheres='';

	elem.innerHTML='<td colspan="'+fpcolnum+'">#'+id+': <input title="Name of waypoint. Go to map-screen to change." readonly="1" type="text" name="name'+id+'" value="'+name+'"/>'+
	    landheres+
	    '</td>';

	if (rowdata!=null && rowdata.length>0)
	{
		var elem=tab.insertRow(-1);
		var s='';
		for(var i=0;i<rowdata.length;++i)
		{			
			var ro='';
			var wh=fpcolshort[i];
			if (wh=='TT' || wh=='D' || wh=='GS' || wh=='CH' || wh=='Time' || wh=='WCA' || wh=='Clock')
			{  
				ro='readonly="1"';
			}
			else
			{
				ro='onkeypress="return not_enter(event)"';
			    modifiable_cols.push(wh);
			}
			s=s+'<td><input '+ro+' id="fplanrow'+id+fpcolshort[i]+'" onkeyup="makedirty();on_updaterow('+id+','+idx+',\''+fpcolshort[i]+'\');"  onchange="makedirty();on_updaterow('+id+','+idx+',\''+fpcolshort[i]+'\');" size="'+fpcolwidth[i]+'" title="'+fpcoldesc[i]+' '+fpcolextra[i]+'" type="text" name="row'+i+''+fpcolshort[i]+'" value="'+rowdata[i]+'"/></td>\n';		
		}
		elem.innerHTML=s;
		
		landelem.id='landingrow'+id;
        
        if (stay.length && idx!=0)
        {
            var date=stay[0];
            var time=stay[1];
            var fuel=stay[2];
            var persons=stay[3];
        	var s=format_empty_landingrow(id,idx);
        	landelem.innerHTML=s;
        	landelem.cells[0].childNodes[0].rows[0].cells[1].childNodes[0].value=date;
        	landelem.cells[0].childNodes[0].rows[1].cells[1].childNodes[0].value=time;
        	landelem.cells[0].childNodes[0].rows[2].cells[1].childNodes[0].value=fuel;
        	landelem.cells[0].childNodes[0].rows[3].cells[1].childNodes[0].value=persons;
		}		
	}
}
idx2time_hours=[];

function fpmain_init()
{
	for(var i=0;i<num_rows-1;++i)
		idx2time_hours.push(0);
	for(var i=0;i<num_rows-1;++i)
	{	
		on_updaterow_impl(fpid[i],i,'all');
	}
	update_clocks();
}





