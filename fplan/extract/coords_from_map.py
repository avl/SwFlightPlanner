#!/usr/bin/python
# -*- coding: utf-8 -*-
import wx
base="llf_middle"
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
	
	#self.bmp=wx.StaticBitmap(self, -1, bitmap,pos=(0,0),size=(1000,1000))
	self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
	self.Bind(wx.EVT_RIGHT_DOWN, self.OnRightDown)
	self.Bind(wx.EVT_PAINT,self.OnPaint)
	self.history=[]
	self.Show(True)	

	self.points=[]

    def OnPaint(self,dummy):
	print "On Paint called"
	dc=wx.PaintDC(self)
	dc.DrawBitmap(self.bitmap,0,0)
	brush=wx.Brush(wx.Colour(0,255,0))
        dc.SetBrush(brush)
	if len(self.points):
	    dc.DrawPolygon([wx.Point(*x) for x in self.points])
	brush=wx.Brush(wx.Colour(255,255,0))
        dc.SetBrush(brush)
	print "History is %d big"%(len(self.history))
	for points in self.history:
	    dc.DrawPolygon([wx.Point(*x) for x in points])
	  
	
	

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
