
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

function loadprofile()
{
	document.getElementById('password1').value='';
	document.getElementById('password2').value='';

%if c.changepass:
	document.getElementById('password1').focus();
%endif
}
addLoadEvent(loadprofile);

</script>

<div>
%if c.splash:
<span style="background:#ffb0b0">
${c.splash}
</span><br/>
%endif

<form method="POST" action="${h.url_for(controller="profile",action="save")}">
%if c.initial:
Choose a user name: <input type="text" name="username" value="${c.user}" /> (using your email address is good idea*)<br/>
%endif
%if not c.initial:
Change name: <input type="text" name="username" value="${c.user}" /><br/> 
%endif

%if c.initial:
<div>
%endif
%if not c.initial:
<a href="#" onclick="document.getElementById('password').style.display='block'">Change password</a><br/>
<div id="password" 
%if not c.changepass:
style="display:none"
%endif
%if c.changepass:
style="background:#80ff80"
%endif
>

%endif
Enter a password: <input type="password" name="password1" id="password1" value="" /><br/>
Enter password again: <input type="password" name="password2" id="password2" value="" /><br/>
</div>



%if not c.initial:
Track as line instead of dots (only for fast computers): <input type="checkbox" name="notfastmap" ${'checked="1"' if c.notfastmap else ''|n}"/><br/>

Optional Information, needed to create ATS-flightplans:<br/>
Real Name: <input type="text" name="realname" value="${c.realname}" />(example: Kalle Svensson)<br/> 
Phone Number (including country-code): <input type="text" name="phonenr" value="${c.phonenr}" />(example: +46701234567)<br/> 

%endif
<input type="submit" name="save" value="Save"/>
</form>

<br/>
<br/>


%if c.initial:
<p>
* If you choose to use your email address as your username, you will be able to reset your password if you forget it.
</p>
<br/>
%endif




</div>



