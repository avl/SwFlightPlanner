function showhide_filter()
{
    var d=document.getElementById('popup_category').style;
    if (d.display=='block') 
        d.display='none';
    else 
        d.display='block';
    return false;
}
function filtercat()
{
    var tab=document.getElementById('filtercattable');
	var freetext=document.getElementById('searchcat').value;
	freetext=freetext.replace('Å','A');
	freetext=freetext.replace('å','a');
	freetext=freetext.replace('Ä','A');
	freetext=freetext.replace('ä','a');
	freetext=freetext.replace('Ö','O');
	freetext=freetext.replace('ö','o');
	var freetextregexp=new RegExp(freetext,'i');
	for(var i=0;i<tab.rows.length;i++)
	{
		var rowelem=tab.rows[i];
		//var namefield=rowelem.cells[1].childNodes[0];
		var cat=rowelem.cells[0].childNodes[0].name;
		var check=rowelem.cells[0].childNodes[0].checked;
		if (freetext=='' || cat.search(freetextregexp)!=-1)
    		rowelem.style.display='table-row';		    
        else
    		rowelem.style.display='none';		            
    }    
}
inprog=[];
queued=[];
function mark_notam(notam,line,marked)
{

    if (inprog.length>0)
    {
        queued.push([notam,line,marked]);
        return;
    }
	function toggle_cb(req)
	{	
		if (req.responseText!='')
		{
			var toggled=evalJSONRequest(req);
			for(var i=0;i<toggled.length;i++)
			{
			    var tid='notamcolor_'+toggled[i][0]+'_'+toggled[i][1];
			    var dive=document.getElementById(tid);
                if (toggled[i][2]==1)
                    dive.style.backgroundColor='#b0ffb0';
                else
                    dive.style.backgroundColor='#ffd0b0';
			}
			if (queued.length)
			{
	            var params={};	
	            inprog=queued;
	            queued=[];
            	params['toggle']=serializeJSON(inprog);
	            var def=doSimpleXMLHttpRequest(marknotamurl,params);
	            def.addCallback(toggle_cb);			
			}
			else
			{
			    inprog=[];
			}
		}
	}
    inprog=queued;
    queued=[];
    inprog.push([notam,line,marked]);
	var params={};	
	params['toggle']=serializeJSON(inprog);
	var def=doSimpleXMLHttpRequest(marknotamurl,params);
	def.addCallback(toggle_cb);
}
function click_item(notam,line,already_toggled)
{

    var e=document.getElementById('notam_'+notam+'_'+line);
    if (already_toggled==0)
    {
        if (e.checked)        
            e.checked=undefined;
        else
            e.checked='1';
    }
    if (e.checked)
        mark_notam(notam,line,1);
    else        
        mark_notam(notam,line,0);       
}

