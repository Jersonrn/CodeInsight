import pynvim


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
            current_def: int = 0
            pos_def: tuple = (definitions[current_def]['range']['start']['line'] + 1,
                              definitions[current_def]['range']['start']['character'])
            uri = definitions[current_def]['uri']
            buffer = self.nvim.exec_lua('return vim.uri_to_bufnr(...)', uri)
            win_id = self.nvim.call('nvim_open_win', buffer, 1, self.config)
            self.nvim.call('nvim_win_set_cursor', win_id, pos_def)
            self.nvim.call('nvim_win_set_var',0,'is_CI_float', True)
            self.windows[win_id] = {'current_def': current_def,
                                    'definitions': definitions}

        else: self.nvim.command(f"echo 'No definitions found'")

    @pynvim.command('NextDefinition', nargs='*') # type: ignore
    def next_definition(self, args):
        win_id =  args[0] if args else self.nvim.call("win_getid")

        definitions = self.windows[win_id]['definitions']

        try: definitions = self.windows[win_id]['definitions']
        except: self.nvim.command(f"echo 'No definitions found for {win_id}'")
        else:
            if len(definitions) > 1:
                current_def = self.windows[win_id]['current_def']
                next_def = 0 if current_def >= len(definitions) else current_def + 1
                pos_def = (definitions[next_def]['range']['start']['line'] + 1,
                           definitions[next_def]['range']['start']['character'])
                uri = definitions[next_def]['uri']
                buffer = self.nvim.exec_lua('return vim.uri_to_bufnr(...)', uri)
                self.nvim.call('nvim_win_set_buf', win_id, buffer)
                self.nvim.call('nvim_win_set_cursor', win_id, pos_def)

            else: self.nvim.command("echo 'No more definitions found'")


    @pynvim.command('Print', nargs='*') # type: ignore
    def __print(self, args) -> None:
        self.nvim.out_write(f'{args}\n')
