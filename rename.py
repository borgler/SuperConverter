from __future__ import division

import re
import os.path

builtins = {'str': str, 'int': int, 'slice': slice, 'float': float}
image_num = 0

def sortkey(s):
    parts = re.findall(r'(\d+|[^\d]+)', os.path.splitext(s)[0])
    for n, part in enumerate(parts):
        if part.isdigit():
            parts[n] = int(part)
    return parts


def replace(globals_dict, matchobj, base=10):
    globals_dict['__builtins__'] = builtins
    
    form = matchobj.group(1).lower()
    if ';' in form:
        width, form = form.split(';', 1)
    else:
        width = 'pad'
        
    if width == 'pad':
        width = len(str(image_num))
    elif width != 'nopad':
        try:
            width = int(width)
        except ValueError:
            width = 0
        
    value = eval(form, globals_dict)
    if isinstance(value, int) or isinstance(value, float):
        if width == 'nopad':
            value = '%d' % value
        else:
            value = '%0*d' % (width, value)
    return value
