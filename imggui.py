from functools import partial

import wx
from PIL import Image

import shared
from util import load_data, save_data, AddLinearSpacer, SetupChoice
from widgets import LabeledWidget


class ImagePanel(wx.Panel):
    format = None
    savefile = 'imgdata.json'
    data = None
    colormode_dict = {'RGB': 'RGB', 'Palette': 'P',
                      'Grayscale': 'L', 'Bilevel': '1'}
    palette_dict = {'Web': Image.WEB, 'Adaptive': Image.ADAPTIVE}
    dither_dict = {'Floydsteinberg': Image.FLOYDSTEINBERG, 'None': Image.NONE}
    def __init__(self, *args, **kwargs):
        wx.Panel.__init__(self, *args, **kwargs)
        if ImagePanel.data is None:
            ImagePanel.data = load_data(self.savefile)
            shared.format_dict.update(ImagePanel.data)
        self.data = ImagePanel.data.get(self.format, {})

    def OnEvent(self, event, attr, func):
        if not self.format in shared.format_dict:
            shared.format_dict[self.format] = {}
        shared.format_dict[self.format][attr] = func()
        save_data(shared.format_dict, file=self.savefile)

    def OnSlider(self, event, attr, func=None):
        self.OnEvent(event, attr, func or event.GetInt)

    def OnCheckBox(self, event, attr, func=None):
        self.OnEvent(event, attr, func or event.IsChecked)

    def OnChoice(self, event, attr, edict=None, func=None):
        if edict:
            func = lambda: edict[event.GetString()]
        else:
            func = func or event.GetString
        self.OnEvent(event, attr, func)

    def onColour(self, event, attr, func=None):
        self.OnEvent(event, attr,
                     func or (lambda: event.GetColour().Get(False)))
    

class JpegPanel(ImagePanel):
    format = 'JPEG'
    def __init__(self, *args, **kwargs):
        ImagePanel.__init__(self, *args, **kwargs)

        # Set up controls
        labeledQuality = LabeledWidget(parent=self, cls=wx.Slider,
                                       label='Quality',
                                       minValue=1, maxValue=95,
                                       style=wx.SL_HORIZONTAL)
        qualitySlider = labeledQuality.widget
        qualitySlider.SetValue(self.data.get('quality', 75))
        qualityText = wx.StaticText(parent=self)
        def setQualityText():
            quality = qualitySlider.GetValue()
            qualityText.SetLabel(str(quality))
            return quality
        setQualityText()
        qualitySlider.Bind(wx.EVT_SLIDER,
                           partial(self.OnSlider, attr='quality',
                                   func=setQualityText))
        
        optimizeCheckBox = wx.CheckBox(parent=self, label='Optimize')
        optimizeCheckBox.SetValue(self.data.get('optimize', False))
        optimizeCheckBox.Bind(wx.EVT_CHECKBOX,
                              partial(self.OnCheckBox, attr='optimize'))

        progCheckBox = wx.CheckBox(parent=self, label='Progressive')
        progCheckBox.SetValue(self.data.get('progressive', False))
        progCheckBox.Bind(wx.EVT_CHECKBOX,
                          partial(self.OnCheckBox, attr='progressive'))

        labeledBackgroundColor = LabeledWidget(parent=self, label='Background',
                                              cls=wx.ColourPickerCtrl)
        bgColorPicker = labeledBackgroundColor.widget
        bgColorPicker.SetColour(self.data.get('background',
                                                      (255, 255, 255)))
        bgColorPicker.Bind(wx.EVT_COLOURPICKER_CHANGED,
                                   partial(self.onColour, attr='background'))

        labeledColormode = LabeledWidget(parent=self, cls=wx.Choice,
                                         label='Color Mode')
        colormodeChoice = labeledColormode.widget
        SetupChoice(colormodeChoice, ['RGB', 'Grayscale', 'Bilevel'],
                    self.data.get('colormode'), self.colormode_dict) 
        colormodeChoice.Bind(wx.EVT_CHOICE, partial(self.OnChoice,
                                                    attr='colormode',
                             edict=self.colormode_dict))

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        
        self.sizer.AddStretchSpacer(prop=1)
        hSizer = wx.BoxSizer(wx.HORIZONTAL)
        hSizer.AddStretchSpacer(prop=1)
        hSizer.Add(labeledQuality, flag=wx.ALIGN_CENTER)
        hSizer.Add(qualityText, flag=wx.ALIGN_CENTER)
        hSizer.AddStretchSpacer(prop=1)
        self.sizer.Add(hSizer, flag=wx.ALIGN_CENTER)
        AddLinearSpacer(self.sizer, 5)

        hSizer = wx.BoxSizer(wx.HORIZONTAL)
        hSizer.AddStretchSpacer(prop=1)
        hSizer.Add(optimizeCheckBox, flag=wx.ALIGN_CENTER)
        AddLinearSpacer(hSizer, 5)
        hSizer.Add(progCheckBox, flag=wx.ALIGN_CENTER)
        AddLinearSpacer(hSizer, 5)
        hSizer.Add(labeledBackgroundColor, flag=wx.ALIGN_CENTER)
        hSizer.AddStretchSpacer(prop=1)
        self.sizer.Add(hSizer, flag=wx.ALIGN_CENTER)
        AddLinearSpacer(self.sizer, 10)

        self.sizer.Add(labeledColormode, flag=wx.ALIGN_CENTER)

        self.sizer.AddStretchSpacer(prop=1)

        #Layout sizers
        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)


class PngPanel(ImagePanel):
    format = 'PNG'
    def __init__(self, *args, **kwargs):
        ImagePanel.__init__(self, *args, **kwargs)

        # Set up controls
        
        optimizeCheckBox = wx.CheckBox(parent=self, label='Optimize')
        optimizeCheckBox.SetValue(self.data.get('optimize', False))
        optimizeCheckBox.Bind(wx.EVT_CHECKBOX,
                              partial(self.OnCheckBox, attr='optimize'))

        labeledBgColor = LabeledWidget(parent=self, label='Background',
                                              cls=wx.ColourPickerCtrl)
        bgColorText, bgColorPicker = labeledBgColor.GetControls()
        bgColorPicker.SetColour(self.data.get('background',
                                                      (255, 255, 255)))
        bgColorPicker.Bind(wx.EVT_COLOURPICKER_CHANGED,
                                   partial(self.onColour, attr='background'))

        transCheckBox = wx.CheckBox(parent=self, label='Transparency')
        transCheckBox.SetValue(self.data.get('transparent', False))
        def onTrans():
            value = transCheckBox.IsChecked()
            labeledBgColor.Enable(not value)
            return value   
        transCheckBox.Bind(wx.EVT_CHECKBOX, partial(self.OnCheckBox,
                                                    attr='transparent',
                                                    func=onTrans))
        onTrans()

        interlaceCheckBox = wx.CheckBox(parent=self, label='Interlace')
        interlaceCheckBox.SetValue(self.data.get('interlace', False))
        interlaceCheckBox.Bind(wx.EVT_CHECKBOX, partial(self.OnCheckBox,
                                                        attr='interlace'))

        self.labeledColormode = LabeledWidget(parent=self, cls=wx.Choice,
                                              label='Color Mode')
        colormodeChoice = self.labeledColormode.widget
        SetupChoice(colormodeChoice, ['RGB', 'Palette',
                                           'Grayscale', 'Bilevel'],
                    self.data.get('colormode'), self.colormode_dict) 
        colormodeChoice.Bind(wx.EVT_CHOICE, partial(self.OnChoice,
                                                    attr='colormode',
                             func=self.onColormodeChoice))

        self.paletteChoice = wx.Choice(parent=self)
        SetupChoice(self.paletteChoice,
                    ['Web', 'Adaptive'], self.data.get('palette'),
                    self.palette_dict) 
        self.paletteChoice.Bind(wx.EVT_CHOICE,
                                partial(self.OnChoice, attr='palette',
                                        edict=self.palette_dict))
        self.paletteText = wx.StaticText(parent=self, label='Palette')

        self.ditherChoice = wx.Choice(parent=self)
        SetupChoice(self.ditherChoice,
                    ['Floydsteinberg', 'None'],
                    self.data.get('dither'), self.dither_dict) 
        self.ditherChoice.Bind(wx.EVT_CHOICE,
                              partial(self.OnChoice, attr='dither',
                                      edict=self.dither_dict))
        self.ditherText = wx.StaticText(parent=self, label='Dither')

        self.colorsChoice = wx.ComboBox(parent=self, style=wx.TE_PROCESS_ENTER)
        self.colorsChoice.AppendItems(strings=map(str, [2, 4, 8, 16, 32,
                                                        64, 128, 256]))
        self.colorsChoice.SetValue(str(self.data.get('colors', 256)))
        def onColorChoice():
            value = int(self.colorsChoice.GetStringSelection())
            self.GetParent().GetChildren()[0].SetFocus()
            return value
        self.colorsChoice.Bind(wx.EVT_COMBOBOX,
                              partial(self.OnChoice, attr='colors',
                                      func=onColorChoice))
        def onColorEnter():
            try:
                value = int(self.colorsChoice.GetValue())
            except ValueError:
                value = -1
            if value <= 0 or value >= 256:
                try:
                    self.colorsChoice.Undo()
                    value = int(self.colorsChoice.GetValue())
                except:
                    value = 256
            self.GetParent().GetChildren()[0].SetFocus()
            return value
        
        self.colorsChoice.Bind(wx.EVT_TEXT_ENTER,
                              partial(self.OnChoice, attr='colors',
                                      func=onColorEnter))
        
        self.colorsText = wx.StaticText(parent=self, label='Colors')

        bitsChoice = wx.Choice(parent=self)
        SetupChoice(bitsChoice,
                    map(str, [1, 2, 4, 8]),
                    str(self.data.get('bits', 8))) 
        bitsChoice.Bind(wx.EVT_CHOICE,
                        partial(self.OnChoice, attr='bits',
                                func=(lambda: int(bitsChoice.GetStringSelection()))))
        bitsText = wx.StaticText(parent=self, label='Bits')

        self.onColormodeChoice()
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        
        self.sizer.AddStretchSpacer(prop=1)
        hSizer = wx.BoxSizer(wx.HORIZONTAL)
        hSizer.AddStretchSpacer(prop=1)
        hSizer.Add(optimizeCheckBox, flag=wx.ALIGN_CENTER)
        AddLinearSpacer(hSizer, 10)
        hSizer.Add(interlaceCheckBox, flag=wx.ALIGN_CENTER)
        AddLinearSpacer(hSizer, 10)
        hSizer.AddStretchSpacer(prop=1)
        self.sizer.Add(hSizer, flag=wx.ALIGN_CENTER)
        AddLinearSpacer(self.sizer, 5)
        
        hSizer = wx.BoxSizer(wx.HORIZONTAL)
        hSizer.AddStretchSpacer(prop=1)
        hSizer.Add(transCheckBox, flag=wx.ALIGN_CENTER)
        AddLinearSpacer(hSizer, 10)
        hSizer.Add(labeledBgColor, flag=wx.ALIGN_CENTER)
        hSizer.AddStretchSpacer(prop=1)
        self.sizer.Add(hSizer, flag=wx.ALIGN_CENTER)
        AddLinearSpacer(self.sizer, 5)
        
        hSizer = wx.BoxSizer(wx.HORIZONTAL)
        hSizer.AddStretchSpacer(prop=1)
        hSizer.Add(self.labeledColormode, flag=wx.ALIGN_CENTER)
        AddLinearSpacer(hSizer, 15)
        hSizer.Add(self.paletteText, flag=wx.ALIGN_CENTER)
        AddLinearSpacer(hSizer, 5)
        hSizer.Add(self.paletteChoice, flag=wx.ALIGN_CENTER)        
        hSizer.AddStretchSpacer(prop=1)
        self.sizer.Add(hSizer, flag=wx.ALIGN_CENTER)
        AddLinearSpacer(self.sizer, 10)

        hSizer = wx.BoxSizer(wx.HORIZONTAL)
        hSizer.AddStretchSpacer(prop=1)
        hSizer.Add(self.ditherText, flag=wx.ALIGN_CENTER)
        AddLinearSpacer(hSizer, 5)
        hSizer.Add(self.ditherChoice, flag=wx.ALIGN_CENTER)
        AddLinearSpacer(hSizer, 15)
        hSizer.Add(self.colorsText, flag=wx.ALIGN_CENTER)
        AddLinearSpacer(hSizer, 5)
        hSizer.Add(self.colorsChoice, flag=wx.ALIGN_CENTER)
        hSizer.AddStretchSpacer(prop=1)
        self.sizer.Add(hSizer, flag=wx.ALIGN_CENTER)
        AddLinearSpacer(self.sizer, 10)
        
        hSizer = wx.BoxSizer(wx.HORIZONTAL)
        hSizer.AddStretchSpacer(prop=1)
        hSizer.Add(bitsText, flag=wx.ALIGN_CENTER)
        AddLinearSpacer(hSizer, 5)
        hSizer.Add(bitsChoice, flag=wx.ALIGN_CENTER)
        hSizer.AddStretchSpacer(prop=1)
        self.sizer.Add(hSizer, flag=wx.ALIGN_CENTER)

        self.sizer.AddStretchSpacer(prop=1)

        #Layout sizers
        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)

    def onColormodeChoice(self):
        mode = self.colormode_dict[self.labeledColormode.widget.
                                   GetStringSelection()]
        enabled = (mode == 'P')
        text_color = (0, 0, 0) if enabled else (130, 130, 130)

        controls = (self.paletteChoice, self.ditherChoice, self.colorsChoice)
        for control in controls:
            control.Enable(enabled)
        
        texts = (self.paletteText, self.ditherText, self.colorsText)
        for text in texts:
            text.Enable(enabled)
            
        return mode


class GifPanel(ImagePanel):
    format = 'GIF'
    def __init__(self, *args, **kwargs):
        ImagePanel.__init__(self, *args, **kwargs)

        # Set up controls
        
        optimizeCheckBox = wx.CheckBox(parent=self, label='Optimize')
        optimizeCheckBox.SetValue(self.data.get('optimize', False))
        optimizeCheckBox.Bind(wx.EVT_CHECKBOX,
                              partial(self.OnCheckBox, attr='optimize'))

        bgColorPicker = wx.ColourPickerCtrl(parent=self)
        bgColorPicker.SetColour(self.data.get('background',
                                                      (255, 255, 255)))
        bgColorPicker.Bind(wx.EVT_COLOURPICKER_CHANGED,
                                   partial(self.onColour, attr='background'))
        bgColorText = wx.StaticText(parent=self, label='Background')

        transCheckBox = wx.CheckBox(parent=self, label='Transparency')
        transCheckBox.SetValue(self.data.get('transparent', False))
        def onTrans():
            value = transCheckBox.IsChecked()
            bgColorText.Enable(not value)
            bgColorPicker.Enable(not value)
            return value   
        transCheckBox.Bind(wx.EVT_CHECKBOX,
                              partial(self.OnCheckBox, attr='transparent',
                                      func=onTrans))
        onTrans()

        interlaceCheckBox = wx.CheckBox(parent=self, label='Interlace')
        interlaceCheckBox.SetValue(self.data.get('interlace', False))
        interlaceCheckBox.Bind(wx.EVT_CHECKBOX,
                              partial(self.OnCheckBox, attr='interlace'))

        self.colormodeChoice = wx.Choice(parent=self)
        SetupChoice(self.colormodeChoice,
                    ['RGB', 'Palette', 'Grayscale', 'Bilevel'],
                    self.data.get('colormode'), self.colormode_dict)
        self.colormodeChoice.Bind(wx.EVT_CHOICE,
                              partial(self.OnChoice, attr='colormode',
                                      func=self.onColormodeChoice))
        colormodeText = wx.StaticText(parent=self, label='Color Mode')

        self.paletteChoice = wx.Choice(parent=self)
        SetupChoice(self.paletteChoice,
                    ['Web', 'Adaptive'], self.data.get('palette'),
                    self.palette_dict) 
        self.paletteChoice.Bind(wx.EVT_CHOICE,
                                partial(self.OnChoice, attr='palette',
                                        edict=self.palette_dict))
        self.paletteText = wx.StaticText(parent=self, label='Palette')

        self.ditherChoice = wx.Choice(parent=self)
        SetupChoice(self.ditherChoice,
                    ['Floydsteinberg', 'None'],
                    self.data.get('dither'), self.dither_dict) 
        self.ditherChoice.Bind(wx.EVT_CHOICE,
                              partial(self.OnChoice, attr='dither',
                                      edict=self.dither_dict))
        self.ditherText = wx.StaticText(parent=self, label='Dither')

        self.colorsChoice = wx.ComboBox(parent=self, style=wx.TE_PROCESS_ENTER)
        self.colorsChoice.AppendItems(strings=map(str, [2, 4, 8, 16, 32,
                                                        64, 128, 256]))
        self.colorsChoice.SetValue(str(self.data.get('colors', 256)))
        def onColorChoice():
            value = int(self.colorsChoice.GetStringSelection())
            self.GetParent().GetChildren()[0].SetFocus()
            return value
        self.colorsChoice.Bind(wx.EVT_COMBOBOX,
                              partial(self.OnChoice, attr='colors',
                                      func=onColorChoice))
        def onColorEnter():
            try:
                value = int(self.colorsChoice.GetValue())
            except ValueError:
                value = -1
            if value <= 0 or value >= 256:
                try:
                    self.colorsChoice.Undo()
                    value = int(self.colorsChoice.GetValue())
                except:
                    value = 256
            self.GetParent().GetChildren()[0].SetFocus()
            return value
        
        self.colorsChoice.Bind(wx.EVT_TEXT_ENTER,
                              partial(self.OnChoice, attr='colors',
                                      func=onColorEnter))
        
        self.colorsText = wx.StaticText(parent=self, label='Colors')

        self.onColormodeChoice()
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        
        self.sizer.AddStretchSpacer(prop=1)
        hSizer = wx.BoxSizer(wx.HORIZONTAL)
        hSizer.AddStretchSpacer(prop=1)
        hSizer.Add(optimizeCheckBox, flag=wx.ALIGN_CENTER)
        AddLinearSpacer(hSizer, 10)
        hSizer.Add(interlaceCheckBox, flag=wx.ALIGN_CENTER)
        AddLinearSpacer(hSizer, 10)
        hSizer.AddStretchSpacer(prop=1)
        self.sizer.Add(hSizer, flag=wx.ALIGN_CENTER)
        AddLinearSpacer(self.sizer, 5)
        
        hSizer = wx.BoxSizer(wx.HORIZONTAL)
        hSizer.AddStretchSpacer(prop=1)
        hSizer.Add(transCheckBox, flag=wx.ALIGN_CENTER)
        AddLinearSpacer(hSizer, 10)
        hSizer.Add(bgColorText, flag=wx.ALIGN_CENTER)
        AddLinearSpacer(hSizer, 5)
        hSizer.Add(bgColorPicker, flag=wx.ALIGN_CENTER)
        hSizer.AddStretchSpacer(prop=1)
        self.sizer.Add(hSizer, flag=wx.ALIGN_CENTER)
        AddLinearSpacer(self.sizer, 5)
        
        hSizer = wx.BoxSizer(wx.HORIZONTAL)
        hSizer.AddStretchSpacer(prop=1)
        hSizer.Add(colormodeText, flag=wx.ALIGN_CENTER)
        AddLinearSpacer(hSizer, 5)
        hSizer.Add(self.colormodeChoice, flag=wx.ALIGN_CENTER)
        AddLinearSpacer(hSizer, 15)
        hSizer.Add(self.paletteText, flag=wx.ALIGN_CENTER)
        AddLinearSpacer(hSizer, 5)
        hSizer.Add(self.paletteChoice, flag=wx.ALIGN_CENTER)        
        hSizer.AddStretchSpacer(prop=1)
        self.sizer.Add(hSizer, flag=wx.ALIGN_CENTER)
        AddLinearSpacer(self.sizer, 10)

        hSizer = wx.BoxSizer(wx.HORIZONTAL)
        hSizer.AddStretchSpacer(prop=1)
        hSizer.Add(self.ditherText, flag=wx.ALIGN_CENTER)
        AddLinearSpacer(hSizer, 5)
        hSizer.Add(self.ditherChoice, flag=wx.ALIGN_CENTER)
        AddLinearSpacer(hSizer, 15)
        hSizer.Add(self.colorsText, flag=wx.ALIGN_CENTER)
        AddLinearSpacer(hSizer, 5)
        hSizer.Add(self.colorsChoice, flag=wx.ALIGN_CENTER)
        hSizer.AddStretchSpacer(prop=1)
        self.sizer.Add(hSizer, flag=wx.ALIGN_CENTER)

        self.sizer.AddStretchSpacer(prop=1)

        #Layout sizers
        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)

    def onColormodeChoice(self):
        mode = self.colormode_dict[self.colormodeChoice.GetStringSelection()]
        enabled = (mode == 'P')
        text_color = (0, 0, 0) if enabled else (130, 130, 130)

        controls = (self.paletteChoice, self.ditherChoice, self.colorsChoice)
        for control in controls:
            control.Enable(enabled)
        
        texts = (self.paletteText, self.ditherText, self.colorsText)
        for text in texts:
            text.Enable(enabled)

        return mode


class SmartPanel(ImagePanel):
    about = 'Converts grayscale images to PNG and color images to JPEG.'
    def __init__(self, *args, **kwargs):
        ImagePanel.__init__(self, *args, **kwargs)
        aboutText = wx.StaticText(parent=self, label=self.about)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(aboutText, flag=wx.ALIGN_CENTER)

        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        

gui_dict = {'JPEG': JpegPanel, 'PNG': PngPanel, 'GIF': GifPanel,
            'Smart': SmartPanel}
