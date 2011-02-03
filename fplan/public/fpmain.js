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

function on_update()
{
	save_data(null);
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
        			on_update();
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
		if (req.responseText!='')
		{
					
		    if (!dirty)
		    {
                var e=document.getElementById('printablelink');
                e.innerHTML='<a href="'+printableurl+'"><u>Printable</u></a>';
                var ret=evalJSONRequest(req);
                update_fields(ret);		    
			    if (cont!=null)
			    {
			    	cont();
				}		
		    }
    		else
    		{
    			save_data(cont);
    		}
		}
		else
		{
			alert('Error saving trip');
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
	if (document.getElementById('realname'))
    	params['realname']=document.getElementById('realname').value;
	var def=doSimpleXMLHttpRequest(saveurl,
		params);
	def.addCallback(save_data_cb);
}


function update_fields(data)
{
	for(var i=0;i<data.rows.length;++i)
	{
		var row=data.rows[i];
		var id=row.id;
		
		var wca=row.wca;
		
		var wcae=gete(id,'WCA');
		if (wca>0)
			wcae.value='+'+wca.toFixed(0);
		else
			wcae.value=''+wca.toFixed(0);
		
		var gse=gete(id,'GS');
		gse.value=row.gs.toFixed(0);
		var ch=gete(id,'CH');
		ch.value=row.ch.toFixed(0);
		var time=gete(id,'Time');
		time.value=row.timestr;
	}
	var e=document.getElementById('tottime');
	e.value=data.tottime;

	return;	
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
    dirty=1;
    save_data(null);
}
function format_empty_landingrow(id,idx)
{
    return '<td colspan="'+fpcolnum+'"><table>'+
            '<tr><td>Takeoff date: </td><td><input size="10" type="text" onchange="makedirty()" id="date_of_flight_'+id+'" value=""/>(YYYY-MM-DD)</td></tr>'+
            '<tr><td>Estimated takeoff time (UTC): </td><td><input size="5" type="text" onchange="makedirty();on_update();" id="departure_time_'+id+'" value=""/>(HH:MM) <span style="font-size:10px">(leave blank for touch-and-go)</span></td></tr>'+
            '<tr><td>Fuel at takeoff: </td><td><input size="4" type="text" onchange="makedirty()" id="fuel_'+id+'" value=""/>(L) <span style="font-size:10px">(leave blank if not fueling)</span></td>'+
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

	elem.innerHTML='<td colspan="'+fpcolnum+'">#'+(idx+1)+': <input title="Name of waypoint. Go to map-screen to change." readonly="1" type="text" name="name'+id+'" value="'+name+'"/>'+
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
			s=s+'<td><input '+ro+' id="fplanrow'+id+fpcolshort[i]+'" onkeyup="makedirty();on_update();"  onchange="makedirty();on_update();" size="'+fpcolwidth[i]+'" title="'+fpcoldesc[i]+' '+fpcolextra[i]+'" type="text" name="row'+i+''+fpcolshort[i]+'" value="'+rowdata[i]+'"/></td>\n';		
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

function fpmain_init()
{
}





