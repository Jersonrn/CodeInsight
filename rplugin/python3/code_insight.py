import os
import sys
import pynvim


def get_default_config(nvim) -> dict:
    columns: int = nvim.api.get_option('columns')
    lines: int = nvim.api.get_option('lines')
    cmd_height = nvim.api.get_option('cmdheight')

    width: float = int((columns * 0.5)//1)
    height: float = int((lines * 0.5)//1)
    
    opts: dict = {'relative': 'win',
                  'anchor': 'NW',
                  'width': width,
                  'height': height,
                  'row': 0,
                  'col': int((columns - width)//1.0),
                  'focusable': True,
                  'external': False,
                  'zindex': 1,
                  'border': ['❖', '═', '╗', '║', '⇲', '═', '╚', '║'],
                  'title': [["CodeInsight", 'FloatTitle']],
                  'title_pos': 'left',
                  }
    config: dict = {"pos":"top-right",
                    "opts":opts}
    return config

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
        except: config = get_default_config(self.nvim)
        self.config = config if type(config['opts']['focusable']) == bool else fix_config(config)

    @pynvim.function('CodeInsightWinClosed', sync=True) 
    def win_closed(self, win_id) -> None:
        try: del self.windows[win_id[0]]
        except: return

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
        curr_def: int = 0
        pos_def: tuple = (definitions[curr_def]['range']['start']['line'] + 1,
                          definitions[curr_def]['range']['start']['character'])
        uri = definitions[curr_def]['uri']
        buffer = self.nvim.exec_lua('return vim.uri_to_bufnr(...)', uri)
        opts = self.config['opts']
        opts['title'][0][0] = f"{os.path.basename(uri)}[{curr_def +1}/{len(definitions)}]"

        win_id = self.nvim.call('nvim_open_win', buffer, 1, opts)
        self.nvim.call('nvim_win_set_cursor', win_id, pos_def)
        self.nvim.call('nvim_win_set_var',win_id,'pos', self.config['pos'])
        self.windows[win_id] = {'current_def': curr_def,
                                'definitions': definitions}
        self.nvim.out_write(f'Showing [{curr_def+1}/{len(definitions)}] definitions\n')

    def handle_next_prev(self, action: str, win_id: int, definitions: list) -> None:
        len_def = len(definitions)
        if len_def > 1:
            curr_def = self.windows[win_id]['current_def']
            if   action == "Next": target = 0 if curr_def >= len_def -1 else curr_def +1
            elif action == "Prev": target = len_def -1 if curr_def <= 0 else curr_def -1
            else: return
            pos_def = (definitions[target]['range']['start']['line'] + 1,
                       definitions[target]['range']['start']['character'])
            uri = definitions[target]['uri']
            buffer = self.nvim.exec_lua('return vim.uri_to_bufnr(...)', uri)
            self.nvim.call('nvim_win_set_buf', win_id, buffer)
            self.nvim.call('nvim_win_set_cursor', win_id, pos_def)
            self.windows[win_id]['current_def'] = target

            opts: dict = self.nvim.api.win_get_config(win_id)
            opts['title'][0][0] = f"{os.path.basename(uri)}[{target +1}/{len_def}]"
            self.nvim.api.win_set_config(win_id, opts)

            self.nvim.out_write(f'Showing [{target+1}/{len_def}] definitions\n')

        else: self.nvim.command("echo 'No more definitions found'")

    def write_in_log(self, *args):
        with open("log.txt", "w") as file_log:
            sys.stdout = file_log
            print(args)
            sys.stdout = sys.__stdout__

    @pynvim.command('OldMoveFloatWindow', nargs='*') # type: ignore
    def old_move_float_window(self, args) -> None:
        direction: str | None = args[0][1:-1] if args else None

        if direction is not None:
            win_id: int = self.nvim.api.get_current_win()
            opts: dict = self.nvim.api.win_get_config(win_id)
            is_floating: bool = False if opts and opts["relative"] == '' else True

            if is_floating:
                if   direction == "h": new_anchor: dict = {'NE':'NW', 'SE':'SW'}
                elif direction == 'j': new_anchor: dict = {'NW':'SW', 'NE':'SE'}
                elif direction == 'k': new_anchor: dict = {'SW':'NW', 'SE':'NE'}
                elif direction == 'l': new_anchor: dict = {'NW':'NE', 'SW':'SE'}
                else: return

                try: opts['anchor'] = new_anchor[opts['anchor']]
                except: return
                else: self.nvim.api.win_set_config(win_id, opts)

    @pynvim.command('MoveFloatWindow', nargs=1) # type: ignore
    def move_float_window(self, dir) -> None:
        direction: str | None = dir[0][1:-1] if dir else None
        win_id: int = self.nvim.api.get_current_win()
        opts: dict = self.nvim.api.win_get_config(win_id)
        width, height = opts['width'], opts['height']
        is_floating: bool = False if opts and opts["relative"] == '' else True

        if direction is not None and is_floating:
            col, lines = self.nvim.eval('&columns'), self.nvim.eval('&lines')
            cmd_height = self.nvim.eval('&cmdheight')
            cell_coords = {
                    'top-left': (0,0),    'top': (1,0),    'top-right': (2,0),
                    'left': (0,1),        'center': (1,1), 'right': (2,1),
                    'bottom-left': (0,2), 'bottom': (1,2), 'bottom-right': (2,2)}

            try: position: str = self.nvim.call('nvim_win_get_var', win_id, 'pos')
            except: position: str = "center"
            pos: tuple = cell_coords[position]

            x, y = (0, 1)
            pos = (
                (pos[x] - 1 if pos[x] > 0 else 0, pos[y]) if direction == "h" else
                (pos[x], pos[y] + 1 if pos[y] < 2 else 2) if direction == "j" else
                (pos[x], pos[y] - 1 if pos[y] > 0 else 0) if direction == "k" else
                (pos[x] + 1 if pos[x] < 2 else 2, pos[y]) if direction == "l" else
                (pos[x], pos[y]) )

            coords_settings: dict = {
                (0,0):{'row':0, 'col':0},
                (1,0):{'row':0, 'col':(col - width) * 0.5},
                (2,0):{'row':0, 'col':col - width},

                (0,1):{'row': (lines - height - cmd_height - 1) * 0.5, 'col': 0},
                (1,1):{'row': (lines - height - cmd_height - 1) * 0.5, 'col': (col - width) * 0.5},
                (2,1):{'row': (lines - height - cmd_height - 1) * 0.5, 'col': col - width},

                (0,2):{'row': lines - height - cmd_height - 1, 'col': 0},
                (1,2):{'row': lines - height - cmd_height - 1, 'col': (col - width) * 0.5},
                (2,2):{'row': lines - height - cmd_height - 1, 'col': col - width},
                }
            opts['row'] = int(coords_settings[pos]['row'] // 1)
            opts['col'] = int(coords_settings[pos]['col'] // 1)
            self.nvim.api.win_set_config(win_id, opts)
            position = [i for i in cell_coords if cell_coords[i] == pos][0]
            self.nvim.call('nvim_win_set_var', win_id, 'pos', position)

