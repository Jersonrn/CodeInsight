import pynvim
import pynvim.api

default_settings = {'focusable': True,
                    'external': False,
                    'width': 70,
                    'height': 20,
                    'win': 1000,
                    'bufpos': [10, 10],
                    'anchor': 'NW',
                    'row': 1.0,
                    'col': 0.0,
                    'zindex': 1,
                    'border': ['❖', '═', '╗', '║', '╝', '═', '╚', '║'],
                    'title': [["", 'FloatTitle']],
                    'title_pos': 'left',
                    'relative': 'win'}

def fix_config(config: dict) -> dict:
    for key in config.keys():
        if config[key] == 1: config[key] = True
        elif config[key] == 0: config[key] = False
    return config


@pynvim.plugin
class Plugin(object):
    def __init__(self, nvim) -> None:
        self.nvim = nvim

    @pynvim.autocmd('VimEnter', sync=True)
    def vim_enter(self) -> None:
        try: config = self.nvim.eval('g:code_insight_config')
        except: config = default_settings
        self.config = config if type(config['focusable']) == bool else fix_config(config)

    @pynvim.command('ShowConfig', nargs='*') # type: ignore
    def show_config(self, args) -> None:
        self.nvim.command(f'echo "{self.config}"')
