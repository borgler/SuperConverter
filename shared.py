formats = ['JPEG', 'PNG', 'GIF']
filetypes = ['.png', '.jpg', '.jpeg', '.psd', '.bmp', '.tiff']

extension_dict = {'JPEG': '.jpg'}

format_dict = {'JPEG': {'optimize': True, 'quality': 95},
              'PNG':  {'optimize': True},
              }

options = {'format': 'JPEG', 'archive': False, 'src_dir': '', 'dest_dir': '',
           'extensions': True}
