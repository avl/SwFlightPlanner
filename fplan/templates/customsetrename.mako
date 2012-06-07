
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

</script>
<div style="height:100%;width:100%;overflow:auto;">

<h1>Custom Data Set ${c.setname}</h1>

<form action="${h.url_for(controller="customsets",action="renamesave")}" method="POST">


New name:<input type="text" name="setname" value="${c.setname}" /><br/>

<input type="hidden" name="oldname" value="${c.setname}" /><br/>
<input type="submit" id="save_id" name="save_button" value="Save"/>
<a href="${h.url_for(controller="customsets",action="index")}">Cancel</a>
</form>

</div>



