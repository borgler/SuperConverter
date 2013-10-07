#!/usr/bin/env python2
from __future__ import division

import os
import sys
import traceback
import shutil
import json
from functools import partial
from multiprocessing import freeze_support

import wx
from wx.lib.intctrl import IntCtrl
from PIL import Image

import images
import shared
import imggui
from util import load_data, save_data, AddLinearSpacer, SetupChoice
from widgets import LabeledWidget


class FilePanel(wx.Panel):
    def __init__(self, parent):       
        wx.Panel.__init__(self, parent)
        self.SetBackgroundColour((255, 255, 255))
        self.Refresh()

        # Set up buttons
        srcButton = wx.Button(parent=self, label='&Source Folder')
        srcButton.Bind(wx.EVT_BUTTON, partial(self.OnFolder, mode='src_dir'))
        srcText = wx.StaticText(parent=self, label=(
                                         shared.options.get('src_dir', '')))
        
        destButton = wx.Button(parent=self, label='&Destination Folder')
        destButton.Bind(wx.EVT_BUTTON, partial(self.OnFolder, mode='dest_dir'))
        destText = wx.StaticText(parent=self, label=(
                                         shared.options.get('dest_dir', '')))

        self.textDict = {'src_dir': srcText, 'dest_dir': destText}
        
        convButton = wx.Button(parent=self, label='&Convert')
        convButton.Bind(wx.EVT_BUTTON, self.OnConvert)
        self.convert_callback = self.GetTopLevelParent().OnConversion
                
        clearCheckBox = wx.CheckBox(parent=self,
                                    label='Clear Destination Folder')
        clearCheckBox.Bind(wx.EVT_CHECKBOX,
                           partial(self.OnCheckBox, attr='clear_dest'))
        clearCheckBox.SetValue(shared.options.get('clear_dest', False))

        zipCheckBox = wx.CheckBox(parent=self, label='Create Zip Archive')
        zipCheckBox.Bind(wx.EVT_CHECKBOX,
                         partial(self.OnCheckBox, attr='archive'))
        zipCheckBox.SetValue(shared.options.get('archive', False))

        # Sizer stuff
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.AddStretchSpacer(prop=1)
        
        hSizer = wx.BoxSizer(wx.HORIZONTAL)
        hSizer.AddStretchSpacer(prop=1)
        hSizer.Add(srcButton, flag=wx.CENTER)
        AddLinearSpacer(hSizer, 5)
        hSizer.Add(srcText, flag=wx.CENTER)
        hSizer.AddStretchSpacer(prop=1)
        self.sizer.Add(hSizer, flag=wx.CENTER)

        AddLinearSpacer(self.sizer, 15)

        hSizer = wx.BoxSizer(wx.HORIZONTAL)
        hSizer.AddStretchSpacer(prop=1)
        hSizer.Add(destButton, flag=wx.CENTER)
        AddLinearSpacer(hSizer, 5)
        hSizer.Add(destText, flag=wx.CENTER)
        hSizer.AddStretchSpacer(prop=1)
        self.sizer.Add(hSizer, flag=wx.CENTER)
        
        AddLinearSpacer(self.sizer, 15)
        self.sizer.Add(convButton, flag=wx.CENTER)
        AddLinearSpacer(self.sizer, 15)
        
        hSizer = wx.BoxSizer(wx.HORIZONTAL)
        hSizer.AddStretchSpacer(prop=1)
        hSizer.Add(clearCheckBox, flag=wx.CENTER)
        AddLinearSpacer(hSizer, 15)
        hSizer.Add(zipCheckBox, flag=wx.CENTER)
        hSizer.AddStretchSpacer(prop=1)
        self.sizer.Add(hSizer, flag=wx.CENTER)
        
        self.sizer.AddStretchSpacer(prop=1)

        #Layout sizers
        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)

    def OnFolder(self, event, mode):
        ''' Open a file'''
        dlg = wx.DirDialog(self, 'Choose a folder', '', wx.DD_DEFAULT_STYLE)
        path = shared.options.get(mode)
        dlg.SetPath(path if (path is not None) else '')
        
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            shared.options[mode] = path
            self.textDict[mode].SetLabel(path)
            self.Layout()
            save_data(shared.options)
        dlg.Destroy()

    def OnConvert(self, event):
        images.convert_folder(callback=self.convert_callback, **shared.options)

    def OnCheckBox(self, event, attr):
        shared.options[attr] = event.IsChecked()
        save_data(shared.options)


class FormatPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        
        labeledChoice = LabeledWidget(parent=self, cls=wx.Choice,
                                      label='Conversion: ', space=0)
        formatChoice = labeledChoice.widget
        choices = (shared.formats + ['Smart'])
        SetupChoice(formatChoice, choices, shared.options.get('format', 'JPEG'))
        formatChoice.Bind(wx.EVT_CHOICE, self.OnFormatChoice)

        # Sizer stuff
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        
        AddLinearSpacer(self.sizer, 10)
        self.sizer.Add(labeledChoice, flag=wx.CENTER)

        #Layout sizers
        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)

        
        self.img_gui_dict = {}
        for img_format, gui_class in imggui.gui_dict.items():
            img_panel = self.img_gui_dict[img_format] = gui_class(parent=self)
            self.sizer.Add(img_panel, flag=wx.EXPAND|wx.ALL, border=10)
            img_panel.Hide()
        img_format = shared.options.get('format', shared.formats[0])
        self.img_panel = self.img_gui_dict.get(img_format)
        if self.img_panel:
            self.img_panel.Show()
            self.sizer.Layout()

    def OnFormatChoice(self, event):
        img_format = event.GetString()
        shared.options['format'] = img_format
        save_data(shared.options)

        if self.img_panel:
            self.img_panel.Hide()
        self.img_panel = self.img_gui_dict.get(img_format)
        if self.img_panel:
            self.img_panel.Show()
            self.sizer.Layout()
            self.Refresh()


class ModifyPanel(wx.Panel):
    filter_dict = {'Nearest': Image.NEAREST, 'Bilinear': Image.BILINEAR,
                   'Bicubic': Image.BICUBIC, 'Antialias': Image.ANTIALIAS}
    def __init__(self, parent):       
        wx.Panel.__init__(self, parent)
        self.SetBackgroundColour((255, 255, 255))
        self.Refresh()

        renameCheckBox = wx.CheckBox(parent=self,
                                     label='Rename Converted Images')
        renameCheckBox.SetValue(shared.options.get('rename', False))

        extCheckBox = wx.CheckBox(parent=self,
                                     label='Automatically Add File Extensions')
        extCheckBox.Bind(wx.EVT_CHECKBOX,
                         partial(self.OnCheckBox, attr='extensions',
                                 ctrl=extCheckBox))
        extCheckBox.SetValue(shared.options.get('extensions', True))
        
        labeledRename = LabeledWidget(parent=self, cls=wx.TextCtrl,
                                      label='Rename Pattern',
                                      style=wx.TE_PROCESS_ENTER)
        renameCtrl = labeledRename.widget
        renameCtrl.SetValue(shared.options.get('renameText', ''))
        OnRenameText = partial(self.OnTextCtrl, attr='renameText',
                               ctrl=renameCtrl)
        renameCtrl.Bind(wx.EVT_TEXT_ENTER, OnRenameText)
        renameCtrl.Bind(wx.EVT_KILL_FOCUS, OnRenameText)

        # Rename help
        rename_help = ('''<NAME> = original name, 
<EXT> = original file extension, 
<N+1> = for numbering starting from 1,
or <N+4> or <(N+3)*6> and so on.
Put a number, PAD, or NOPAD, followed by a ";",
before numbering to adjust numerical padding (like <3;N+1>)''')
        def onHelp(event):
            renameCtrl.SetToolTipString(rename_help)
        wx.ToolTip.SetDelay(15)
        renameCtrl.Bind(wx.wx.EVT_MOTION, onHelp)

        # Last, so the other controls will enable/disable with the checkbox
        onRename = partial(self.OnCheckBox, attr='rename', ctrl=renameCheckBox,
                           related=[extCheckBox, labeledRename])
        renameCheckBox.Bind(wx.EVT_CHECKBOX, onRename)
        onRename(None)


        resizeCheckBox = wx.CheckBox(parent=self,
                                     label='Resize Converted Images')
        resizeCheckBox.SetValue(shared.options.get('resize', False))

        aspectCheckBox = wx.CheckBox(parent=self,
                                     label='Maintain Aspect Ratio')
        aspectCheckBox.SetValue(shared.options.get('maintainRatio', False))
        onAspect = partial(self.OnCheckBox, attr='maintainRatio',
                           ctrl=aspectCheckBox)
        aspectCheckBox.Bind(wx.EVT_CHECKBOX, onAspect)
        
        
        labeledWidth = LabeledWidget(parent=self, cls=IntCtrl,
                                     label='Width',
                                     style=wx.TE_PROCESS_ENTER,
                                     value=shared.options.get('resizeWidth',
                                                              1000),
                                     limited=True,
                                     min=0)
        widthCtrl = labeledWidth.widget
        OnWidth = partial(self.OnTextCtrl, attr='resizeWidth', ctrl=widthCtrl)
        widthCtrl.Bind(wx.EVT_TEXT_ENTER, OnWidth)
        widthCtrl.Bind(wx.EVT_KILL_FOCUS, OnWidth)
        
        labeledHeight = LabeledWidget(parent=self, cls=IntCtrl,
                                     label='Height',
                                     style=wx.TE_PROCESS_ENTER,
                                     value=shared.options.get('resizeHeight',
                                                              1000),
                                     limited=True,
                                     min=0)
        heightCtrl = labeledHeight.widget
        OnHeight = partial(self.OnTextCtrl, attr='resizeHeight',
                           ctrl=heightCtrl)
        heightCtrl.Bind(wx.EVT_TEXT_ENTER, OnHeight)
        heightCtrl.Bind(wx.EVT_KILL_FOCUS, OnHeight)

        labeledFilter = LabeledWidget(parent=self, cls=wx.Choice,
                                         label='Resize Filter')
        filterChoice = labeledFilter.widget
        SetupChoice(filterChoice,
                    ['Nearest', 'Bilinear', 'Bicubic', 'Antialias'],
                    shared.options.setdefault('resizeFilter', Image.ANTIALIAS),
                    self.filter_dict)
        filterChoice.Bind(wx.EVT_CHOICE, partial(self.OnChoice,
                                                 attr='resizeFilter',
                                                 edict=self.filter_dict))


        # Last, so the other controls will enable/disable with the checkbox
        onResize = partial(self.OnCheckBox, attr='resize', ctrl=resizeCheckBox,
                           related=[labeledWidth, aspectCheckBox,
                                    labeledHeight, labeledFilter])
        resizeCheckBox.Bind(wx.EVT_CHECKBOX, onResize)
        onResize(None)
        

        # Sizer stuff
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.AddStretchSpacer(prop=1)

        hSizer = wx.BoxSizer(wx.HORIZONTAL)
        hSizer.AddStretchSpacer(prop=1)
        hSizer.Add(renameCheckBox, flag=wx.CENTER)
        AddLinearSpacer(hSizer, 10)
        hSizer.Add(extCheckBox, flag=wx.CENTER)
        hSizer.AddStretchSpacer(prop=1)
        self.sizer.Add(hSizer, flag=wx.CENTER)

        AddLinearSpacer(self.sizer, 10)
        self.sizer.Add(labeledRename, flag=wx.CENTER)
        
        AddLinearSpacer(self.sizer, 20)

        hSizer = wx.BoxSizer(wx.HORIZONTAL)
        hSizer.AddStretchSpacer(prop=1)
        hSizer.Add(resizeCheckBox, flag=wx.CENTER)
        AddLinearSpacer(hSizer, 10)
        hSizer.Add(aspectCheckBox, flag=wx.CENTER)
        hSizer.AddStretchSpacer(prop=1)
        self.sizer.Add(hSizer, flag=wx.CENTER)

        hSizer = wx.BoxSizer(wx.HORIZONTAL)
        hSizer.AddStretchSpacer(prop=1)
        hSizer.Add(labeledWidth, flag=wx.CENTER)
        AddLinearSpacer(hSizer, 10)
        hSizer.Add(labeledHeight, flag=wx.CENTER)
        hSizer.AddStretchSpacer(prop=1)
        self.sizer.Add(hSizer, flag=wx.CENTER)
        
        hSizer = wx.BoxSizer(wx.HORIZONTAL)
        hSizer.AddStretchSpacer(prop=1)
        hSizer.Add(labeledWidth, flag=wx.CENTER)
        AddLinearSpacer(hSizer, 10)
        hSizer.Add(labeledHeight, flag=wx.CENTER)
        hSizer.AddStretchSpacer(prop=1)
        self.sizer.Add(hSizer, flag=wx.CENTER)
        
        AddLinearSpacer(self.sizer, 10)
        self.sizer.Add(labeledFilter, flag=wx.CENTER)

        self.sizer.AddStretchSpacer(prop=1)

        #Layout sizers
        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)

    def OnTextCtrl(self, e, attr, ctrl):
        self.GetParent().SetFocus()
        shared.options[attr] = ctrl.GetValue()
        save_data(shared.options)

    def OnCheckBox(self, event, attr, ctrl, related=[]):
        checked = ctrl.IsChecked()
        shared.options[attr] = checked
        for item in related:
            item.Enable(checked)
        save_data(shared.options)

    def OnChoice(self, event, attr, edict=None):
        shared.options[attr] = edict[event.GetString()]
        save_data(shared.options)
        
        
class FocusMixIn(wx.Window):
    def prepareFrame(self, closeEventHandler=None):
        self._closeHandler = closeEventHandler
        EVT_CLOSE(self, self.closeFrame)

    def closeFrame(self, event):
        win = wxWindow_FindFocus()
        if win != None:
            win.Disconnect(-1, -1, wxEVT_KILL_FOCUS)
        if self._closeHandler != None:
            self._closeHandler(event)
        else:
            event.Skip()


class MainWindow(wx.Frame, FocusMixIn):
    def __init__(self, *args, **kwargs):
        wx.Frame.__init__(self, *args, **kwargs)
        shared.options.update(load_data())

        #menu setup
        self.CreateStatusBar() # A Statusbar in the bottom of the window

        # Setting up the menu.
        filemenu = wx.Menu()
        menuAbout = filemenu.Append(wx.ID_ABOUT, '&About',' Information about this program')
        menuExit = filemenu.Append(wx.ID_EXIT,'E&xit',' Terminate the program')

        # Creating the menubar.
        menuBar = wx.MenuBar()
        menuBar.Append(filemenu,'&File') # Adding the 'filemenu' to the MenuBar
        self.SetMenuBar(menuBar)  # Adding the MenuBar to the Frame content.

        # Events.
        self.Bind(wx.EVT_MENU, self.OnExit, menuExit)
        self.Bind(wx.EVT_MENU, self.OnAbout, menuAbout)

        # Here we create a panel and a notebook on the panel
        panel = wx.Panel(self)
        notebook = wx.Notebook(panel)

        # create the page windows as children of the notebook
        filepage = FilePanel(notebook)
        formatpage = FormatPanel(notebook)
        modifypage = ModifyPanel(notebook)

        # add the pages to the notebook with the label to show on the tab
        notebook.AddPage(filepage, 'Convert')
        notebook.AddPage(formatpage, 'Format')
        notebook.AddPage(modifypage, 'Modify')

        # finally, put the notebook in a sizer for the panel to manage
        # the layout
        sizer = wx.BoxSizer()
        sizer.Add(notebook, 1, wx.EXPAND)
        panel.SetSizer(sizer)
        self.SetSize(self.GetSize() + (0, 35)) # Expand to fit the PngPanel
        self.Show()
                            
    def OnAbout(self, event):
        # Create a message dialog box
        dlg = wx.MessageDialog(self, 'SuperConverter is licensed under the MPL',
                               'SuperConverter',
                               wx.OK)
        dlg.ShowModal() # Shows it
        dlg.Destroy() # finally destroy it when finished.

    def OnExit(self, event):
        self.Close(True)  # Close the frame.

    def OnConversion(self, imagename, exception):
        if exception:
            self.SetStatusText('Failed to process ' + imagename)
        else:
            self.SetStatusText('Processed ' + imagename)


if __name__ == "__main__":
    freeze_support()
    app = wx.App()
    frame = MainWindow(parent=None, title='SuperConverter')
    app.MainLoop()
