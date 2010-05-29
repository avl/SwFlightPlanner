function get(wcol)
{
	var vid='fplanrow'+idx+wcol;
	var e=document.getElementById(vid);
	if (e==null)
		alert(vid);
	if (e.value=='')
		return 0.0;			
	return parseFloat(e.value);
}
function gete(wcol)
{
	var vid='fplanrow'+idx+wcol;
	var e=document.getElementById(vid);
	return e;
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
	
	var glist=document.getElementById('tab_fplan');
	var params={};
	for(var i=0;i<num_rows;i++)
	{
		var rowelem=glist.rows[i];		
		var namefield=rowelem.cells[1].childNodes[0];
		var posfield=rowelem.cells[2].childNodes[0];
		var origposfield=rowelem.cells[2].childNodes[1];
		params[namefield.name]=namefield.value;
		params[posfield.name]=posfield.value;
		params[origposfield.name]=origposfield.value;
	}			
	params['tripname']=document.getElementById('entertripname').value;
	params['oldtripname']=document.getElementById('oldtripname').value;
	params['showarea']=showarea;
	params['showairspaces']=showairspaces;
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
		var tas=get('TAS');
		var tt=get('TT');
		var wind=get('W');
		var windvel=get('V');
		var variation=get('Var');
		var dev=get('Dev');
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
		var wcae=gete('WCA');
		if (wca>0)
			wcae.value='+'+wca.toFixed(0);
		else
			wcae.value=''+wca.toFixed(0);
		
		var gse=gete('GS');
		gse.value=GS.toFixed(0);
		next=1;	
	}
	if (next || col=='TAS' || col=='W' || col=='V' || col=='Var' || col=='Dev')
	{
		var tt=get('TT');
		var wca=get('WCA');
		var var_=get('Var');
		var dev=get('Dev');
		var ch=gete('CH');
		ch.value=parseInt(0.5+tt+wca-var_-dev)%360;
	}	
	if (next || col=='TAS' || col=='W' || col=='V' || col=='Var' || col=='Dev')
	{
		var gs=get('GS');
		var D=get('D');
		var time=gete('Time');
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
function fpaddwaypoint(pos,name,rowdata)
{
	var noyet=document.getElementById('nowaypointsyet');
	noyet.display='none';
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
	elem.innerHTML='<td colspan="'+fpcolnum+'">#'+idx+': <input type="text" name="name'+idx+'" value="'+name+'"/></td>';
	if (rowdata!=null && rowdata.length>0)
	{
		var elem=tab.insertRow(-1);
		var s='';
		for(var i=0;i<rowdata.length;++i)
		{			
			var ro='';
			var wh=fpcolshort[i];
			if (wh=='TT' || wh=='D' || wh=='GS' || wh=='CH' || wh=='Time') 
				ro='readonly="1"';
			s=s+'<td><input '+ro+' id="fplanrow'+idx+fpcolshort[i]+'" onchange="on_updaterow('+idx+',\''+fpcolshort[i]+'\');" size="'+fpcolwidth[i]+'" title="'+fpcoldesc[i]+' '+fpcolextra[i]+'" type="text" name="row'+i+''+fpcolshort[i]+'" value="'+rowdata[i]+'"/></td>\n';		
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
