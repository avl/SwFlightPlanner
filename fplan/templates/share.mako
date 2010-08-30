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

<u><a href="${h.url_for(controller="mapview",action="index")}">Back</a></u><br/>

%if c.error:
${c.error}
%endif

%if not c.error:

%if not c.sharing:
You are currently NOT sharing the trip "${c.trip}" with anyone.

<form method="post" action="${h.url_for(controller="mapview",action="updsharing")}">

<input type="submit" name="share" value="Share with Others"/>
</form>
%endif

%if c.sharing:
You are are sharing the trip "${c.trip}" with anyone who has this link:<br/>
<br/>
Copy-paste this link to an email or chat message, and send to someone you want to share this trip with:<br/>
<span style="color:#4040ff">${c.sharelink}</span><br/>
<br/>
Or you can drag-and-drop this link to an email or chat message:<br/>
<a href="${c.sharelink}" style="color:#4040ff">${c.trip}</a><br/>
<br/>

<form method="post" action="${h.url_for(controller="mapview",action="updsharing")}">
<input type="submit" name="stop" value="Stop Sharing"/> <br/>
By pressing the button above, any already distributed links will stop working. This cannot be undone. To enable access by others, you will have to generate a new link and send it to them.
</form>

%endif
%endif

