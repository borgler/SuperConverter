from __future__ import division

import sys
import os
import re
import traceback
import tempfile
from shutil import rmtree, make_archive
from io import BytesIO
from StringIO import StringIO
from itertools import izip_longest
from multiprocessing import Pool

from PIL import Image, ImageChops
import PIL.PngImagePlugin
import PIL.GifImagePlugin
import PIL.JpegImagePlugin
import PIL.BmpImagePlugin
import PIL.TiffImagePlugin
Image._initialized=2

import png
from psd_tools import PSDImage

import shared


def is_grayscale(im):
    gray_im = im.convert('L')
    if 'RGB' in im.mode:
        gray_im = gray_im.convert(im.mode)
    diff = ImageChops.difference(gray_im, im)
    
    for color in diff.getdata():
        if color != 0 and color[: 3] != (0, 0, 0):
            return False
    return True


def prepare_dir(dest_dir, clear_dest=False):
    if clear_dest:
        try:
            for path in os.listdir(dest_dir):
                ext = os.path.splitext(path)[1].lower()
                path = os.path.join(dest_dir, path)
                try:
                    if os.path.isfile(path) and ext in shared.filetypes:
                        os.remove(path)
                except OSError:
                    pass
        except OSError:
            pass

    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)


def convert_image(src_dir, dest_dir, format, filename, format_dict):
    try:
        name, ext = os.path.splitext(filename)
        ext = ext.lower()
        
        filepath = os.path.join(src_dir, filename)
        if ext == '.psd':
            psd = PSDImage.load(filepath)
            im = psd.as_PIL()
        else:
            im = Image.open(filepath)
        orig_im = im

        if format == 'Smart':
            if is_grayscale(im):
                format = 'PNG'
            else:
                format = 'JPEG'

        options = format_dict.get(format, {}).copy()
        
        bands = list(im.getbands())
        colormode = options.get('colormode')
        if options.get('transparent')  and colormode in ('RGB', 'L'):
            colormode += 'A'
        elif not options.get('transparent') and 'A' in bands:
            back_color = tuple(options.get('background',
                                           (255, 255, 255)))
            back_im = Image.new('RGBA', im.size, back_color)
            alpha = im.split()[bands.index('A')]
            new_im = Image.composite(im, back_im, alpha)
            im = new_im.convert('RGB')
            
        if colormode is not None and im.mode != colormode:
            im.draft(colormode, im.size)
            if (im.mode == 'RGBA' and colormode == 'P' and
                options.get('transparent')):
                if format != 'PNG':
                    im = RGBA_to_P(im, options)
                else:
                    im = im.convert('RGB')
                    im = im.convert('P', palette=Image.ADAPTIVE,
                                    colors=options.get('colors', 256))
            elif colormode == 'P':
                convert_options = {
                    'dither': options.get('dither',
                                          Image.FLOYDSTEINBERG),
                    'palette': options.get('palette', Image.WEB),
                    'colors': options.get('colors', 256),
                    }
                im = im.convert(colormode, **convert_options)
                for key in convert_options:
                    try:
                        del options[key]
                    except KeyError:
                        pass
            else:
                im = im.convert(colormode)
        if format:  
            #im.info = {}
            dest_path = os.path.join(dest_dir, name)
            
            new_ext = shared.extension_dict.get(format,
                                                '.' + format.lower())
            dest_path += new_ext
            if (options.get('interlace') or options.get('bits', 8) != 8
                or options.get('optimize')):
                save_as_PNG(im, orig_im, dest_path, options)
            else:
                im.save(dest_path, format, **options)
    except BaseException as e:
        return filename, e
    return filename, None
            

def convert_folder(src_dir, dest_dir, format='JPEG', archive=False,
                   clear_dest=False, callback=True, **kwargs):
    old_stdout = sys.stdout
    err_log = StringIO()
    sys.stdout = err_log
    
    prepare_dir(dest_dir, clear_dest)
    if archive:
        old_dest = dest_dir
        dest_dir = tempfile.mkdtemp()

    pool = Pool()

    image_files = []
    for filename in os.listdir(src_dir):
        name, ext = os.path.splitext(filename)
        ext = ext.lower()
        
        if ext in shared.filetypes:
            image_files.append(filename)

    global image_count, image_num
    image_num = len(image_files)
    image_count = 0

    def convert_callback(results):
        filename, exception = results
        global image_count, image_num
        if exception:
            print('Failed to process ' + filename)
            print(''.join(traceback.format_exception_only(type(exception),
                                                          exception)))
            image_num -= 1
        else:
            image_count += 1
        if image_count >= image_num:
            old_stdout.write(err_log.getvalue())
            sys.stdout = old_stdout
            
        callback(filename, exception)
        
    for filename in image_files:
        try:
            result = pool.apply_async(convert_image, (src_dir, dest_dir,
                                                      format, filename,
                                                      shared.format_dict),
                                      callback=convert_callback)
            
        except:
            print('failed to process %s%s' % (name, ext))
            print(''.join(traceback.format_exception(*sys.exc_info())))
            pass
 
    if archive:
        archive_name = os.path.join(old_dest, os.path.basename(src_dir))
        make_archive(archive_name, 'zip', dest_dir)
        rmtree(dest_dir)


class PilImageToPyPngAdapter:
    # taken from GitHub
    def __init__(self, im):
        self.im = im
        self.iml = im.load()

    def __len__(self):
        return self.im.size[1]

    def __getitem__(self, row):
        out = []
        for col in range(self.im.size[0]):
            px = self.iml[col, row]
            if hasattr(px, '__iter__'):
                #Multi-channel image
                out.extend(px)
            else:
                #Single channel image
                out.append(px)
        return out


def to_greyscale(r, g, b):
    return int(r * 299/1000 + g * 587/1000 + b * 114/1000)


def grouper(iterable, n, fillvalue=None):
    "Collect data into fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx
    args = [iter(iterable)] * n
    return izip_longest(fillvalue=fillvalue, *args)


def save_as_PNG(im, orig_im, filename, options):
    colormode = options.get('colormode')
    transparent = options.get('transparent')
    greyscale = ('L' in im.mode or '1' in im.mode)
    bitdepth = options.get('bits', 8)
    background = None if transparent else options.get('background')
    if greyscale and background:
        background = to_greyscale(*background)
    palette = im.getpalette()
    
    if palette:
        palette = grouper(palette, 3)

    writer_args = {
        'size': im.size,
        'greyscale': greyscale,
        'alpha': 'A' in im.mode,
        'bitdepth': bitdepth,
        'palette':  palette,
        'transparent': None,
        'background':  background,
        'compression': 9 if options.get('optimize') else -1,
        'interlace': options.get('interlace'),
    }
    if not palette and bitdepth != 8:
        im = Image.eval(im, lambda x: (x * (2 ** bitdepth)) / 256)
    png_writer = png.Writer(**writer_args)

    with open(filename, 'wb') as outfile:
        png_writer.write(outfile, PilImageToPyPngAdapter(im))


def RGBA_to_P(im, options):
    alpha = im.split()[3]
    colors = options.get('colors', 256)
    hicolor = colors - 1
    
    # Convert the image into P mode but only use
    # n - 1 colors in the palette out of n
    im = im.convert('RGB').convert('P', palette=Image.ADAPTIVE, colors=hicolor)

    # Set all pixel values below 128 to 256,
    # and the rest to 0
    mask = Image.eval(alpha, lambda a: 255 if a < 128 else 0)

    # Paste the color of index (n - 1) and use alpha as a mask
    im.paste(hicolor, mask)
    # The transparency index is (n - 1)
    options['transparency'] = hicolor
    return im
