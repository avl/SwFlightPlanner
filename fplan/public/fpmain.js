modifiable_cols=[];
dirty=0;
in_prog=0;
cache={};
recursion=0;


function get_rownum(searchfpid)
{
	for(var i=0;i<num_rows;++i)
	{
		if (fpid[i]==searchfpid)
			return i;
	}
	return null;
}

function set_calculating()
{
	var e=document.getElementById('progmessage');
	e.innerHTML='Calculating...';
	e.style.display='block';
}
function set_calculating_msg(msg)
{
	var e=document.getElementById('progmessage');
	e.innerHTML=msg;
	e.style.display='block';
}

function clear_calculating()
{
	var e=document.getElementById('progmessage');
	e.innerHTML='';
	e.style.display='none';
}

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
	return e.value;
}
function getf(id,wcol)
{
	var val=get(id,wcol);
	if (val=='')
		return 0.0;
	var pf=parseFloat(val);
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
function on_update_all()
{
	if (recursion!=0) return;
	makedirty();
	clear_fields();
	save_data(null);
}
function on_focus(id,wcol)
{
	function dofocus()
	{
		gete(id,wcol).select();	
	}
	setTimeout(dofocus,0); //Get around chrome-bug
}
function on_keydown(event,id,wcol)
{
	function movefocus(id,wcol)
	{
		var vid='fplanrow'+id+wcol;
		var e=document.getElementById(vid);
		if (e)
		{
			e.focus();			
		}
	}
	if (event.which==38 || event.which==40)
	{
		var row=get_rownum(id);
		if (event.which==38)
		{ //up	
			row-=1;
		}
		if (event.which==40)
		{ //down
			row+=1;
		} 
		if (row<0) row=0;
		if (row>=num_rows) row=num_rows-1;
		movefocus(fpid[row],wcol);
		return false;
	}
}
function on_update(id,wcol)
{
	if (recursion!=0) return;
	var newval=get(id,wcol);
	if (cache[''+id])
	{
		if (''+cache[''+id][wcol]==''+newval)
			return;
	}
	on_update_all();
}


function fetch_winds()
{
	function weather_cb(req)
	{
		if (req.responseText=='')
		{
		 	alert('Failed to fetch weather');
			return;
		}
		weather=evalJSONRequest(req);
		for(var i=0;i<weather.length;++i)
		{
			var w=gete(fpid[i],'W');
			var v=gete(fpid[i],'V');
			if (''+weather[i][0]!='NaN' && weather[i][0]!='')
			{
		        w.value=''+parseInt(parseFloat(weather[i][0]));
		        while (w.value.length<3)
		        {
		        	w.value='0'+w.value;
		        }
		        v.value=parseInt(parseFloat(weather[i][1]));
    		}
		}
		on_update_all();
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

optimize_in_prog=0;
function optimize_alts(strategy)
{
	if (optimize_in_prog!=0 || in_prog) 	
	{
		alert('Optimization or calculation already in progress. Please wait at least 30 seconds (worst case). If it has hung, reload page and try again.');
		return;
	}
	optimize_in_prog=1;
	function do_optimize()
	{
		if (strategy=='fuel')
			set_calculating_msg('Optimizing altitudes for fuel consumption - please wait.');
		else
			set_calculating_msg('Optimizing altitudes for travel time - please wait.');
	
		
		function optimize_cb(req)
		{		
			optimize_in_prog=0;	
			clear_calculating();
			if (req.responseText=='')
			{
				alert('Failed to optimize route. Check if headwind is greater than TAS, or airport elevations exceed climb performance.');
				return;
			}
			optresult=evalJSONRequest(req);
			

			for(var i=0;i<optresult.length;++i)
			{
				var w=gete(fpid[i],'W');
				var v=gete(fpid[i],'V');
				var alt=gete(fpid[i],'Alt');
				
				w.value=''+parseInt(parseFloat(optresult[i][0]));
				v.value=''+parseInt(parseFloat(optresult[i][1]));
				alt.value=''+parseInt(parseFloat(optresult[i][2]));
			}
			makedirty();
			do_save();

		}
		var params={};	
		params['tripname']=tripname;
		params['strategy']=strategy;
		var def=doSimpleXMLHttpRequest(optimizeurl,params);
		def.addCallback(optimize_cb);
	}

        save_data(do_optimize);	    

}

function reset_winds()
{
    for(var i=0;i<num_rows-1;++i)
    {
	var w=gete(fpid[i],'W');
	var v=gete(fpid[i],'V');
	w.value='0';
	v.value='0';
    }
    on_update_all();
    return true;
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
	if (num_rows<=1)
	{
		dirty=0;
		if (cont!=null) cont();
		return;		
	}
    if (in_prog)
    {
    	//alert('too much work!');
        return;
    }
    in_prog=1;
    set_calculating();
	function save_data_cb(req)
	{	
	    in_prog=0;
		if (req.responseText!='')
		{
					
		    if (!dirty)
		    {
	                var e=document.getElementById('printablelink');
        	        e.innerHTML='<a id="actualprintable" href="'+printableurl+'"><u>Printable</u></a>';
        	        var ret=evalJSONRequest(req);
        	        update_fields(ret);		    
			clear_calculating();
   		        if (cont!=null)
			{
			    	cont();			    	
			}		
		    }
	    	    else
	    	    {
	    		save_data(cont);
			return;
	    	    }
		    
		}
		else
		{
			var e=document.getElementById('progmessage');
			e.innerHTML='Error saving trip - check format of entered values.';
			e.style.display='block';
		}
	}
	dirty=0;
	var params={};
	for(var i=0;i<num_rows;i++)
	{
		var ik=fpid[i];
		var val=document.getElementById('name'+ik).value;
		params['name'+ik]=val;
	}
	
	
	for(var i=0;i<num_rows-1;i++)
	{
		cache[''+fpid[i]]={};
		for(var j=0;j<modifiable_cols.length;++j)
		{
		    var wh=modifiable_cols[j];
		    var val;
		    if (wh!='Alt')
		    {       
		        val=getf(fpid[i],wh);
		    }
		    else
		    {
		        val=parsealt(get(fpid[i],wh));
		    }
				cache[''+fpid[i]][wh]=get(fpid[i],wh);
		    //alert('Value:'+val);
		    
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
	if (document.getElementById('realname'))
    	params['realname']=document.getElementById('realname').value;
	var def=doSimpleXMLHttpRequest(saveurl,
		params);
	def.addCallback(save_data_cb);
}


function update_fields(data)
{
	if (num_rows<=1) return;
	recursion=1;
	for(var i=0;i<data.rows.length;++i)
	{
		var row=data.rows[i];
		var id=row.id;
		var wcae=gete(id,'WCA');
		var gse=gete(id,'GS');
		var che=gete(id,'CH');
		var tase=gete(id,'TAS');
		
		if (row.gs!=null && row.ch!=null && row.wca!=null)
		{		
			var wca=row.wca;
			
			if (wca>0)
				wcae.value='+'+wca.toFixed(0);
			else
				wcae.value=''+wca.toFixed(0);
			
			gse.value=row.gs;
			che.value=row.ch;
			if (advanced_model)
				tase.value=row.tas;
		}
		else
		{
			wcae.value="--";
			gse.value="--";
			che.value="--";
			if (advanced_model)
				tase.value='--';
		}
		var time=gete(id,'Time');
		time.value=row.timestr;
		var clock=gete(id,'Clock');
		clock.value=row.clockstr;
	}
	var e=document.getElementById('tottime');
	e.value=data.tottime;
	var e=document.getElementById('totfuel');
	e.value=data.totfuel;
	recursion=0;
	return;	
}

function clear_fields()
{
	recursion=1;
	for(var i=0;i<num_rows-1;++i)
	{
		var id=fpid[i];
		var wcae=gete(id,'WCA');		
		var gse=gete(id,'GS');
		var ch=gete(id,'CH');
		var time=gete(id,'Time');
		var clock=gete(id,'Clock');
		wcae.value='--';
		gse.value='--';
		ch.value='--';
		time.value='--';
		clock.value='--:--';
	}
	var e=document.getElementById('tottime');
	e.value='--';
	recursion=0;

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
        	format_empty_landingrow(landingrow,id,idx);
        }
    }
    else
    {
    	var landingrow=document.getElementById('landingrow'+id);
	while ( landingrow.childNodes.length > 0 )
	    {
		landingrow.removeChild( landingrow.firstChild );
	    } 
    }
    dirty=1;

    save_data(null);
}
function format_empty_landingrow(trelem,id,idx)
{
    while ( trelem.childNodes.length > 0 )
	    {
		trelem.removeChild( trelem.firstChild );
	    } 
    var tdelem = document.createElement("td");
    tdelem.colSpan=''+fpcolnum;
    tdelem.innerHTML='<table>'+
            '<tr><td>Takeoff date: </td><td><input size="10" type="text" onchange="on_update_all()" id="date_of_flight_'+id+'" value=""/>(YYYY-MM-DD)</td></tr>'+
            '<tr><td>Estimated takeoff time (UTC): </td><td><input size="5" type="text" onchange="on_update_all();" id="departure_time_'+id+'" value=""/>(HH:MM) <span style="font-size:10px">(leave blank for touch-and-go)</span></td></tr>'+
            '<tr><td>Fuel at takeoff: </td><td><input size="4" type="text" onchange="on_update_all()" id="fuel_'+id+'" value=""/>(L) <span style="font-size:10px">(leave blank if not fueling)</span></td>'+
            '<tr><td>Persons on board: </td><td><input size="4" type="text" onchange="makedirty()" id="persons_'+id+'" value=""/></td></tr>'+
        	'</table>';
    trelem.appendChild(tdelem);
}
function fpaddwaypoint(idx,pos,name,rowdata,altitude,stay)
{
	var id=fpid[idx];
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

	if (idx==0)
	{
		clockstr="";
	}
	else
	{
		var previd=fpid[idx-1];
		clockstr='<input readonly="1" id="fplanrow'+previd+'Clock" size="4" title="The time at which you arrive at this waypoint." type="text" name="row'+previd+'Clock" value=""/>';		
	}
	var wpname = document.createElement("td");
	wpname.colSpan=''+fpcolnum;
	wpname.innerHTML='#'+(idx+1)+': <input title="Name of waypoint. Go to map-screen to change." type="text" name="name'+id+'" onchange="makedirty();" onkeydown="makedirty();" id="name'+id+'" value="'+name+'"/>'+
		clockstr+landheres;
	elem.appendChild(wpname);
	    

	if (rowdata!=null && rowdata.length>0)
	{
	
	
		var elem=tab.insertRow(-1);
		for(var i=0;i<rowdata.length;++i)
		{	
			var tdelem = document.createElement("td");

			var ro='';
			var wh=fpcolshort[i];
			if (wh=='Clock')
				continue;
			if (wh=='TT' || wh=='D' || wh=='GS' || wh=='CH' || wh=='Time' || wh=='WCA' || wh=='Var' || (wh=='TAS' && advanced_model))
			{  
				ro='readonly="1"';
			}
			else
			{
				ro='onkeyup="on_update('+id+',\''+wh+'\')" onfocus="on_focus('+id+',\''+wh+'\')" onkeydown="on_keydown(event,'+id+',\''+wh+'\')" onchange="on_update('+id+',\''+wh+'\')"'; 
			    modifiable_cols.push(wh);
			}
			tdelem.innerHTML='<input '+ro+' id="fplanrow'+id+fpcolshort[i]+'" size="'+fpcolwidth[i]+'" onkeypress="return not_enter(event );" title="'+fpcoldesc[i]+' '+fpcolextra[i]+'" type="text" name="row'+id+''+fpcolshort[i]+'" value="'+rowdata[i]+'"/>';	
			elem.appendChild(tdelem);
		}
		
		landelem.id='landingrow'+id;
        
        if (stay.length && idx!=0)
        {
            var date=stay[0];
            var time=stay[1];
            var fuel=stay[2];
            var persons=stay[3];
		format_empty_landingrow(landelem,id,idx);
        	landelem.cells[0].childNodes[0].rows[0].cells[1].childNodes[0].value=date;
        	landelem.cells[0].childNodes[0].rows[1].cells[1].childNodes[0].value=time;
        	landelem.cells[0].childNodes[0].rows[2].cells[1].childNodes[0].value=fuel;
        	landelem.cells[0].childNodes[0].rows[3].cells[1].childNodes[0].value=persons;
		}		
	}
}

function fpmain_init()
{
}





