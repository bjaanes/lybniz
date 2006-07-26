#!/usr/bin/env python
# -*- coding: UTF-8 -*-

""" 
	Simple Function Graph Plotter
	© Thomas Führinger, 2005-02-12
	www.fuhringer.com/thomas
		
	Version 0.1.0
	Requires PyGtk 2.6	
	Released under the terms of the revised BSD license
	Modified: 2005-11-01
"""

import sys, gtk, math, Workbench, Graph
	
AppWin = None
Actions = gtk.ActionGroup("General")
Script = \
"""def y1():
    return 1 / x**2

def y2():
    return math.cos(x)

Graph1.y = [y1, y2]

Graph1.xMin = -6
Graph1.xMax = 6
Graph1.xScale = .5
Graph1.yMin = -2
Graph1.yMax = 6
Graph1.yScale = 1

Graph1.Refresh()
"""
x = None
Workbench1 = None
		

def ShowAboutDialog(Widget):
	AboutDialog = gtk.AboutDialog()
	AboutDialog.set_name("Lybniz Workbench")
	AboutDialog.set_version("0.1.0")
	AboutDialog.set_authors([u"Thomas Führinger"])
	AboutDialog.set_comments("Function Graph Plotter")
	AboutDialog.set_license("Revised BSD")
	AboutDialog.show()


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
	#MenuFile.append(MenuItemSave)
	
	Actions.Quit = gtk.Action("Quit", "_Quit", "Quit Application", gtk.STOCK_QUIT)
	Actions.Quit.connect ("activate", QuitDlg)
	Actions.add_action(Actions.Quit)
	MenuItemQuit = Actions.Quit.create_menu_item()
	MenuItemQuit.add_accelerator("activate", AppWin.AccelGroup, ord("Q"), gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)
	MenuFile.append(MenuItemQuit)
	
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
	AppWin.MenuMain.append(MenuItemHelp)
	
	AppWin.ToolBar = gtk.Toolbar()
	AppWin.ToolBar.insert(Actions.Quit.create_tool_item(), -1)
	

def Save(Widget, Event=None):
	"yet to be implemented"

	pass
	

def QuitDlg(Widget, Event=None):
	gtk.main_quit()
	

def ShowYelp(Widget):
	import os
	os.system("yelp lybniz-wb-manual.xml")


class Editor:

	def __init__(self):
		
		self.WorkbenchWindow = None
		self.Output = None
		self.GtkWidget = gtk.VBox()
	
		self.ToolBar = gtk.Toolbar()
		self.ActionExecute = gtk.Action("Execute", "_Execute", "Execute Script", gtk.STOCK_EXECUTE)
		self.ActionExecute.connect ("activate", self.Execute)
		self.ToolBar.insert(self.ActionExecute.create_tool_item(), -1)
		
		self.ActionSave = gtk.Action("Save", "_Save", "Save script", gtk.STOCK_SAVE)
		self.ActionSave.connect ("activate", self.Save)
		
		self.HandleBox = gtk.HandleBox()
		self.HandleBox.add(self.ToolBar)
		self.GtkWidget.pack_start(self.HandleBox, False, False, 0)
		
		self.GtkTextView = gtk.TextView()
		#self.GtkTextView.set_wrap_mode(gtk.WRAP_WORD)
		self.GtkTextView.set_size_request(220, 200)
		self.GtkTextBuffer = self.GtkTextView.get_buffer()
		self.GtkTextBuffer.set_text(Script)
		Tag = gtk.TextTag(type)
		Tag.set_property("family", "monospace")
		#Tag.set_property("tabs", 4)
		TTable = self.GtkTextBuffer.get_tag_table()
		TTable.add(Tag)
		self.GtkTextBuffer.apply_tag(Tag, self.GtkTextBuffer.get_start_iter(), self.GtkTextBuffer.get_end_iter())
		
		self.GtkScrolledWindow = gtk.ScrolledWindow()
		self.GtkScrolledWindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		self.GtkScrolledWindow.add(self.GtkTextView)
		self.GtkWidget.pack_start(self.GtkScrolledWindow)
		
	def Execute(self, Action=None):
	
		b = self.GtkTextBuffer.get_selection_bounds()
		if b != ():
			Script = self.GtkTextBuffer.get_text(b[0], b[1])
		else:
			Script = self.GtkTextBuffer.get_text(self.GtkTextBuffer.get_start_iter(), self.GtkTextBuffer.get_end_iter())
			
		SaveOut = sys.stdout
		SaveErr = sys.stderr
		try:
			if self.Output is not None:
				sys.stdout = self.Output
				sys.stderr = self.Output
			exec Script in globals(), locals()
		finally: 
			sys.stdout = SaveOut
			sys.stderr = SaveErr
                
		
	def ConnectWindow(self, WorkbenchWindow):
		"make widget appear in WorkbenchWindow and add popup window"
		
		self.WorkbenchWindow = WorkbenchWindow
		self.WorkbenchWindow.Connect(self.GtkWidget)
		self.GtkTextView.connect ("populate-popup", self.PopulateMenu)
		
	def OutputTo(self, Output):
		"redirect output"
		
		self.Output = Output
		
	def PopulateMenu(self, Textview, Menu):
		"append the submenu for inserting addtional windows into popup menu"
		
		s = gtk.SeparatorMenuItem()
		s.show()
		Menu.append(s)
		MenuItemSave = self.ActionSave.create_menu_item()
		Menu.append(MenuItemSave)
		Menu.append(self.WorkbenchWindow.PopupMenuItemCreate())

	def Save(self, Widget, Event=None):
		"Save script"
			
		FileDialog = gtk.FileChooserDialog("Save as..", None, gtk.FILE_CHOOSER_ACTION_SAVE, (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_SAVE, gtk.RESPONSE_OK))
		FileDialog.set_default_response(gtk.RESPONSE_OK)
		Filter = gtk.FileFilter()
		Filter.add_mime_type("text/txt")
		Filter.add_pattern("*.py")
		FileDialog.add_filter(Filter)
		FileDialog.set_filename("Script1.py")
		
		Response = FileDialog.run()
		FileDialog.destroy()
		if Response == gtk.RESPONSE_OK:
			File = open(FileDialog.get_filename(), "w")
			File.write(self.GtkTextBuffer.get_text(self.GtkTextBuffer.get_start_iter(), self.GtkTextBuffer.get_end_iter()))
			File.close()


class Output:
	"Output window"

	def __init__(self):
		
		self.WorkbenchWindow = None
	
		self.GtkTextView = gtk.TextView()
		self.GtkTextView.set_wrap_mode(gtk.WRAP_WORD)
		self.GtkTextView.set_size_request(220, 100)
		self.GtkTextBuffer = self.GtkTextView.get_buffer()
		Tag = gtk.TextTag(type)
		Tag.set_property("family", "monospace")
		TTable = self.GtkTextBuffer.get_tag_table()
		TTable.add(Tag)
		self.GtkTextBuffer.apply_tag(Tag, self.GtkTextBuffer.get_start_iter(), self.GtkTextBuffer.get_end_iter())
		
		GtkScrolledWindow = gtk.ScrolledWindow()
		GtkScrolledWindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		GtkScrolledWindow.add(self.GtkTextView)
		self.GtkWidget = GtkScrolledWindow
		
	def write(self, String):
		"implement write method of file class for redirection of output"
		
		self.GtkTextBuffer.insert(self.GtkTextBuffer.get_end_iter(), String)
		
	def ConnectWindow(self, WorkbenchWindow):
		"make widget appear in WorkbenchWindow and add popup window"
		
		self.WorkbenchWindow = WorkbenchWindow
		self.WorkbenchWindow.Connect(self.GtkWidget)
		self.GtkTextView.connect ("populate-popup", self.PopulateMenu)
		
	def PopulateMenu(self, Textview, Menu):
		"append the submenu for inserting addtional windows into popup menu"
		
		s = gtk.SeparatorMenuItem()
		s.show()
		Menu.append(s)
		Menu.append(self.WorkbenchWindow.PopupMenuItemCreate())


def Main():

	global AppWin, Graph1, Workbench1
	
	AppWin = gtk.Window(gtk.WINDOW_TOPLEVEL)
	AppWin.set_title("Lybniz Workbench")
	AppWin.set_default_size(800, 600)
	AppWin.connect("delete-event", QuitDlg)

	AppWin.AccelGroup = gtk.AccelGroup()
	AppWin.add_accel_group(AppWin.AccelGroup)

	AppWin.VBox = gtk.VBox(False, 1)
	AppWin.VBox.set_border_width(1)
	AppWin.add(AppWin.VBox)
	MenuToolbarCreate()
	AppWin.VBox.pack_start(AppWin.MenuMain, False, True, 0)
		
	# create workbench with windows "Editor1", "Output1" and "Graph1"
	Workbench1 = Workbench.Workbench("Editor1")
	Workbench1.WindowInsert("Editor1", 2, 2, "Graph1")
	Workbench1.WindowInsert("Editor1", 1, 2, "Output1")
	
	Editor1 = Editor()
	Editor1.ConnectWindow(Workbench1.Window["Editor1"])
	
	Output1 = Output()
	Output1.ConnectWindow(Workbench1.Window["Output1"])
	Editor1.OutputTo(Output1)

	Graph1 = Graph.Graph2D()
	Graph1.ConnectWindow(Workbench1.Window["Graph1"])	

	AppWin.VBox.pack_start(Workbench1.GtkWidget, True, True, 0)	
	AppWin.show_all()
	gtk.main()


# Start it all
if __name__ == '__main__': Main()
