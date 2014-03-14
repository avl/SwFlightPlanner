<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>Swflightplanner GPS Log</name>
    <open>1</open>
    <description>GPS Log ${c.start}</description>
 <!-- Normal track style -->
    <Style id="track_n">
      <IconStyle>
        <Icon>
          <href>http://earth.google.com/images/kml-icons/track-directional/track-none.png</href>
        </Icon>
      </IconStyle>
    </Style>
<!-- Highlighted track style -->
    <Style id="track_h">
      <IconStyle>
        <scale>1.2</scale>
        <Icon>
          <href>http://earth.google.com/images/kml-icons/track-directional/track-none.png</href>
        </Icon>
      </IconStyle>
    </Style>
    <StyleMap id="track">
      <Pair>
        <key>normal</key>
        <styleUrl>#track_n</styleUrl>
      </Pair>
      <Pair>
        <key>highlight</key>
        <styleUrl>#track_h</styleUrl>
      </Pair>
    </StyleMap>
<!-- Normal waypoint style -->
    <Style id="waypoint_n">
      <IconStyle>
        <Icon>
          <href>http://maps.google.com/mapfiles/kml/pal4/icon61.png</href>
        </Icon>
      </IconStyle>
    </Style>
<!-- Highlighted waypoint style -->
    <Style id="waypoint_h">
      <IconStyle>
        <scale>1.2</scale>
        <Icon>
          <href>http://maps.google.com/mapfiles/kml/pal4/icon61.png</href>
        </Icon>
      </IconStyle>
    </Style>
    <StyleMap id="waypoint">
      <Pair>
        <key>normal</key>
        <styleUrl>#waypoint_n</styleUrl>
      </Pair>
      <Pair>
        <key>highlight</key>
        <styleUrl>#waypoint_h</styleUrl>
      </Pair>
    </StyleMap>
    <Style id="lineStyle">
      <LineStyle>
        <color>99ffac59</color>
        <width>3</width>
      </LineStyle>
    </Style>   
    
    <Folder>
      <name>Paths</name>

      <description>GPS Log from ${c.start}</description>
        <Placemark>
          <name>Path</name>
          <styleUrl>#lineStyle</styleUrl>
          <LineString>
            <tessellate>1</tessellate>
            <coordinates>
%for (pos1,altmeters1,when1) in c.rec.points:
          ${pos1[1]},${pos1[0]},${altmeters1}
%endfor      
          </coordinates>
        </LineString>
      </Placemark>
    </Folder>
  </Document>
</kml>

