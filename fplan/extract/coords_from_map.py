#!/usr/bin/python
# -*- coding: utf-8 -*-
import wx
import sys
from coord2latlon import parse_line
base=sys.argv[1] #"llf_middle"

filename="/home/anders/saker/avl_fplan_world/%s.png"%(base,)
output=open(base+".txt","a")

class Popup(wx.Frame):
    def __init__(self,parent,cur):
	self.cur=cur
        self.parent=parent

	wx.Frame.__init__(self,None,-1,"Lerad",size=(400,125))
        
        gs=wx.BoxSizer(wx.VERTICAL)

	self.atext=wx.TextCtrl(self,-1,"",size=(400,30))
	
	gs.Add(self.atext)
  
	okbutton=wx.Button(self,-1,"OK")
        okbutton.Bind(wx.EVT_BUTTON,self.okbutton)
        gs.Add(okbutton)
	
	cnclbutton=wx.Button(self,-1,"Cancel")
        cnclbutton.Bind(wx.EVT_BUTTON,self.cnclbutton)
        gs.Add(cnclbutton)
	
        gs.Layout()
	self.atext.SetFocus()
	self.Show()
	okbutton.SetDefault()

    def okbutton(self,event):
	output.write("%s: %s\n"%(self.atext.GetValue(),
	    ";".join("%d,%d"%(p[0],p[1]) for p in self.cur)))
	output.flush()
	self.Close()
	self.parent.history.append(self.cur)
	self.parent.Refresh()


    def cnclbutton(self,event):
	self.Close()



class MainFrame(wx.Frame):
    def __init__(self):
	wx.Frame.__init__(self,None,-1,"Lerad",size=(1000,1000))

	im=wx.Image(filename, wx.BITMAP_TYPE_ANY)
	im.Rescale(1000,1000)
	self.bitmap = im.ConvertToBitmap()	
	self.panel = wx.Panel(self, -1)

	#self.bmp=wx.StaticBitmap(self, -1, bitmap,pos=(0,0),size=(1000,1000))
	self.panel.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
	self.panel.Bind(wx.EVT_RIGHT_DOWN, self.OnRightDown)
	self.panel.Bind(wx.EVT_PAINT,self.OnPaint)
	self.history=[]
        self.panel.Bind(wx.EVT_KEY_DOWN,self.KeyDown)
	self.points=[]

	self.Show(True)	

        self.old=[]
        self.curold=0
        for line in open(base+".txt"):
            print "Line:",line
            if line.strip()=="": continue
            name,coord=parse_line(line,False)
            self.old.append((name,coord))
    def KeyDown(self,event):
        print "Key pressed!"
        if event.KeyCode==ord('A'):
            self.curold+=1
        if event.KeyCode==ord('Z'):
            self.curold-=1
        print "Curr:",self.curold,":",self.old[self.curold][0],'X,Y:',self.old[self.curold][1][0]," #",len(self.old[self.curold][1])
        self.Refresh()
    def OnPaint(self,dummy):
	print "On Paint called"
	dc=wx.PaintDC(self.panel)
	dc.DrawBitmap(self.bitmap,0,0)
	brush=wx.Brush(wx.Colour(0,255,0))
        dc.SetBrush(brush)
	if len(self.points):
	    dc.DrawPolygon([wx.Point(*x) for x in self.points])
	brush=wx.Brush(wx.Colour(255,255,0))
        dc.SetBrush(brush)
	print "History is %d big"%(len(self.history))
	for pointlist in self.history:
	    dc.DrawPolygon([wx.Point(*x) for x in pointlist])
	  
	if self.curold>=0 and self.curold<len(self.old):
            brush=wx.Brush(wx.Colour(0,255,128))
            dc.SetBrush(brush)
            dc.DrawPolygon([wx.Point(*x) for x in self.old[self.curold][1]])

	

    def OnLeftDown(self,event):
	print "left down"
	pt = event.GetPosition()
	self.points.append((pt.x,pt.y))
	self.Refresh()
    def OnRightDown(self,event):
	print "Right down"
	Popup(self,self.points)
	self.points=[]
	self.Refresh()
	
	
myapp=wx.PySimpleApp()
m=MainFrame()
myapp.MainLoop()
