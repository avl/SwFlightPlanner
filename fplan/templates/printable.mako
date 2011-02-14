<h1>${c.departure} - ${c.arrival}</h1>

%if min(r.accum_fuel_burn for r in c.route)<0:
<span style="font-size:20px;color:#ff0000">
DON'T FLY! YOU DON'T HAVE ENOUGH FUEL!
</span>
%endif

%if len(c.route)>=2 and min( (next.depart_dt-prev.arrive_dt) for prev,next in zip(c.route,c.route[1:]))<-h.timedelta(seconds=1):
<span style="font-size:20px;color:#ff0000">
DEPARTURE IS BEFORE ARRIVAL, FOR SOME WAYPOINTS!
</span>
%endif

<table>
<tr>
<td style="font-size:12px">Date:</td><td>${c.route[0].depart_dt.strftime("%Y-%m-%d")}</td>
%if c.ac and c.ac.aircraft:
<td style="font-size:12px">Aircraft:</td><td> ${c.ac.aircraft}</td>
%endif
</tr>
<tr><td style="font-size:12px">Total time:</td><td>${h.timefmt(c.route[-1].accum_time_hours)}</td>
<td style="font-size:12px">Total distance:</td><td>${"%.1f"%(c.route[-1].accum_dist,)}NM</td></tr>
<tr><td style="font-size:12px">Initial fuel:</td><td>${c.startfuel}L</td>
<td style="font-size:12px">Fuel needed:</td><td>${"%.1f"%(sum(r.fuel_burn for r in c.route),)}L</td>
<td style="font-size:12px">Number of fuel stops:</td><td>${sum(1 if (x.a.stay and (x.a.stay.fuel>0 or x.a.stay.fueladjust>0)) else 0 for x in c.route[1:])}</td>
</tr>
<tr>
<td style="font-size:12px">Reserve:</td><td>${c.reserve_endurance}</td>
<td style="font-size:12px">Sunrise:</td><td>${c.sunrise}<span style="font-size:10px">(at start)</span></td>
<td style="font-size:12px">Sunset:</td><td>${c.sunset}<span style="font-size:10px">(earliest enroute)</span></td>
</tr>
</table>

<table border="1" width="100%"> 
<tr><td colspan="7" style="font-size:16px">
<b>${c.route[0].a.waypoint}</b>
<span style="font-size:10px">Start:</span>${c.route[0].depart_dt.strftime("%H:%M")}
<span style="font-size:10px">Fuel:</span>${"%.1f"%(c.startfuel)}<span style="font-size:10px">L</span>
<span style="font-size:10px">Terrain:</span>${"%.0f"%(c.route[0].startelev,)}<span style="font-size:10px">ft</span>
</td></tr>
%for rt,next_rt in h.izip(c.route,h.chain(c.route[1:],[None])):
<tr>
<td><span style="font-size:10px">CH:</span>${"%03.0f"%(rt.ch,)}</td>
<td><span style="font-size:10px">D:</span>${"%.0f"%(rt.d,)}<span style="font-size:10px">NM</span></td>
<td><span style="font-size:10px">Obst-free alt.:</span>${"%.0f"%(rt.maxobstelev+500,)}<span style="font-size:10px">ft</span></td>
<td><span style="font-size:10px">W:</span>${"%.0f"%(rt.windvel,)}<span style="font-size:10px">kt@</span>${"%03.0f"%(rt.winddir,)}<span style="font-size:10px">°</span></td>
<td><span style="font-size:10px">Alt:</span>${rt.altitude.replace(" ","&nbsp;")|n}</td>
<td><span style="font-size:10px">TAS:</span>${rt.tas}<span style="font-size:10px">kt</span></td>
<td><span style="font-size:10px">Time:</span>${h.timefmt(rt.time_hours)}</td>
</tr>

%if len(rt.notampoints)>0:
<tr style="font-size:11px">
<td colspan="7">There ${"are" if len(rt.notampoints)>1 else "is"} ${len(rt.notampoints)} NOTAM${"s" if len(rt.notampoints)>1 else ""} for this leg.</td>
</tr>
%endif
%if len(rt.freqset)>0:
<tr style="font-size:11px">
<td colspan="7">
%for name,freqs in sorted(rt.freqset.items()):
<b>${name}</b>
%for freq in freqs:
${freq}
%endfor
%endfor
</td>
</tr>
%endif

<tr><td colspan="7" style="font-size:16px">
<b>${rt.b.waypoint}</b>
<span style="font-size:10px">ETA: </span>${rt.arrive_dt.strftime("%H:%M")} 
%if rt.b.stay and next_rt!=None:
<span style="font-size:10px">Depart: </span>${next_rt.depart_dt.strftime("%H:%M")} 
%endif

%if rt.b.stay==None: 

%if rt.accum_fuel_burn<=0:
<span style="font-size:10px">Fuel: </span><span style="color:#ff0000">EMPTY!</span>(${"%.1f"%(-rt.accum_fuel_burn,)}L SHORT)
%endif
%if rt.accum_fuel_burn>0:
<span style="font-size:10px">Fuel left: </span>${"%.1f"%(rt.accum_fuel_burn,)}
<span style="font-size:10px">L</span>
%endif

%endif

%if rt.b.stay!=None: 
%if not (rt.accum_fuel_burn<0):

%if rt.b.stay.fueladjust==None:
%if rt.b.stay.fuel!=None and rt.b.stay.fuel>0:
<span style="font-size:10px">Fuel left: </span>${"%.1f"%(rt.accum_fuel_burn,)}<span style="font-size:10px">L Fill tanks to: </span>${"%.1f"%(rt.b.stay.fuel,)}<span style="font-size:10px">L</span>
%endif
%if (rt.b.stay.fuel==None or rt.b.stay.fuel<=0):
<span style="font-size:10px">Fuel left: </span>${"%.1f"%(rt.accum_fuel_burn,)}<span style="font-size:10px">L</span>
%endif
%endif
%if rt.b.stay.fueladjust!=None:
%if rt.b.stay.fueladjust<0:
<span style="font-size:10px">Fuel left: </span>${"%.1f"%(rt.accum_fuel_burn,)}
<span style="font-size:10px">L Drain: </span>${"%.1f"%(abs(rt.b.stay.fueladjust),)}
%endif
%if rt.b.stay.fueladjust>0:
<span style="font-size:10px">Fuel left: </span>${"%.1f"%(rt.accum_fuel_burn,)}
<span style="font-size:10px">L Add: </span>${"%.1f"%((rt.b.stay.fueladjust),)}
%endif
<span style="font-size:10px">L Giving a total of: </span>${"%.1f"%((rt.accum_fuel_burn+rt.b.stay.fueladjust),)}
<span style="font-size:10px">L</span>
%endif
%endif



%endif



<span style="font-size:10px">Terrain: </span>${"%.0f"%(rt.endelev,)}<span style="font-size:10px">ft</span>
</td>
</tr>

%endfor

</table>
<a style="font-size:10px" href="${h.url_for(controller="flightplan",action="index")}"><u>Back</u></a>


