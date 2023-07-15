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
                    'zindex': 1, 'border': ['❖', '═', '╗', '║', '╝', '═', '╚', '║'],
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

    @pynvim.function('CodeInsightWinClosed', sync=True) 
    def win_closed(self, win_id) -> None:
        try: del self.windows[win_id[0]]
        except: pass
        # is_CI_float = self.nvim.call('nvim_win_get_var', win_id[0], 'is_CI_float')
        # if is_CI_float: del self.windows[win_id[0]]

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
            self.nvim.call('nvim_win_set_var',win_id,'is_CI_float', True)
            self.windows[win_id] = {'current_def': current_def,
                                    'definitions': definitions}
            self.nvim.out_write(f'Showing [{current_def+1}/{len(definitions)}] definitions\n')

        else: self.nvim.command(f"echo 'No definitions found'")

    @pynvim.command('NextDefinition', nargs='*') # type: ignore
    def next_definition(self, args) -> None:
        win_id =  args[0] if args else self.nvim.call("win_getid")

        try: definitions = self.windows[win_id]['definitions']
        except: self.nvim.command(f"echo 'No definitions found for {win_id}'")
        else:
            if len(definitions) > 1:
                current_def = self.windows[win_id]['current_def']
                next_def = 0 if current_def >= len(definitions)- 1 else current_def + 1
                pos_def = (definitions[next_def]['range']['start']['line'] + 1,
                           definitions[next_def]['range']['start']['character'])
                uri = definitions[next_def]['uri']
                buffer = self.nvim.exec_lua('return vim.uri_to_bufnr(...)', uri)
                self.nvim.call('nvim_win_set_buf', win_id, buffer)
                self.nvim.call('nvim_win_set_cursor', win_id, pos_def)
                self.windows[win_id]['current_def'] = next_def
                self.nvim.out_write(f'Showing [{next_def+1}/{len(definitions)}] definitions\n')

            else: self.nvim.command("echo 'No more definitions found'")

    @pynvim.command('PrevDefinition', nargs='*') # type: ignore
    def previous_definition(self, args) -> None:
        win_id =  args[0] if args else self.nvim.call("win_getid")

        try: definitions = self.windows[win_id]['definitions']
        except: self.nvim.command(f"echo 'No definitions found for {win_id}'")
        else:
            if len(definitions) > 1:
                current_def = self.windows[win_id]['current_def']
                prev_def = len(definitions)- 1 if current_def <= 0 else current_def - 1
                pos_def = (definitions[prev_def]['range']['start']['line'] + 1,
                           definitions[prev_def]['range']['start']['character'])
                uri = definitions[prev_def]['uri']
                buffer = self.nvim.exec_lua('return vim.uri_to_bufnr(...)', uri)
                self.nvim.call('nvim_win_set_buf', win_id, buffer)
                self.nvim.call('nvim_win_set_cursor', win_id, pos_def)
                self.windows[win_id]['current_def'] = prev_def
                self.nvim.out_write(f'Showing [{prev_def+1}/{len(definitions)}] definitions\n')

            else: self.nvim.command("echo 'No more definitions found'")

    def handle_CI_window(self): pass

