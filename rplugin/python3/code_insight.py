import pynvim
import pynvim.api

default_config = {'focusable': True,
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
class CodeInsight(object):
    def __init__(self, nvim) -> None:
        self.nvim = nvim
        self.config: dict
        self.windows: dict = {}

    @pynvim.autocmd('VimEnter', sync=True)
    def vim_enter(self) -> None:
        try: config = self.nvim.eval('g:code_insight_config')
        except: config = default_config
        self.config = config if type(config['focusable']) == bool else fix_config(config)

    @pynvim.command('ShowFloatDefinition') # type: ignore
    def show_float_definition(self) -> None:
        definitions = self.nvim.call('coc#rpc#request', 'definitions', [])
        if definitions:
            current_def = 0
            uri = definitions[current_def]['uri']
            buffer = self.nvim.exec_lua('return vim.uri_to_bufnr(...)', uri)
            win_id = self.nvim.call('nvim_open_win', buffer, 1, self.config)

            self.windows[win_id] = {'current_def': current_def, 'definitions': definitions}
            # win_info = self.nvim.call('getwininfo')
            self.nvim.command(f'echo "{self.windows}"')
            # self.nvim.api.win_close(W,True)


    @pynvim.command('Print', nargs='*') # type: ignore
    def __print(self, args) -> None:
        self.nvim.out_write(f'{args}\n')
