W;V;Temp;Alt;TAS;TT;wca;TH;var;MH;dev;CH;D;GS;Waypoint
%for wp in c.waypoints:
%for what in ['winddir','windvel','','altitude','tas','tt','wca','th','variation','mh','deviation','ch','d','gs']:
%if what:
${getattr(wp,what) if getattr(wp,what)!="" else 0};\
%endif
%if not what:
;\
%endif
%endfor
"${wp.b.waypoint.replace('"',"'")}"
%endfor
