import json

import wx

def AddLinearSpacer(boxsizer, pixelSpacing):
    """ A one-dimensional spacer along only
        the major axis for any BoxSizer """
    
    orientation = boxsizer.GetOrientation()
    if (orientation == wx.HORIZONTAL):
        boxsizer.Add((pixelSpacing, 0))

    elif (orientation == wx.VERTICAL):
        boxsizer.Add((0, pixelSpacing))

def SetupChoice(choice, options, value, rename_dict=None):
    if rename_dict:
        rename_dict = dict(reversed(i) for i in rename_dict.items())
        value = rename_dict.get(value)
    choice.AppendItems(strings=options)
    try:
        index = options.index(value)
    except (ValueError, KeyError):
        index = 0
    choice.SetSelection(n=index)


def save_data(data, file='data.json'):
    try:
        with open(file, 'wt') as jsonfile:
            json.dump(data, jsonfile)
    except IOError:
        pass

def load_data(file='data.json'):
    try:
        with open(file, 'rt') as jsonfile:
            return json.load(jsonfile)
    except (IOError, ValueError):
        return {}
