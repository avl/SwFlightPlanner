

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

