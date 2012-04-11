<h1>${c.trip}</h1>

%if min(r.accum_fuel_left for r in c.route)<0:
<span style="font-size:20px;color:#ff0000">
DON'T FLY! YOU DON'T HAVE ENOUGH FUEL!
</span><br/>
%endif

%if len(c.route)>=2 and min( ((next.depart_dt-prev.arrive_dt) if next.depart_dt and prev.arrive_dt else h.timedelta(seconds=1)) for prev,next in zip(c.route,c.route[1:]))<-h.timedelta(seconds=1):
<span style="font-size:20px;color:#ff0000">
DEPARTURE IS BEFORE ARRIVAL, FOR SOME WAYPOINTS!<br/>
</span>
%endif

%if any(rt.time_hours==None for rt in c.route):  
<span style="font-size:20px;color:#ff0000">
EXPECTED HEADWIND IS GREATER THAN TAS!<br/>
</span>
%endif

<table>
<tr>
<td style="font-size:12px">Date:</td><td>${c.route[0].depart_dt.strftime("%Y-%m-%d") if c.route[0].depart_dt else '--'}</td>
%if c.ac and c.ac.aircraft:
<td style="font-size:12px">Aircraft:</td><td> ${c.ac.aircraft}</td>
%endif
</tr>
<tr><td style="font-size:12px">Total time:</td><td>${h.timefmt(c.route[-1].accum_time_hours)}</td>
<td style="font-size:12px">Total distance:</td><td>${"%.1f"%(c.route[-1].accum_dist,)}NM</td></tr>
<tr><td style="font-size:12px">Initial fuel:</td><td>${c.startfuel}L</td>
<td style="font-size:12px">Fuel needed:</td><td>${"%.1f"%(sum(r.fuel_burn for r in c.route if r.fuel_burn),)}L</td>
<td style="font-size:12px">Number of fuel stops:</td><td>${sum(1 if (x.a.stay and x.is_start and (x.a.stay.fuel>0 or x.a.stay.fueladjust>0)) else 0 for x in c.route[1:])}</td>
</tr>
<tr>
<td style="font-size:12px">Reserve:</td><td>${c.reserve_endurance}</td>
<td style="font-size:12px">Sunrise (at start):</td><td>${c.sunrise}</td>
<td style="font-size:12px">Sunset (earliest enroute):</td><td>${c.sunset}</td>
</tr>
</table>

<table border="1" cellspacing="0" cellpadding="4" width="100%"> 
<tr><td colspan="${6 if c.fillable else 9}" style="font-size:16px">
<b>${c.route[0].a.waypoint}</b>
<span style="font-size:10px">Start:</span><b>${c.route[0].depart_dt.strftime("%H:%M") if c.route[0].depart_dt else '--'}</b>
%if c.ac!=None:
<span style="font-size:10px">Fuel:</span>${"%.1f"%(c.startfuel)}<span style="font-size:10px">L</span>
%endif
<span style="font-size:10px">Terrain:</span>${"%.0f"%(c.route[0].startelev,)}<span style="font-size:10px">ft</span>
</td>

%if c.fillable:
<td>
<span style="font-size:10px">Actual start:</span>&nbsp;&nbsp;&nbsp;&nbsp;
</td>
<td>
<span style="font-size:10px">delay:</span>&nbsp;&nbsp;&nbsp;&nbsp;
</td>
<td>
<span style="font-size:10px">acc. delay:</span>&nbsp;&nbsp;&nbsp;&nbsp;
</td>
%endif


</tr>
%for rt,next_rt in h.izip(c.route,h.chain(c.route[1:],[None])):
<tr>
<td>
%if not rt.what:
&nbsp;
%endif
%if rt.what:
<span style="font-size:10px">${rt.what}</span>
%endif
</td>
<td><span style="font-size:10px">CH:</span>${"%03.0f"%(rt.ch,)}° <span style="font-size:10px">TT:</span>${"%03.0f"%(rt.tt,)}°</td>
<td><span style="font-size:10px">D:</span>${"%.0f"%(rt.d,)}<span style="font-size:10px">NM</span></td>
<td><span style="font-size:10px">Obst-free alt.:</span>${"%.0f"%(rt.maxobstelev+1000,)}<span style="font-size:10px">ft</span></td>
<td><span style="font-size:10px">W:</span>${"%.0f"%(rt.windvel,)}<span style="font-size:10px">kt@</span>${"%03.0f"%(rt.winddir,)}°</td>
<td><span style="font-size:10px">Alt:</span>${rt.altitude.replace(" ","&nbsp;")|n}</td>
<td>
  <span style="font-size:10px">TAS:</span>${"%.0f"%(rt.tas,) if rt.tas else '-'}<span style="font-size:10px">kt</span>
  <span style="font-size:10px">GS:</span>${"%.0f"%(rt.gs,) if rt.gs else '-'}<span style="font-size:10px">kt</span>
</td>
<td><span style="font-size:10px">Time:</span>${h.timefmt(rt.time_hours)}</td>
<td><span style="font-size:10px">Total time:</span>${h.timefmt(rt.accum_time_hours)}</td>
</tr>
%if rt.is_end:

%if len(rt.notampoints)>0:
<tr style="font-size:11px">
<td>&nbsp;</td>
<td colspan="8">There ${"are" if len(rt.notampoints)>1 else "is"} ${len(rt.notampoints)} NOTAM${"s" if len(rt.notampoints)>1 else ""} for this leg.</td>
</tr>
%endif
%if len(rt.freqset)>0:
<tr style="font-size:11px">
<td>&nbsp;</td>
<td colspan="8">
%for name,freqs in sorted(rt.freqset.items()):
<b>${name}</b>
%for freq in freqs:
${freq}
%endfor
%endfor
</td>
</tr>
%endif

<tr><td colspan="${6 if c.fillable else 9}" style="font-size:16px">
<b>${rt.b.waypoint}</b>

%if c.ac!=None:
%if rt.b.stay==None: 

%if rt.accum_fuel_left<=0:
<span style="font-size:10px">Fuel: </span><span style="color:#ff0000">EMPTY!</span>(${"%.1f"%(-rt.accum_fuel_left,) if rt.accum_fuel_left else '-'}L SHORT)
%endif
%if rt.accum_fuel_left>0:
<span style="font-size:10px">Fuel left: </span>${"%.1f"%(rt.accum_fuel_left,) if rt.accum_fuel_left else '-'}
<span style="font-size:10px">L</span>
%endif

%endif

%if rt.b.stay!=None: 
%if not (rt.accum_fuel_left<0):

%if rt.b.stay.fueladjust==None:
%if rt.b.stay.fuel!=None and rt.b.stay.fuel>0:
<span style="font-size:10px">Fuel left: </span>${"%.1f"%(rt.accum_fuel_left,) if rt.accum_fuel_left else '-'}<span style="font-size:10px">L Fill tanks to: </span>${"%.1f"%(rt.b.stay.fuel,)}<span style="font-size:10px">L</span>
%endif
%if (rt.b.stay.fuel==None or rt.b.stay.fuel<=0):
<span style="font-size:10px">Fuel left: </span>${"%.1f"%(rt.accum_fuel_left,) if rt.accum_fuel_left else '-'}<span style="font-size:10px">L</span>
%endif
%endif
%if rt.b.stay.fueladjust!=None:
%if rt.b.stay.fueladjust<0:
<span style="font-size:10px">Fuel left: </span>${"%.1f"%(rt.accum_fuel_left,) if rt.accum_fuel_left else '-'}
<span style="font-size:10px">L Drain: </span>${"%.1f"%(abs(rt.b.stay.fueladjust),)}
%endif
%if rt.b.stay.fueladjust>0:
<span style="font-size:10px">Fuel left: </span>${"%.1f"%(rt.accum_fuel_left,) if rt.accum_fuel_left else '-'}
<span style="font-size:10px">L Add: </span>${"%.1f"%((rt.b.stay.fueladjust),)}
%endif
<span style="font-size:10px">L Giving a total of: </span>${"%.1f"%((rt.accum_fuel_left+rt.b.stay.fueladjust),) if rt.accum_fuel_left else '-'}
<span style="font-size:10px">L</span>
%endif
%endif


%endif
%endif
<span style="font-size:10px">Terrain: </span>${"%.0f"%(rt.endelev,)}<span style="font-size:10px">ft</span>

<span style="font-size:10px"><b>ETA:</b> </span><b>${rt.arrive_dt.strftime("%H:%M") if rt.arrive_dt else '--'}</b> 
%if rt.b.stay and next_rt!=None:
<span style="font-size:10px">Depart: </span>${next_rt.depart_dt.strftime("%H:%M") if next_rt.depart_dt else '--'} 
%endif

</td>

%if c.fillable:
<td>
<span style="font-size:10px">ATA:</span>&nbsp;&nbsp;&nbsp;&nbsp;
</td>
<td>
<span style="font-size:10px">delay:</span>&nbsp;&nbsp;&nbsp;&nbsp;
</td>
<td>
<span style="font-size:10px">acc. delay:</span>&nbsp;&nbsp;&nbsp;&nbsp;
</td>
%endif


</tr>
%endif

%endfor

</table>
<a style="font-size:10px" href="${h.url_for(controller="flightplan",action="index")}"><u>Back</u></a>


