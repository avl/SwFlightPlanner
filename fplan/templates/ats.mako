<html>

<body>

<h1>${c.trip}</h1>

%for w in c.waypoints:

<p>
<b>${w['name']}</b>:${w['pos']} 
</p>

%endfor

<p>
%for w in c.waypoints:
DCT ${w['pos']} 
%endfor
</p>
</body>

</html>