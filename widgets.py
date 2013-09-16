#!/usr/bin/env python2
import wx

from util import AddLinearSpacer

class LabeledWidget(wx.Panel):
    def __init__(self, parent, cls, label, space=5, *args, **kwargs):
        wx.Panel.__init__(self, parent)
        
        self.widget = cls(parent=self, *args, **kwargs)
        self.label = wx.StaticText(parent=self, label=label)

        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.Add(self.label, flag=wx.CENTER)
        AddLinearSpacer(self.sizer, space)
        self.sizer.Add(self.widget, flag=wx.CENTER)

        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)

    def GetControls(self):
        return self.label, self.widget

    def SetLabel(self, value):
        self.label.SetLabel(value)

    def Enable(self, value=True):
        self.label.Enable(value)
        self.widget.Enable(value)

    def Disable(self):
        self.Enable(False)


class MainWindow(wx.Frame):
    def __init__(self, *args, **kwargs):
        wx.Frame.__init__(self, *args, **kwargs)
        lw = LabeledWidget(self, wx.Choice, 'Choose', choices=['1', '2', '3'], space=5)
        lw.widget.SetSelection(1)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddStretchSpacer(prop=1)
        sizer.Add(lw, flag=wx.CENTER)
        sizer.AddStretchSpacer(prop=1)
        self.SetSizer(sizer)
        self.Show()
        
        
if __name__ == "__main__":
    app = wx.App()
    frame = MainWindow(parent=None, title='SuperConverter')
    app.MainLoop()
