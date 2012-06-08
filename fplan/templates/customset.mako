
<%inherit file="base.mako"/>
<script src="/MochiKit.js" type="text/javascript"></script>

<script type="text/javascript">
function navigate_to(where)
{	
	function finish_nav()
	{				
		window.location.href=where;
	}
	finish_nav();
}

function datachanged()
{
	var geb=document.getElementById('save_id');
%if c.havenext:	
	geb.value='Resurrect';
%endif 
}

</script>
<div style="height:100%;width:100%;overflow:auto;">

<h1>${c.setname}</h1>

%if c.flash:
<b style="background-color:#ffb0b0">${c.flash|n}</b><br/>
%endif

<form action="${h.url_for(controller="customsets",action="save",setname=c.setname,version=c.cur)}" method="POST">

<a href="${h.url_for(controller="customsets",action="index")}">Back</a>

%if c.haveprev:
<input type="submit" name="prev_button" value="Prev (${c.cur-1})"/>
%endif
<input type="submit" id="save_id" name="save_button" value="Save"/>

%if c.havenext:
<input type="submit" name="next_button" value="Next (${c.cur+1})"/>
%endif
Version: ${c.cur}<br/>

<input type="checkbox" name="active" ${'checked="1"' if c.active else ''|n}"/> Active (Check this to make data available to you only)<br/>
<input type="checkbox" name="ready" ${'checked="1"' if c.ready else ''|n}"/> Ready (Check this to make data available to general public and in android app)<br/>

<textarea name="data" rows="100" cols="100" onkeydown="datachanged();return 0;" onchange="datachanged();return 0;">
${c.data}
</textarea>

</form>

</div>



