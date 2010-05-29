
<%inherit file="base.mako"/>

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

<div>
<form>
User name: <input type="text" name="username" value="" /> 

</form>

</div>

