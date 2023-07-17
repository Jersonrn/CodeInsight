import sys
import pynvim


default_config = {  'focusable': True,
                    'external': False,
                    'width': 100,
                    'height': 20,
                    # 'win': 1000,
                    'bufpos': [10, 10],
                    'anchor': 'SE',
                    'row': 1.0,
                    'col': 0.0,
                    'zindex': 1,
                    'border': ['❖', '═', '╗', '║', '⇲', '═', '╚', '║'],
                    'title': [["CodeInsight", 'FloatTitle']],
                    'title_pos': 'left',
                    'relative': 'win'
                  }

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
    def show_float_definitions(self) -> None:
        definitions = self.nvim.call('coc#rpc#request', 'definitions', [])
        if definitions: self.open_float_window( definitions )
        else: self.nvim.command(f"echo 'No definitions found'")

    @pynvim.command('ShowFloatTypeDefinition') # type: ignore
    def show_type_definitions(self):
        definitions = self.nvim.call('coc#rpc#request', 'typeDefinitions', [])
        if definitions: self.open_float_window( definitions )
        else: self.nvim.command(f"echo 'No definitions found'")

    @pynvim.command('ShowFloatReferences') # type: ignore
    def show_float_references(self) -> None:
        references = self.nvim.call('coc#rpc#request', 'references', [])
        if references: self.open_float_window( references )
        else: self.nvim.command(f"echo 'No references found'")

    @pynvim.command('NextDefinition', nargs='*') # type: ignore
    def next_definition(self, args) -> None:
        win_id =  args[0] if args else self.nvim.call("win_getid")

        try: definitions = self.windows[win_id]['definitions']
        except: self.nvim.command(f"echo 'No definitions found for {win_id}'")
        else: self.handle_next_prev('Next', win_id, definitions)

    @pynvim.command('PrevDefinition', nargs='*') # type: ignore
    def previous_definition(self, args) -> None:
        win_id =  args[0] if args else self.nvim.call("win_getid")

        try: definitions = self.windows[win_id]['definitions']
        except: self.nvim.command(f"echo 'No definitions found for {win_id}'")
        else: self.handle_next_prev('Prev', win_id, definitions)

    def open_float_window(self, definitions: list) -> None:
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

    def handle_next_prev(self, action:str, win_id: int, definitions: list) -> None:
        if len(definitions)>1:
            curr_def = self.windows[win_id]['current_def']
            if   action == "Next": target = 0 if curr_def >= len(definitions) -1 else curr_def +1
            elif action == "Prev": target = len(definitions)- 1 if curr_def <= 0 else curr_def -1
            else: return
            pos_def = (definitions[target]['range']['start']['line'] + 1,
                       definitions[target]['range']['start']['character'])
            uri = definitions[target]['uri']
            buffer = self.nvim.exec_lua('return vim.uri_to_bufnr(...)', uri)
            self.nvim.call('nvim_win_set_buf', win_id, buffer)
            self.nvim.call('nvim_win_set_cursor', win_id, pos_def)
            self.windows[win_id]['current_def'] = target
            self.nvim.out_write(f'Showing [{target+1}/{len(definitions)}] definitions\n')

        else: self.nvim.command("echo 'No more definitions found'")

    def write_in_log(self, args):
        with open("log.txt", "w") as file_log:
            sys.stdout = file_log
            print(args)
            sys.stdout = sys.__stdout__
