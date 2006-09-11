#!/usr/bin/env python
# -*- coding: UTF-8 -*-

""" 
	Simple Function Graph Plotter
	© Thomas Führinger, Sam Tygier 2005-2006
	http://lybniz2.sourceforge.net/
	
	Version 1.1
	Requires PyGtk 2.6	
	Released under the terms of the revised BSD license
	Modified: 2006-07-18
"""
from __future__ import division
import gtk, pango, sys
import math
from math import *

# profiling
enable_profiling = True
if enable_profiling:
	from time import time

AppWin = None
Actions = gtk.ActionGroup("General")
Graph = None
ConnectPoints = True

x_res = 1

xMax = "5.0"
xMin = "-5.0"
xScale = "1.0"

yMax = "3.0"
yMin = "-3.0"
yScale = "1.0"

y1 = "sin(x)"
y2 = ""
y3 = ""

# create a safe namespace for the eval()s in the graph drawing code
def sub_dict(somedict, somekeys, default=None):
	return dict([ (k, somedict.get(k, default)) for k in somekeys ])
# a list of the functions from math that we want.
safe_list = ['math','acos', 'asin', 'atan', 'atan2', 'ceil', 'cos', 'cosh', 'degrees', 'e', 'exp', 'fabs', 'floor', 'fmod', 'frexp', 'hypot', 'ldexp', 'log', 'log10', 'modf', 'pi', 'pow', 'radians', 'sin', 'sinh', 'sqrt', 'tan', 'tanh']
safe_dict = sub_dict(locals(), safe_list)

#add any needed builtins back in.
safe_dict['abs'] = abs

def marks(min_val,max_val,minor=1):
	"yield positions of scale marks between min and max. For making minor marks, set minor to the number of minors you want between majors"
	try:
		min_val = float(min_val)
		max_val = float(max_val)
	except:
		print "needs 2 numbers"
		raise ValueError

	if(min_val >= max_val):
		print "min bigger or equal to max"
		raise ValueError		

	a=0.2 # tweakable control for when to switch scales
	          # big a value results in more marks

	a = a + log10(minor)

	width = max_val - min_val
	log10_range = log10(width)

	interval = 10 ** int(floor(log10_range - a))
	lower_mark = min_val - fmod(min_val,interval)
	
	if lower_mark < min_val:
		lower_mark += interval

	a_mark = lower_mark
	while a_mark <= max_val:
		if abs(a_mark) < interval / 2:
			a_mark = 0
		yield a_mark
		a_mark += interval


class GraphClass:
	def __init__(self):	

		# Create backing pixmap of the appropriate size
		def ConfigureEvent(Widget, Event):
			x, y, w, h = Widget.get_allocation()
			self.PixMap = gtk.gdk.Pixmap(Widget.window, w, h)
			
			# make colors
			self.gc = dict()
			for name, color in (('black',(0,0,0)),('red',(32000,0,0)),('blue',(0,0,32000)),('green',(0,32000,0))):
				self.gc[name] =self.PixMap.new_gc()
				self.gc[name].set_rgb_fg_color(gtk.gdk.Color(red=color[0],green=color[1],blue=color[2]))
			self.layout = pango.Layout(Widget.create_pango_context())
			self.CanvasWidth = w
			self.CanvasHeight = h
			self.xMax = eval(xMax,{"__builtins__":{}},safe_dict)
			self.xMin = eval(xMin,{"__builtins__":{}},safe_dict)
			self.xScale = eval(xScale,{"__builtins__":{}},safe_dict)
			self.yMax = eval(yMax,{"__builtins__":{}},safe_dict)
			self.yMin = eval(yMin,{"__builtins__":{}},safe_dict)
			self.yScale = eval(yScale,{"__builtins__":{}},safe_dict)
			self.ScaleStyle = "dec" # should be set from gui
			self.Plot()
			return True

		# Redraw the screen from the backing pixmap
		def ExposeEvent(Widget, Event):
			x, y, w, h = Event.area
			Widget.window.draw_drawable(Widget.get_style().fg_gc[gtk.STATE_NORMAL], self.PixMap, x, y, x, y, w, h)
			return False

		# Start marking selection
		def ButtonPressEvent(Widget, Event):
			global xSel, ySel
			
			if Event.button == 1:
				self.Selection[0][0], self.Selection[0][1] = int(Event.x), int(Event.y)
				self.Selection[1][0], self.Selection[1][1] = None, None

		# End of selection
		def ButtonReleaseEvent(Widget, Event):
			
			if Event.button == 1 and Event.x != self.Selection[0][0] and Event.y != self.Selection[0][1]:
				xmi, ymi = min(self.GraphX(self.Selection[0][0]), self.GraphX(Event.x)), min(self.GraphY(self.Selection[0][1]), self.GraphY(Event.y))
				xma, yma = max(self.GraphX(self.Selection[0][0]), self.GraphX(Event.x)), max(self.GraphY(self.Selection[0][1]), self.GraphY(Event.y))
				self.xMin, self.yMin, self.xMax, self.yMax = xmi, ymi, xma, yma
				ParameterEntriesRepopulate()
				Graph.Plot()
				self.Selection[1][0] = None
				self.Selection[0][0] = None

		# Draw rectangle during mouse movement
		def MotionNotifyEvent(Widget, Event):
			
			if Event.is_hint:
				x, y, State = Event.window.get_pointer()
			else:
				x = Event.x
				y = Event.y
				State = Event.state

			if State & gtk.gdk.BUTTON1_MASK and self.Selection[0][0] is not None:
				gc = self.DrawingArea.get_style().black_gc
				gc.set_function(gtk.gdk.INVERT)
				if self.Selection[1][0] is not None:
					x0 = min(self.Selection[1][0], self.Selection[0][0])
					y0 = min(self.Selection[1][1], self.Selection[0][1])
					w = abs(self.Selection[1][0] - self.Selection[0][0])
					h = abs(self.Selection[1][1] - self.Selection[0][1])
					self.PixMap.draw_rectangle(gc, False, x0, y0, w, h)
				x0 = min(self.Selection[0][0], int(x))
				y0 = min(self.Selection[0][1], int(y))
				w = abs(int(x) - self.Selection[0][0])
				h = abs(int(y) - self.Selection[0][1])
				self.PixMap.draw_rectangle(gc, False, x0, y0, w, h)
				self.Selection[1][0], self.Selection[1][1] = int(x), int(y)
				self.DrawDrawable()
				
		self.PrevY = [None, None, None]
		
		# Marked area point[0, 1][x, y]
		self.Selection = [[None, None], [None, None]]
		
		self.DrawingArea = gtk.DrawingArea()		
		self.DrawingArea.connect("expose_event", ExposeEvent)
		self.DrawingArea.connect("configure_event", ConfigureEvent)
		self.DrawingArea.connect("button_press_event", ButtonPressEvent)
		self.DrawingArea.connect("button_release_event", ButtonReleaseEvent)
		self.DrawingArea.connect("motion_notify_event", MotionNotifyEvent)
		self.DrawingArea.set_events(gtk.gdk.EXPOSURE_MASK | gtk.gdk.LEAVE_NOTIFY_MASK | gtk.gdk.BUTTON_PRESS_MASK | gtk.gdk.BUTTON_RELEASE_MASK | gtk.gdk.POINTER_MOTION_MASK |gtk.gdk.POINTER_MOTION_HINT_MASK)

	def DrawDrawable(self):
		x, y, w, h = self.DrawingArea.get_allocation()
		self.DrawingArea.window.draw_drawable(self.DrawingArea.get_style().fg_gc[gtk.STATE_NORMAL], self.PixMap, 0, 0, 0, 0, w, h)
		
	def Plot(self):
		self.PixMap.draw_rectangle(self.DrawingArea.get_style().white_gc, True, 0, 0, self.CanvasWidth, self.CanvasHeight)
				
		if (self.ScaleStyle == "cust"):
			
			#draw cross
			self.PixMap.draw_lines(self.gc['black'], [(int(round(self.CanvasX(0))),0),(int(round(self.CanvasX(0))),self.CanvasHeight)])
			self.PixMap.draw_lines(self.gc['black'], [(0,int(round(self.CanvasY(0)))),(self.CanvasWidth,int(round(self.CanvasY(0))))])
			# old style axis marks
			iv = self.xScale * self.CanvasWidth/(self.xMax - self.xMin) # pixel interval between marks
			os = self.CanvasX(0) % iv # pixel offset of first mark 
			# loop over each mark.
			for i in xrange(int(self.CanvasWidth / iv + 1)):
				#multiples of iv, cause adding of any error in iv, so keep iv as float
				# use round(), to get to closest pixel, int() to prevent warning
				self.PixMap.draw_lines(self.gc['black'], [(int(round(os + i * iv)), int(round(self.CanvasY(0) - 5))), (int(round(os + i * iv)), int(round(self.CanvasY(0) + 5)))])
			
			# and the y-axis
			iv = self.yScale * self.CanvasHeight/(self.yMax - self.yMin)
			os = self.CanvasY(0) % iv
			for i in xrange(int(self.CanvasHeight / iv + 1)):
				self.PixMap.draw_lines(self.gc['black'], [(int(round(self.CanvasX(0) - 5)), int(round(i * iv + os))), (int(round(self.CanvasX(0) + 5)), int(round(i * iv + os)))])			
		
		else:
			#new style
			factor = 1
			if (self.ScaleStyle == "rad"): factor = pi

			# where to put the numbers
			numbers_x_pos = -10
			numbers_y_pos = 10
			
			# where to center the axis
			center_x_pix = int(round(self.CanvasX(0)))
			center_y_pix = int(round(self.CanvasY(0)))			
			if (center_x_pix < 5): center_x_pix = 5
			if (center_x_pix < 20):numbers_x_pos = 10
			if (center_y_pix < 5): center_y_pix = 5
			if (center_x_pix > self.CanvasWidth - 5): center_x_pix = self.CanvasWidth - 5
			if (center_y_pix > self.CanvasHeight -5): center_y_pix = self.CanvasHeight - 5;
			if (center_y_pix > self.CanvasHeight -20): numbers_y_pos = - 10
			
			# draw cross
			self.PixMap.draw_lines(self.gc['black'], [(center_x_pix,0),(center_x_pix,self.CanvasHeight)])
			self.PixMap.draw_lines(self.gc['black'], [(0,center_y_pix),(self.CanvasWidth,center_y_pix)])			
				
			for i in marks(self.xMin/factor,self.xMax/factor):
				label = '%g' % i
				if (self.ScaleStyle == "rad"): label += "pi"
				i = i * factor

				self.PixMap.draw_lines(self.gc['black'], [(int(round(self.CanvasX(i))), center_y_pix - 5), (int(round(self.CanvasX(i))), center_y_pix + 5)])
				
				self.layout.set_text(label)
				extents = self.layout.get_pixel_extents()[1]
				if (numbers_y_pos < 0): adjust = extents[3]
				else: adjust = 0
				self.PixMap.draw_layout(self.gc['black'],int(round(self.CanvasX(i))), center_y_pix + numbers_y_pos - adjust,self.layout)

			for i in marks(self.yMin,self.yMax):
				label = '%g' % i

				self.PixMap.draw_lines(self.gc['black'], [(center_x_pix - 5, int(round(self.CanvasY(i)))), (center_x_pix + 5, int(round(self.CanvasY(i))))])
				
				self.layout.set_text(label)
				extents = self.layout.get_pixel_extents()[1]
				if (numbers_x_pos < 0): adjust = extents[2]
				else: adjust = 0
				self.PixMap.draw_layout(self.gc['black'],center_x_pix +numbers_x_pos - adjust,int(round(self.CanvasY(i))),self.layout)

			# minor marks
			for i in marks(self.xMin/factor,self.xMax/factor,minor=10):
				i = i * factor
				self.PixMap.draw_lines(self.gc['black'], [(int(round(self.CanvasX(i))), center_y_pix - 2), (int(round(self.CanvasX(i))), center_y_pix +2)])

			for i in marks(self.yMin,self.yMax,minor=10):
				label = '%g' % i
				self.PixMap.draw_lines(self.gc['black'], [(center_x_pix - 2, int(round(self.CanvasY(i)))), (center_x_pix +2, int(round(self.CanvasY(i))))])
				
		plots = []
		# precompile the functions
		try:
			compiled_y1 = compile(y1,"",'eval')
			plots.append((compiled_y1,0,self.gc['blue']))
		except:
			compiled_y1 = None
		try:
			compiled_y2 = compile(y2,"",'eval')
			plots.append((compiled_y2,1,self.gc['red']))
		except:
			compiled_y2 = None
		try:
			compiled_y3 = compile(y3,"",'eval')
			plots.append((compiled_y3,2,self.gc['green']))
		except:
			compiled_y3 = None
		
		self.PrevY = [None, None, None]
		
		if enable_profiling:
			start_graph = time()
		
		if len(plots) != 0:
			for i in xrange(0,self.CanvasWidth,x_res):
				x = self.GraphX(i + 1)
				for e in plots:
					safe_dict['x']=x
					try:
						y = eval(e[0],{"__builtins__":{}},safe_dict)
						yC = int(round(self.CanvasY(y)))
						
						if yC < 0 or yC > self.CanvasHeight:
							raise ValueError
						
						if ConnectPoints and self.PrevY[e[1]] is not None:
							self.PixMap.draw_lines(e[2], [(i, self.PrevY[e[1]]), (i + x_res, yC)])
						else:
							self.PixMap.draw_points(e[2], [(i + x_res, yC)])
						self.PrevY[e[1]] = yC
					except:
						#print "Error at %d: %s" % (x, sys.exc_value)
						self.PrevY[e[1]] = None
					
		if enable_profiling:
			print "time to draw graph:", (time() - start_graph) * 1000, "ms"
					
		self.DrawDrawable()

		
	def CanvasX(self, x):
		"Calculate position on canvas to point on graph"
		return (x - self.xMin) * self.CanvasWidth/(self.xMax - self.xMin)

	def CanvasY(self, y):
		return (self.yMax - y) * self.CanvasHeight/(self.yMax - self.yMin)
		
	def CanvasPoint(self, x, y):
		return (self.CanvasX(x), self.CanvasY(y))
	
	def GraphX(self, x):
		"Calculate position on graph from point on canvas"
		return x  * (self.xMax - self.xMin) / self.CanvasWidth + self.xMin
		
	def GraphY(self, y):
		return self.yMax - (y * (self.yMax - self.yMin) / self.CanvasHeight)
		
		
def MenuToolbarCreate():

	AppWin.MenuMain = gtk.MenuBar()
	
	MenuFile = gtk.Menu()	
	MenuItemFile = gtk.MenuItem("_File")
	MenuItemFile.set_submenu(MenuFile)
	
	Actions.Save = gtk.Action("Save", "_Save", "Save graph as bitmap", gtk.STOCK_SAVE)
	Actions.Save.connect ("activate", Save)
	Actions.add_action(Actions.Save)
	MenuItemSave = Actions.Save.create_menu_item()
	MenuItemSave.add_accelerator("activate", AppWin.AccelGroup, ord("S"), gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)
	MenuFile.append(MenuItemSave)
	
	Actions.Quit = gtk.Action("Quit", "_Quit", "Quit Application", gtk.STOCK_QUIT)
	Actions.Quit.connect ("activate", QuitDlg)
	Actions.add_action(Actions.Quit)
	MenuItemQuit = Actions.Quit.create_menu_item()
	MenuItemQuit.add_accelerator("activate", AppWin.AccelGroup, ord("Q"), gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)
	MenuFile.append(MenuItemQuit)
	
	MenuGraph = gtk.Menu()	
	MenuItemGraph = gtk.MenuItem("_Graph")
	MenuItemGraph.set_submenu(MenuGraph)
	
	Actions.Plot = gtk.Action("Plot", "P_lot", "Plot Functions", gtk.STOCK_REFRESH)
	Actions.Plot.connect ("activate", Plot)
	Actions.add_action(Actions.Plot)
	MenuItemPlot = Actions.Plot.create_menu_item()
	MenuItemPlot.add_accelerator("activate", AppWin.AccelGroup, ord("l"), gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)
	MenuGraph.append(MenuItemPlot)
	
	Actions.Evaluate = gtk.Action("Evaluate", "_Evaluate", "Evaluate Functions", gtk.STOCK_EXECUTE)
	Actions.Evaluate.connect ("activate", Evaluate)
	Actions.add_action(Actions.Evaluate)
	MenuItemEvaluate = Actions.Evaluate.create_menu_item()
	MenuItemEvaluate.add_accelerator("activate", AppWin.AccelGroup, ord("e"), gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)
	MenuGraph.append(MenuItemEvaluate)
	
	Actions.ZoomIn = gtk.Action("ZoomIn", "Zoom _In", "Zoom In", gtk.STOCK_ZOOM_IN)
	Actions.ZoomIn.connect ("activate", ZoomIn)
	Actions.add_action(Actions.ZoomIn)
	MenuItemZoomIn = Actions.ZoomIn.create_menu_item()
	MenuItemZoomIn.add_accelerator("activate", AppWin.AccelGroup, ord("+"), gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)
	MenuGraph.append(MenuItemZoomIn)
	
	Actions.ZoomOut = gtk.Action("ZoomOut", "Zoom _Out", "Zoom Out", gtk.STOCK_ZOOM_OUT)
	Actions.ZoomOut.connect ("activate", ZoomOut)
	Actions.add_action(Actions.ZoomOut)
	MenuItemZoomOut = Actions.ZoomOut.create_menu_item()
	MenuItemZoomOut.add_accelerator("activate", AppWin.AccelGroup, ord("-"), gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)
	MenuGraph.append(MenuItemZoomOut)
	
	Actions.ZoomReset = gtk.Action("ZoomReset", "Zoom _Reset", "Zoom Reset", gtk.STOCK_ZOOM_100)
	Actions.ZoomReset.connect ("activate", ZoomReset)
	Actions.add_action(Actions.ZoomReset)
	MenuItemZoomReset = Actions.ZoomReset.create_menu_item()
	MenuItemZoomReset.add_accelerator("activate", AppWin.AccelGroup, ord("r"), gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)
	MenuGraph.append(MenuItemZoomReset)
	
	MenuItemToggleConnect = gtk.CheckMenuItem("_Connect Points")
	MenuItemToggleConnect.set_active(True)
	MenuItemToggleConnect.connect ("toggled", ToggleConnect)
	MenuGraph.append(MenuItemToggleConnect)
	
	MenuScaleStyle = gtk.Menu()
	MenuItemScaleStyle = gtk.MenuItem("Scale Style")
	MenuItemScaleStyle.set_submenu(MenuScaleStyle)
	MenuGraph.append(MenuItemScaleStyle)
	
	Actions.Dec = gtk.Action("Dec", "Decimal", "Decimal",None)
	Actions.Dec.connect ("activate", ScaleDec)
	Actions.add_action(Actions.Dec)
	MenuItemDec = Actions.Dec.create_menu_item()
	MenuScaleStyle.append(MenuItemDec)
	
	Actions.Rad = gtk.Action("Rad", "Radians", "Radians",None)
	Actions.Rad.connect ("activate", ScaleRad)
	Actions.add_action(Actions.Rad)
	MenuItemRad = Actions.Rad.create_menu_item()
	MenuScaleStyle.append(MenuItemRad)	
	
	Actions.Cust = gtk.Action("Cust", "Custom", "Custom",None)
	Actions.Cust.connect ("activate", ScaleCust)
	Actions.add_action(Actions.Cust)
	MenuItemCust = Actions.Cust.create_menu_item()
	MenuScaleStyle.append(MenuItemCust)
	
	MenuHelp = gtk.Menu()
	MenuItemHelp = gtk.MenuItem("_Help")
	MenuItemHelp.set_submenu(MenuHelp)

	Actions.Help = gtk.Action("Help", "_Contents", "Help Contents", gtk.STOCK_HELP)
	Actions.Help.connect ("activate", ShowYelp)
	Actions.add_action(Actions.Help)
	MenuItemContents = Actions.Help.create_menu_item()
	MenuItemContents.add_accelerator("activate", AppWin.AccelGroup, gtk.gdk.keyval_from_name("F1"), 0, gtk.ACCEL_VISIBLE)
	MenuHelp.append(MenuItemContents)

	Actions.About = gtk.Action("About", "_About", "About Box", gtk.STOCK_ABOUT)
	Actions.About.connect ("activate", ShowAboutDialog)
	Actions.add_action(Actions.About)
	MenuItemAbout = Actions.About.create_menu_item()
	MenuHelp.append(MenuItemAbout)
	
	AppWin.MenuMain.append(MenuItemFile)
	AppWin.MenuMain.append(MenuItemGraph)
	AppWin.MenuMain.append(MenuItemHelp)
	
	AppWin.ToolBar = gtk.Toolbar()
	AppWin.ToolBar.insert(Actions.Plot.create_tool_item(), -1)
	AppWin.ToolBar.insert(Actions.Evaluate.create_tool_item(), -1)
	AppWin.ToolBar.insert(gtk.SeparatorToolItem(), -1)
	AppWin.ToolBar.insert(Actions.ZoomIn.create_tool_item(), -1)
	AppWin.ToolBar.insert(Actions.ZoomOut.create_tool_item(), -1)
	AppWin.ToolBar.insert(Actions.ZoomReset.create_tool_item(), -1)
	AppWin.ToolBar.insert(gtk.SeparatorToolItem(), -1)
	AppWin.ToolBar.insert(Actions.Quit.create_tool_item(), -1)
	

def Plot(Widget, Event=None):
	global xMax, xMin, xScale, yMax, yMin, yScale, y1, y2, y3
	
	xMax = AppWin.xMaxEntry.get_text()
	xMin = AppWin.xMinEntry.get_text()
	xScale = AppWin.xScaleEntry.get_text()

	yMax = AppWin.yMaxEntry.get_text()
	yMin = AppWin.yMinEntry.get_text()
	yScale = AppWin.yScaleEntry.get_text()
	
	Graph.xMax = eval(xMax,{"__builtins__":{}},safe_dict)
	Graph.xMin = eval(xMin,{"__builtins__":{}},safe_dict)
	Graph.xScale = eval(xScale,{"__builtins__":{}},safe_dict)

	Graph.yMax = eval(yMax,{"__builtins__":{}},safe_dict)
	Graph.yMin = eval(yMin,{"__builtins__":{}},safe_dict)
	Graph.yScale = eval(yScale,{"__builtins__":{}},safe_dict)

	y1 = AppWin.Y1Entry.get_text()
	y2 = AppWin.Y2Entry.get_text()
	y3 = AppWin.Y3Entry.get_text()
	
	Graph.Plot()
	

def Evaluate(Widget, Event=None):
	"Evaluate a given x for the three functions"
	
	def EntryChanged(self):
		for e in ((y1, DlgWin.Y1Entry), (y2, DlgWin.Y2Entry), (y3, DlgWin.Y3Entry)):
			try:
				x = float(DlgWin.XEntry.get_text())
				e[1].set_text(str(eval(e[0],{"__builtins__":{}},safe_dict)))
			except:
				if len(e[0]) > 0:
					e[1].set_text("Error: %s" % sys.exc_value)
				else:
					e[1].set_text("")
				
	def Close(self):
		DlgWin.destroy()
		
	DlgWin = gtk.Window(gtk.WINDOW_TOPLEVEL)
	DlgWin.set_title("Evaluate")
	DlgWin.connect("destroy", Close)
	
	DlgWin.XEntry = gtk.Entry()
	DlgWin.XEntry.set_size_request(200, 24)
	DlgWin.XEntry.connect("changed", EntryChanged)
	DlgWin.Y1Entry = gtk.Entry()
	DlgWin.Y1Entry.set_size_request(200, 24)
	DlgWin.Y1Entry.set_sensitive(False)
	DlgWin.Y2Entry = gtk.Entry()
	DlgWin.Y2Entry.set_size_request(200, 24)
	DlgWin.Y2Entry.set_sensitive(False)
	DlgWin.Y3Entry = gtk.Entry()
	DlgWin.Y3Entry.set_size_request(200, 24)
	DlgWin.Y3Entry.set_sensitive(False)
	
	Table = gtk.Table(2, 5)
	l = gtk.Label("x = ")
	l.set_alignment(0, .5)
	Table.attach(l, 0, 1, 0, 1, xpadding=5, ypadding=5, xoptions=gtk.FILL)
	Table.attach(DlgWin.XEntry, 1, 2, 0, 1)
	l = gtk.Label("y1 = ")
	l.set_alignment(0, .5)
	l.modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse("blue"))
	Table.attach(l, 0, 1, 1, 2, xpadding=5, ypadding=5, xoptions=gtk.FILL)
	Table.attach(DlgWin.Y1Entry, 1, 2, 1, 2)
	l = gtk.Label("y2 = ")
	l.set_alignment(0, .5)
	l.modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse("red"))
	Table.attach(l, 0, 1, 2, 3, xpadding=5, ypadding=5, xoptions=gtk.FILL)
	Table.attach(DlgWin.Y2Entry, 1, 2, 2, 3)
	l = gtk.Label("y3 = ")
	l.set_alignment(0, .5)
	l.modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse("DarkGreen"))
	Table.attach(l, 0, 1, 3, 4, xpadding=5, ypadding=5, xoptions=gtk.FILL)
	Table.attach(DlgWin.Y3Entry, 1, 2, 3, 4)
	
	Table.set_border_width(24)	
	DlgWin.add(Table)	
	DlgWin.show_all()


def ZoomIn(Widget, Event=None):
	"Narrow the plotted section by half"
	center_x = (Graph.xMin + Graph.xMax) / 2
	center_y = (Graph.yMin + Graph.yMax) / 2
	range_x = (Graph.xMax - Graph.xMin)
	range_y = (Graph.yMax - Graph.yMin)
	
	Graph.xMin = center_x - (range_x / 4)
	Graph.xMax = center_x + (range_x / 4)
	Graph.yMin = center_y - (range_y / 4)
	Graph.yMax = center_y +(range_y / 4)
	
	ParameterEntriesRepopulate()
	Graph.Plot()


def ZoomOut(Widget, Event=None):
	"Double the plotted section"
	center_x = (Graph.xMin + Graph.xMax) / 2
	center_y = (Graph.yMin + Graph.yMax) / 2
	range_x = (Graph.xMax - Graph.xMin)
	range_y = (Graph.yMax - Graph.yMin)
	
	Graph.xMin = center_x - (range_x)
	Graph.xMax = center_x + (range_x)
	Graph.yMin = center_y - (range_y)
	Graph.yMax = center_y +(range_y)	
	
	ParameterEntriesRepopulate()
	Graph.Plot()


def ZoomReset(Widget, Event=None):
	"Set the range back to the user's input"
   
	Graph.xMin = eval(xMin,{"__builtins__":{}},safe_dict)
	Graph.yMin = eval(yMin,{"__builtins__":{}},safe_dict)
	Graph.xMax = eval(xMax,{"__builtins__":{}},safe_dict)
	Graph.yMax = eval(yMax,{"__builtins__":{}},safe_dict)
	ParameterEntriesPopulate()
	Graph.Plot()

def ScaleDec(Widget, Event=None):
	Graph.ScaleStyle = "dec"
	AppWin.ScaleBox.hide()
	Plot(None)
	
def ScaleRad(Widget, Event=None):
	Graph.ScaleStyle = "rad"
	AppWin.ScaleBox.hide()
	Plot(None)

def ScaleCust(Widget, Event=None):
	Graph.ScaleStyle = "cust"
	AppWin.ScaleBox.show()
	Plot(None)

def ToggleConnect(Widget, Event=None):
	"Toggle between a graph that connects points with lines and one that does not"
	
	global ConnectPoints
	ConnectPoints = not ConnectPoints
	Graph.Plot()
	

def Save(Widget, Event=None):
	"Save graph as .png"

	FileDialog = gtk.FileChooserDialog("Save as..", AppWin, gtk.FILE_CHOOSER_ACTION_SAVE, (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_SAVE, gtk.RESPONSE_OK))
	FileDialog.set_default_response(gtk.RESPONSE_OK)
	Filter = gtk.FileFilter()
	Filter.add_mime_type("image/png")
	Filter.add_pattern("*.png")
	FileDialog.add_filter(Filter)
	FileDialog.set_filename("FunctionGraph.png")
	
	Response = FileDialog.run()
	FileDialog.destroy()
	if Response == gtk.RESPONSE_OK:
		x, y, w, h = Graph.DrawingArea.get_allocation()
		PixBuffer = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, False, 8, w, h)
		PixBuffer.get_from_drawable(Graph.PixMap, Graph.PixMap.get_colormap(), 0, 0, 0, 0, w, h)
		PixBuffer.save(FileDialog.get_filename(), "png")
	

def QuitDlg(Widget, Event=None):
	gtk.main_quit()
	

def ShowYelp(Widget):
	import os
	os.system("yelp lybniz-manual.xml")
		

def ShowAboutDialog(Widget):
	AboutDialog = gtk.AboutDialog()
	AboutDialog.set_name("Lybniz")
	AboutDialog.set_version("1.1")
	#AboutDialog.set_copyright(u"© 2005 by Thomas Führinger")
	AboutDialog.set_authors([u"Thomas Führinger","Sam Tygier"])
	AboutDialog.set_comments("Function Graph Plotter")
	AboutDialog.set_license("Revised BSD")
	#AboutDialog.set_website("http://www.fuhringer.com/thomas/lybniz")
	AboutDialog.show()


def ParameterEntriesCreate():
	# create text entries for parameters	
	Table = gtk.Table(6, 3)
	
	AppWin.Y1Entry = gtk.Entry()
	AppWin.Y1Entry.set_size_request(300, 24)
	AppWin.Y2Entry = gtk.Entry()
	AppWin.Y3Entry = gtk.Entry()
	AppWin.xMinEntry = gtk.Entry()
	AppWin.xMinEntry.set_size_request(90, 24)
	AppWin.xMinEntry.set_alignment(1)
	AppWin.xMaxEntry = gtk.Entry()
	AppWin.xMaxEntry.set_size_request(90, 24)
	AppWin.xMaxEntry.set_alignment(1)
	AppWin.xScaleEntry = gtk.Entry()
	AppWin.xScaleEntry.set_size_request(90, 24)
	AppWin.xScaleEntry.set_alignment(1)
	AppWin.yMinEntry = gtk.Entry()
	AppWin.yMinEntry.set_size_request(90, 24)
	AppWin.yMinEntry.set_alignment(1)
	AppWin.yMaxEntry = gtk.Entry()
	AppWin.yMaxEntry.set_size_request(90, 24)
	AppWin.yMaxEntry.set_alignment(1)
	AppWin.yScaleEntry = gtk.Entry()
	AppWin.yScaleEntry.set_size_request(90, 24)
	AppWin.yScaleEntry.set_alignment(1)
	
	ParameterEntriesPopulate()
	
	AppWin.Y1Entry.connect("key-press-event", key_press_plot)
	AppWin.Y2Entry.connect("key-press-event", key_press_plot)
	AppWin.Y3Entry.connect("key-press-event", key_press_plot)
	AppWin.xMinEntry.connect("key-press-event", key_press_plot)
	AppWin.yMinEntry.connect("key-press-event", key_press_plot)
	AppWin.xMaxEntry.connect("key-press-event", key_press_plot)
	AppWin.yMaxEntry.connect("key-press-event", key_press_plot)
	AppWin.xScaleEntry.connect("key-press-event", key_press_plot)
	AppWin.yScaleEntry.connect("key-press-event", key_press_plot)
	
	AppWin.ScaleBox = gtk.HBox()
	
	l = gtk.Label("y1 = ")
	l.set_alignment(0, .5)
	l.modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse("blue"))
	Table.attach(l, 0, 1, 0, 1, xpadding=5, ypadding=5, xoptions=gtk.FILL)
	Table.attach(AppWin.Y1Entry, 1, 2, 0, 1)
	l = gtk.Label("xMin")
	l.set_alignment(1, .5)
	Table.attach(l, 2, 3, 0, 1, xpadding=5, ypadding=7, xoptions=gtk.FILL)
	Table.attach(AppWin.xMinEntry, 3, 4, 0, 1, xoptions=gtk.FILL)
	l = gtk.Label("yMin")
	l.set_alignment(1, .5)
	Table.attach(l, 4, 5, 0, 1, xpadding=5, ypadding=5, xoptions=gtk.FILL)
	Table.attach(AppWin.yMinEntry, 5, 6, 0, 1, xpadding=5, xoptions=gtk.FILL)
	l = gtk.Label("y2 = ")
	l.set_alignment(0, .5)
	l.modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse("red"))
	Table.attach(l, 0, 1, 1, 2, xpadding=5, ypadding=5, xoptions=gtk.FILL)
	Table.attach(AppWin.Y2Entry, 1, 2, 1, 2)
	l = gtk.Label("xMax")
	l.set_alignment(1, .5)
	Table.attach(l, 2, 3, 1, 2, xpadding=5, ypadding=7, xoptions=gtk.FILL)
	Table.attach(AppWin.xMaxEntry, 3, 4, 1, 2, xoptions=gtk.FILL)
	l = gtk.Label("yMax")
	l.set_alignment(1, .5)
	Table.attach(l, 4, 5, 1, 2, xpadding=5, ypadding=5, xoptions=gtk.FILL)
	Table.attach(AppWin.yMaxEntry, 5, 6, 1, 2, xpadding=5, xoptions=gtk.FILL)
	l = gtk.Label("y3 = ")
	l.set_alignment(0, .5)
	l.modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse("DarkGreen"))
	Table.attach(l, 0, 1, 2, 3, xpadding=5, ypadding=5, xoptions=gtk.FILL)
	Table.attach(AppWin.Y3Entry, 1, 2, 2, 3)
	
	
	l = gtk.Label("xScale")
	l.set_alignment(0, .5)
	AppWin.ScaleBox.add(l)
	#Table.attach(l, 2, 3, 2, 3, xpadding=5, ypadding=7, xoptions=gtk.FILL)
	#Table.attach(AppWin.xScaleEntry, 3, 4, 2, 3, xoptions=gtk.FILL)
	AppWin.ScaleBox.add(AppWin.xScaleEntry)
	l = gtk.Label("yScale")
	l.set_alignment(0, .5)
	AppWin.ScaleBox.add(l)
	#Table.attach(l, 4, 5, 2, 3, xpadding=5, ypadding=5, xoptions=gtk.FILL)
	#Table.attach(AppWin.yScaleEntry, 5, 6, 2, 3, xpadding=5, xoptions=gtk.FILL)
	AppWin.ScaleBox.add(AppWin.yScaleEntry)
	Table.attach(AppWin.ScaleBox, 2, 6, 2, 3, xpadding=5, xoptions=gtk.FILL)
	return Table
	
	
def ParameterEntriesPopulate():
	# set text in entries for parameters with user's input
	
	AppWin.Y1Entry.set_text(y1)
	AppWin.Y2Entry.set_text(y2)
	AppWin.Y3Entry.set_text(y3)
	AppWin.xMinEntry.set_text(xMin)
	AppWin.xMaxEntry.set_text(xMax)
	AppWin.xScaleEntry.set_text(xScale)
	AppWin.yMinEntry.set_text(yMin)
	AppWin.yMaxEntry.set_text(yMax)
	AppWin.yScaleEntry.set_text(yScale)
	
	
def ParameterEntriesRepopulate():
	# set text in entries for parameters
	
	AppWin.Y1Entry.set_text(y1)
	AppWin.Y2Entry.set_text(y2)
	AppWin.Y3Entry.set_text(y3)
	AppWin.xMinEntry.set_text(str(Graph.xMin))
	AppWin.xMaxEntry.set_text(str(Graph.xMax))
	AppWin.xScaleEntry.set_text(str(Graph.xScale))
	AppWin.yMinEntry.set_text(str(Graph.yMin))
	AppWin.yMaxEntry.set_text(str(Graph.yMax))
	AppWin.yScaleEntry.set_text(str(Graph.yScale))
	
def key_press_plot(widget, event):
	if event.keyval == 65293:
		Plot(None)
		return True
	else:
		return False

def Main():
	global AppWin, Graph
	
	AppWin = gtk.Window(gtk.WINDOW_TOPLEVEL)
	AppWin.set_title("Lybniz")
	AppWin.set_default_size(800, 600)
	AppWin.connect("delete-event", QuitDlg)

	AppWin.AccelGroup = gtk.AccelGroup()
	AppWin.add_accel_group(AppWin.AccelGroup)

	AppWin.VBox = gtk.VBox(False, 1)
	AppWin.VBox.set_border_width(1)
	AppWin.add(AppWin.VBox)
	
	AppWin.StatusBar = gtk.Statusbar()
	AppWin.StatusBar.ContextId = AppWin.StatusBar.get_context_id("Dummy")

	MenuToolbarCreate()
	AppWin.VBox.pack_start(AppWin.MenuMain, False, True, 0)
	
	HandleBox = gtk.HandleBox()
	HandleBox.add(AppWin.ToolBar)
	AppWin.VBox.pack_start(HandleBox, False, True, 0)
	
	AppWin.VBox.pack_start(ParameterEntriesCreate(), False, True, 4)
	
	Graph = GraphClass()
	AppWin.VBox.pack_start(Graph.DrawingArea, True, True, 0)
	AppWin.VBox.pack_start(AppWin.StatusBar, False, True, 0)	
		
	AppWin.show_all()
	AppWin.ScaleBox.hide()

	gtk.main()


# Start it all
if __name__ == '__main__': Main()
