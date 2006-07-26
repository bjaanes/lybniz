# -*- coding: UTF-8 -*-
""" Workbench module - handle screen separation
	Thomas Führinger, 2005-10-26
"""


import gtk
	
class Workbench:

	def __init__(self, FirstWindowName, Widget=None):
		
		if Widget is None:
			Widget = gtk.Label(FirstWindowName)
			
		self.Window = {}
		self.Window[FirstWindowName] = WorkbenchWindow(self, FirstWindowName)
		self.GtkWidget = gtk.HPaned()	# dummy to keep WorkbenchWindow.Insert() happy
		self.Window[FirstWindowName].ParentContainer = self.GtkWidget
		self.Window[FirstWindowName].Place = 1
		
		self.GtkWidget.pack1(Widget, True, True)
		self.Window[FirstWindowName].GtkWidget = Widget		
		
	def WindowInsert(self, Window, SplitLine, Place, Name=None, NewWidget=None):
		"SplitLine: 1 = vertical, 2 = horizontal"
		
		# assign default window names "W1", "W2" ...
		if Name is None:
			Name = "W" + str(len(self.Window) + 1)
			
		self.Window[Name] = WorkbenchWindow(self, Name, NewWidget)
		self.Window[Window].Insert(SplitLine, Place, self.Window[Name])
		
		
class WorkbenchWindow:

	def __init__(self, Workbench, Name, Widget=None):
	
		def PopulateMenu(Textview, Menu):
			s = gtk.SeparatorMenuItem()
			s.show()
			Menu.append(s)
			Menu.append(self.PopupMenuItemCreate())
		
		self.Workbench = Workbench		# Workbench I am contained in
		self.Name = Name	
		self.ParentContainer = None		# parent GtkPaned, holds my own GtkWidget
		self.Place = None				# my place in the parent GtkPaned
		
		if Widget is None:
			self.GtkWidget = gtk.Label(Name)
			self.GtkWidget.set_selectable(True)
			self.GtkWidget.connect ("populate-popup", PopulateMenu)			
		else:
			self.GtkWidget = Widget
		
	def Insert(self, SplitLine, PlaceNew, NewWindow):
		
		# create new GtkPaned dependent on split line
		if SplitLine == 1:
			Paned = gtk.VPaned()
		else:
			Paned = gtk.HPaned()
			
		# unhook own widget
		self.ParentContainer.remove(self.GtkWidget)
			
		# pack new GtkPaned in previous place of own widget
		if self.Place == 1:
			self.ParentContainer.pack1(Paned, True, False)
		else:
			self.ParentContainer.pack2(Paned, True, False)
	
		# pack own widget and new window's into new GtkPaned
		if PlaceNew == 1:
			NewWindow.Place = 1
			self.Place = 2
			Paned.pack1(NewWindow.GtkWidget)
			Paned.pack2(self.GtkWidget)
		else:
			self.Place = 1
			NewWindow.Place = 2
			Paned.pack1(self.GtkWidget)
			Paned.pack2(NewWindow.GtkWidget)
			
		self.ParentContainer = Paned
		NewWindow.ParentContainer = Paned
		self.ParentContainer.show_all()
		
	def Connect(self, Widget):
		# replace my current Widget
		
		self.ParentContainer.remove(self.GtkWidget)
		
		# pack new Widget in previous place of own widget
		if self.Place == 1:
			self.ParentContainer.pack1(Widget)
		else:
			self.ParentContainer.pack2(Widget)
		
		self.GtkWidget = Widget
		
	def PopupMenuItemCreate(self):
		# create submenu item to use as popup
		
		WindowMenuItem = gtk.MenuItem("Window")
		WindowMenuItem.set_submenu(self.PopupMenuCreate())
		WindowMenuItem.show()
		return WindowMenuItem
		
	def PopupMenuCreate(self):
		# create submenu to use as popup
		
		def InsertRight(Action=None):	
			self.Workbench.WindowInsert(self.Name, 2, 2)
		def InsertBottom(Action=None):	
			self.Workbench.WindowInsert(self.Name, 1, 2)
		def InsertLeft(Action=None):	
			self.Workbench.WindowInsert(self.Name, 2, 1)
		def InsertTop(Action=None):	
			self.Workbench.WindowInsert(self.Name, 1, 1)
			
		def ShowName(Action=None):
			"Display dialog box with window's name"
						
			def Close(self):
				DlgWin.destroy()
				
			DlgWin = gtk.Window(gtk.WINDOW_TOPLEVEL)
			DlgWin.set_title("Window Name")
			DlgWin.connect("destroy", Close)
			l = gtk.Label(self.Name)
			l.set_padding(39, 30)	
			DlgWin.add(l)	
			DlgWin.show_all()
		
		WindowMenu = gtk.Menu()
		
		ActionInsertRight = gtk.Action("InsertRight", "Insert Right", "Insert new window on right side", gtk.STOCK_GO_FORWARD)
		ActionInsertRight.connect ("activate", InsertRight)
		MenuItemInsertRight = ActionInsertRight.create_menu_item()
		ActionInsertBottom = gtk.Action("InsertBottom", "Insert Bottom", "Insert new window on bottom", gtk.STOCK_GO_DOWN)
		ActionInsertBottom.connect ("activate", InsertBottom)
		MenuItemInsertBottom = ActionInsertBottom.create_menu_item()
		ActionInsertLeft = gtk.Action("InsertLeft", "Insert Left", "Insert new window on left side", gtk.STOCK_GO_BACK)
		ActionInsertLeft.connect ("activate", InsertLeft)
		MenuItemInsertLeft = ActionInsertLeft.create_menu_item()
		ActionInsertTop = gtk.Action("InsertTop", "Insert Top", "Insert new window on top", gtk.STOCK_GO_UP)
		ActionInsertTop.connect ("activate", InsertTop)
		MenuItemInsertTop = ActionInsertTop.create_menu_item()
		
		ActionShowName = gtk.Action("ShowName", "Show Name", "Show window's name", None)
		ActionShowName.connect ("activate", ShowName)
		MenuItemShowName = ActionShowName.create_menu_item()
		
		WindowMenu.append(MenuItemInsertRight)
		WindowMenu.append(MenuItemInsertBottom)
		WindowMenu.append(MenuItemInsertLeft)
		WindowMenu.append(MenuItemInsertTop)
		s = gtk.SeparatorMenuItem()
		s.show()
		WindowMenu.append(s)
		WindowMenu.append(MenuItemShowName)
		WindowMenu.show()
		return WindowMenu

			
