<h1>${c.departure} - ${c.arrival}</h1>

%if c.startfuel<c.route[-1].accum_fuel_burn:
<span style="font-size:20px">
DON'T FLY! YOU DON'T HAVE ENOUGH FUEL!
</span>
%endif
<table>
%if c.ac and c.ac.aircraft:
<tr><td style="font-size:12px">Aircraft:</td><td> ${c.ac.aircraft}</td></tr>
%endif
<tr><td style="font-size:12px">Total time:</td><td>${c.route[-1].accum_time}</td>
<td style="font-size:12px">Total distance:</td><td>${"%.1f"%(c.route[-1].accum_dist,)}NM</td></tr>
<tr><td style="font-size:12px">Fuel on board:</td><td>${c.startfuel}L</td>
<td style="font-size:12px">Fuel needed:</td><td>${"%.1f"%(c.route[-1].accum_fuel_burn,)}L</td></tr>
<tr><td style="font-size:12px">Reserve:</td><td>${c.reserve_endurance}</td></tr>
</table>

<table border="1" width="100%"> 
<tr><td colspan="6" style="font-size:16px">
<b>${c.route[0].a.waypoint}</b>
<span style="font-size:10px">Start:</span>0h0m
<span style="font-size:10px">Fuel:</span>${"%.1f"%(c.startfuel)}<span style="font-size:10px">L</span>
<span style="font-size:10px">Terrain:</span>${"%.0f"%(c.route[0].startelev,)}<span style="font-size:10px">ft</span>
</td></tr>
%for rt in c.route:
<tr>
<td><span style="font-size:10px">CH:</span>${"%.0f"%(rt.ch,)}</td>
<td><span style="font-size:10px">D:</span>${"%.0f"%(rt.d,)}<span style="font-size:10px">NM</span></td>
<td><span style="font-size:10px">Obst-free alt.:</span>${"%.0f"%(rt.maxobstelev+500,)}<span style="font-size:10px">ft</span></td>
<td><span style="font-size:10px">W:</span>${"%.0f"%(rt.windvel,)}<span style="font-size:10px">kt@</span>${"%03.0f"%(rt.winddir,)}<span style="font-size:10px">dgr</span></td>
<td><span style="font-size:10px">Alt:</span>${rt.altitude.replace(" ","&nbsp;")|n}</td>
<td><span style="font-size:10px">Tas:</span>${rt.tas}<span style="font-size:10px">kt</span></td>
</tr>

%if len(rt.notampoints)>0:
<tr style="font-size:11px">
<td colspan="6">There ${"are" if len(rt.notampoints)>1 else "is"} ${len(rt.notampoints)} NOTAM${"s" if len(rt.notampoints)>1 else ""} for this leg.</td>
</tr>
%endif

<tr><td colspan="6" style="font-size:16px">
<b>${rt.b.waypoint}</b>
<span style="font-size:10px">ETA</span>${rt.accum_time}
%if rt.accum_fuel_burn>c.startfuel:
<span style="font-size:10px">Fuel</span><span style="color:#ff0000">EMPTY!</span>(${"%.1f"%(-(c.startfuel-rt.accum_fuel_burn),)}L SHORT)
%endif
%if rt.accum_fuel_burn<=c.startfuel:
<span style="font-size:10px">Fuel</span>${"%.1f"%(c.startfuel-rt.accum_fuel_burn,)}<span style="font-size:10px">L</span>
%endif
<span style="font-size:10px">Terrain:</span>${"%.0f"%(rt.endelev,)}<span style="font-size:10px">ft</span>
</td>
</tr>

%endfor

</table>
<a style="font-size:10px" href="${h.url_for(controller="flightplan",action="index")}"><u>Back</u></a>


