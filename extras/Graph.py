# -*- coding: UTF-8 -*-
""" Graph module - plot function graphs
	Thomas Führinger, 2005-10-28
"""

import gtk, sys, __main__
	
class Graph2D:
	def __init__(self):	

		# Create backing pixmap of the appropriate size
		def ConfigureEvent(Widget, Event):
			x, y, w, h = Widget.get_allocation()
			self.PixMap = gtk.gdk.Pixmap(Widget.window, w, h)
			self.CanvasWidth = w
			self.CanvasHeight = h
			self.Refresh()
			return True

		# Redraw the screen from the backing pixmap
		def ExposeEvent(Widget, Event):
			x, y, w, h = Event.area
			Widget.window.draw_drawable(Widget.get_style().fg_gc[gtk.STATE_NORMAL], self.PixMap, x, y, x, y, w, h)
			return False

		def ButtonPressEvent(Widget, Event):
			global xSel, ySel
			
			# Start marking selection
			if Event.button == 1:
				self.Selection[0][0], self.Selection[0][1] = int(Event.x), int(Event.y)
				self.Selection[1][0], self.Selection[1][1] = None, None
			
			# Show popup menu allowing to split window
			if Event.button == 3 and self.WorkbenchWindow is not None:
				m = self.WorkbenchWindow.PopupMenuCreate()
				MenuItemSave = self.ActionSave.create_menu_item()
				m.append(MenuItemSave)
				m.popup(None, None, None, 3, Event.time)

		# End of selection
		def ButtonReleaseEvent(Widget, Event):
			
			if Event.button == 1 and Event.x != self.Selection[0][0] and Event.y != self.Selection[0][1]:
				xmi, ymi = min(self.GraphX(self.Selection[0][0]), self.GraphX(Event.x)), min(self.GraphY(self.Selection[0][1]), self.GraphY(Event.y))
				xma, yma = max(self.GraphX(self.Selection[0][0]), self.GraphX(Event.x)), max(self.GraphY(self.Selection[0][1]), self.GraphY(Event.y))
				self.xMin, self.yMin, self.xMax, self.yMax = xmi, ymi, xma, yma
				self.GtkSpinButton.set_value(1)
				self.Refresh()
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
				
		self.xMax = 10.0
		self.xMin = -10.0
		self.xScale = 1
		self.yMax = 10.0
		self.yMin = -10.0
		self.yScale = 1
		
		self.y = []
		
		self.Zoom = 1
		self.ConnectPoints = True
		
		self.GtkWidget = gtk.VBox()
		self.WorkbenchWindow = None
	
		self.ToolBar = gtk.Toolbar()	
		ti = gtk.ToolItem()
		ti.add(gtk.Label(" Zoom Factor  "))		
		self.ToolBar.insert(ti, -1)
		
		self.GtkSpinButton = gtk.SpinButton(None, 1, 1)
		self.GtkSpinButton.set_numeric(True)
		self.GtkSpinButton.set_range(0.1, 100.0)
		self.GtkSpinButton.set_increments(.2, .2)
		self.GtkSpinButton.set_value(1)		
		ti = gtk.ToolItem()
		ti.add(self.GtkSpinButton)		
		self.ToolBar.insert(ti, -1)
		
		self.ActionRefresh = gtk.Action("Refresh", "_Refresh", "Refresh graphs", gtk.STOCK_REFRESH)
		self.ActionRefresh.connect ("activate", self.Refresh)
		self.ToolBar.insert(self.ActionRefresh.create_tool_item(), -1)
		self.HandleBox = gtk.HandleBox()
		self.HandleBox.add(self.ToolBar)
		self.GtkWidget.pack_start(self.HandleBox, False, False, 0)
		
		self.ActionSave = gtk.Action("Save", "_Save", "Save graph", gtk.STOCK_SAVE)
		self.ActionSave.connect ("activate", self.Save)
				
		# Marked area point[0, 1][x, y]
		self.Selection = [[None, None], [None, None]]
		
		self.DrawingArea = gtk.DrawingArea()
		self.DrawingArea.set_size_request(60, 60)
		self.DrawingArea.connect("expose_event", ExposeEvent)
		self.DrawingArea.connect("configure_event", ConfigureEvent)
		self.DrawingArea.connect("button_press_event", ButtonPressEvent)
		self.DrawingArea.connect("button_release_event", ButtonReleaseEvent)
		self.DrawingArea.connect("motion_notify_event", MotionNotifyEvent)
		self.DrawingArea.set_events(gtk.gdk.EXPOSURE_MASK | gtk.gdk.LEAVE_NOTIFY_MASK | gtk.gdk.BUTTON_PRESS_MASK | gtk.gdk.BUTTON_RELEASE_MASK | gtk.gdk.POINTER_MOTION_MASK |gtk.gdk.POINTER_MOTION_HINT_MASK)
		
		self.GtkWidget.pack_start(self.DrawingArea, True, True, 0)
			
	def DrawDrawable(self):
		x, y, w, h = self.DrawingArea.get_allocation()
		self.DrawingArea.window.draw_drawable(self.DrawingArea.get_style().fg_gc[gtk.STATE_NORMAL], self.PixMap, 0, 0, 0, 0, w, h)
		
	def Refresh(self, Widget=None, Event=None):
		
		self.GtkSpinButton.update()
		self.Zoom = self.GtkSpinButton.get_value()
		self.PixMap.draw_rectangle(self.DrawingArea.get_style().white_gc, True, 0, 0, self.CanvasWidth, self.CanvasHeight)
		
		# draw cross
		self.PixMap.draw_lines(self.DrawingArea.get_style().black_gc, [self.CanvasPoint(0, self.yMin * self.Zoom), self.CanvasPoint(0, self.yMax / self.Zoom)])
		self.PixMap.draw_lines(self.DrawingArea.get_style().black_gc, [self.CanvasPoint(self.xMin * self.Zoom, 0), self.CanvasPoint(self.xMax / self.Zoom, 0)])
		
		# draw scaling x
		iv = int(self.xScale * self.CanvasWidth/(self.xMax - self.xMin) * self.Zoom)
		os = self.CanvasX(0) % iv
		for i in xrange(self.CanvasWidth / iv + 1):
			self.PixMap.draw_lines(self.DrawingArea.get_style().black_gc, [(os + i * iv, self.CanvasY(0) - 5), (os + i * iv, self.CanvasY(0) + 5)])
		# draw scaling x
		iv = int(self.yScale * self.CanvasHeight/(self.yMax - self.yMin) * self.Zoom)
		os = self.CanvasY(0) % iv
		for i in xrange(self.CanvasHeight / iv + 1):
			self.PixMap.draw_lines(self.DrawingArea.get_style().black_gc, [(self.CanvasX(0) - 5, i * iv + os), (self.CanvasX(0) + 5, i * iv + os)])

		# plot
		GC1 = self.DrawingArea.get_style().fg_gc[gtk.STATE_NORMAL]
		GC1.foreground = gtk.gdk.color_parse("blue")
		
		PrevY = []
		for i in  xrange(len(self.y)): PrevY.append(None)
		for i in xrange(self.CanvasWidth):
			__main__.x = self.GraphX(i + 1)
			for ii in xrange(len(self.y)):
				try:
					y = self.y[ii]()
					yC = self.CanvasY(y)
					
					if yC < 0 or yC > self.CanvasHeight:
						raise ValueError
					
					if self.ConnectPoints and PrevY[ii] is not None:
						self.PixMap.draw_lines(GC1, [(i, PrevY[ii]), (i + 1, yC)])
					else:
						self.PixMap.draw_points(GC1, [(i + 1, yC)])
					PrevY[ii] = yC
				except:
					#print "Error at %d: %s" % (__main__.x, sys.exc_value)
					PrevY[ii] = None
		self.DrawDrawable()

		
	def CanvasX(self, x):
		"Calculate position on canvas to point on graph"
		return int((x - self.xMin / self.Zoom) * self.CanvasWidth/(self.xMax - self.xMin) * self.Zoom)

	def CanvasY(self, y):
		return int((self.yMax / self.Zoom - y) * self.CanvasHeight/(self.yMax - self.yMin) * self.Zoom)
		
	def CanvasPoint(self, x, y):
		return (self.CanvasX(x), self.CanvasY(y))
	
	def GraphX(self, x):
		"Calculate position on graph from point on canvas"
		return x  * (self.xMax - self.xMin) / self.Zoom / self.CanvasWidth + self.xMin / self.Zoom
		
	def GraphY(self, y):
		return self.yMax / self.Zoom - (y * (self.yMax * self.Zoom - self.yMin / self.Zoom) / self.CanvasHeight)
		
	def ConnectWindow(self, WorkbenchWindow):
		"make widget appear in WorkbenchWindow"
		
		self.WorkbenchWindow = WorkbenchWindow
		self.WorkbenchWindow.Connect(self.GtkWidget)
		self.GtkWidget.show_all()

	def Save(self, Widget, Event=None):
		"Save graph as .png"

		FileDialog = gtk.FileChooserDialog("Save as..", None, gtk.FILE_CHOOSER_ACTION_SAVE, (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_SAVE, gtk.RESPONSE_OK))
		FileDialog.set_default_response(gtk.RESPONSE_OK)
		Filter = gtk.FileFilter()
		Filter.add_mime_type("image/png")
		Filter.add_pattern("*.png")
		FileDialog.add_filter(Filter)
		FileDialog.set_filename("FunctionGraph.png")
		
		Response = FileDialog.run()
		FileDialog.destroy()
		if Response == gtk.RESPONSE_OK:
			x, y, w, h = self.DrawingArea.get_allocation()
			PixBuffer = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, False, 8, w, h)
			PixBuffer.get_from_drawable(self.PixMap, self.PixMap.get_colormap(), 0, 0, 0, 0, w, h)
			PixBuffer.save(FileDialog.get_filename(), "png")
	
