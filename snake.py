# -*- coding: utf-8 -*-
from random import randint
from time import sleep
import os
from threading import Thread
import urllib.request as request
import json
import sys

class Window:
    @staticmethod
    def window_size(min_size=(10, 10)):
        from time import sleep
        from os import get_terminal_size

        min_w, min_h = min_size
        width, height = get_terminal_size()
        old_map = None
        while width < min_w or height < min_h:
            width, height = get_terminal_size()
            map = __class__.make_map(width, height)
            __class__.make_border_map(map, size=(width, height))
            string = f'{width}x{height}─>>─{min_w}x{min_h}'
            for i, s in enumerate(string):
                map[1][i+1] = s
            old_map = __class__.print_map(map, old_map)
            sleep(0.05)
    
    @staticmethod
    def make_map(width, height):
        map = [[' ' for _ in range(width)] for _ in range(height)]
        return map

    @staticmethod
    def make_border_map(map, size=(10, 10), border=None):
        if not border:
            border = (
            '┌', '─', '┐',
            '│',      '│',
            '└', '─', '┘'
            )
        width, height = len(map[0]), len(map)
        bor_width, bor_height = size
        for i in range(1, bor_height-1):
            map[i][0] = border[3]
            map[i][bor_width-width-1] = border[4]
        map[1] = list(border[0] + (border[1] * (bor_width - 2)) + border[2] + ' ' * (width - bor_width))
        map[bor_height-1] = list(border[5] + (border[6] * (bor_width - 2)) + border[7] + ' ' * (width - bor_width))
    
    @staticmethod
    def resize_map(map, new_size):
        w, h = len(map[0]), len(map)
        w_new, h_new = new_size
        blank_str = ' ' * w
        diff = ' ' * (w_new - w)
        if h_new != h:
            if h_new > h:
                [map.append(blank_str) for _ in range(h, h_new)]
            else:
                map = map[:h_new]
        if w_new != w:
            if w_new > w:
                for i in map:
                    i += diff
            else:
                for ind, lst in enumerate(map):
                    map[ind] = lst[:w_new]
        return map

    @staticmethod
    def print_map(map, old_map=None):
        if map == old_map:
            pass # return
        out = "\033[H"
        for i in map:
            out += ''.join(i)
        a = "\n\033[0E\033[2K"
        print(out + a, end="")
        return map


class Snake:
    def __init__(self, size=(10, 10)):
        import sys

        if sys.platform == "win32":
            recognising = Thread(target=self.win_recog, daemon=True)
        else:
            recognising = Thread(target=self.unix_recog, daemon=True)
        recognising.start()

        self.size = size
        self.w, self.h = size
        term_size = os.get_terminal_size()
        if term_size[0] < self.w or term_size[1] < self.h:
            Window.window_size(SIZE)
            term_size = os.get_terminal_size()
        map = Window.make_map(*term_size)
        Window.make_border_map(map, size=size)
        map[2] = map[1].copy()
        map[1] = map[0].copy()
        map[1][0] = map[1][size[0]-1] = '│'
        self.header = self.head_tmp = 'loading...'
        self.map = map

        value_thread = Thread(target=self.value)
        value_thread.start()

        self.win_amount = (self.w-2) * (self.h-4)
        self.frame_count = 0
        self.key = None
        self.old_map = None
        self.exit_flag = False
        self.new_game_flag = True
        self.end_game_flag = False
        self.end_game_option_flag = False

    def unix_recog(self):
        """unix like system keyboard's recognition"""
        import select
        import tty
        import termios
        global fd, old_settings

        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        tty.setraw(fd)
        while True:
            rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
            if rlist:
                char = sys.stdin.read(1)
                if ord(char) == 13:
                    self.key = "Key.enter"
                else:
                    self.key = char.rstrip()
            sleep(0.05)

    def win_recog(self):
        """windows keyboard's recognition"""
        import msvcrt
        while True:
            if msvcrt.kbhit():
                char = msvcrt.getwch()
                if ord(char) == 13:
                    self.key = "Key.enter"
                else:
                    self.key = char.rstrip()
                sleep(0.05)

    def value(self):
        """request to get current external rates"""
        global CURRENCIES, MAIN_CURRENSY
        link = 'https://cdn.jsdelivr.net/gh/fawazahmed0/currency-api@1/latest/currencies/'
        try:
            date = json.loads(request.urlopen(f'{link}usd/rub.json').read())['date'] + ' |'
            dct_s = ''
            for cur in CURRENCIES:
                cont = request.urlopen(f'{link}{cur}/{MAIN_CURRENSY}.json').read()
                dct_s += f" {cur}: {json.loads(cont)[MAIN_CURRENSY]:.2f},"
                self.frame_count = 0
                self.header = self.head_tmp = date + dct_s[:-1]
        except: 
            self.frame_count = 0
            self.header = self.head_tmp = 'network error'
    
    def swimming_string(self):
        if len(self.head_tmp) < self.w-2:
            self.head_tmp += ' ' * 5 + self.header
        out = self.head_tmp[:self.w-2]
        self.head_tmp = self.head_tmp[1:]
        return out

    def main(self):
        """which new frame will be drawn"""
        if self.exit_flag:
            return True
        elif self.new_game_flag:
            self.new_game_flag = False
            self.new_game()
        elif self.end_game_flag:
            if self.end_game_option_flag:
                self.end_game_option()
            else:
                self.end_game_option_flag = True
                self.pick_indx = 0
                self.end_game_map()
        else:
            self.game_tick()
        
        head = self.swimming_string()
        for indx, s in enumerate(head, 1):
            self.map[1][indx] = s
        self.frame_count += 1

        Window.print_map(self.map)

    def new_game(self):
        self.blank_game_map()
        self.max_fruit = self.w * (self.h - 3) / 4
        self.fruit_lst = []
        self.end_game = False
        self.i = 0
        self.direct = (0, 1)
        y, x = 5, 1
        self.pos_lst = [(y - 1, x), (y, x)]

    def blank_game_map(self):
        for i in range(3, self.h-1):
            for j in range(1, self.w-1):
                self.map[i][j] = ' '

    def end_game_map(self):
        self.score = len(self.pos_lst) - 2
        self.deadmenu = [
            ' You lost  ',
            f' Score: {self.score} ',
            ' Try again ',
            ' Exit      ',
            ]
        begin = (self.h) // 2 - 2
        if self.score == self.win_amount:
            self.deadmenu[0] = 'You won!. Thank you for the game'
        for line, y in zip(self.deadmenu, range(1, 5)):
            for symbol, x in zip(line, range(4, len(line)+4)):
                self.map[begin + y][x] = symbol
        self.map[begin + 3][3] = '*'

    def end_game_option(self):
        begin = (self.h) // 2 - 2
        key = self.key
        if key == 's':
            self.map[begin + 3][3] = ' '
            self.map[begin + 4][3] = '*'
            self.pick_indx = 1
        elif key == 'w':
            self.map[begin + 3][3] = '*'
            self.map[begin + 4][3] = ' '
            self.pick_indx = 0
        elif key == 'Key.enter':
            if self.pick_indx:
                self.exit_flag = True
            else: 
                self.new_game_flag = True
                self.end_game_flag = False
                self.end_game_option_flag = False

    def game_tick(self):
        """snake go shhh and move(fruits spawns also)"""
        def translate(inp):
            dct = {'w': (-1, 0), 'a': (0, -1), 's': (1, 0), 'd': (0, 1)}
            return dct.get(inp)

        def add_fruit():
            fruit = (randint(3, self.h-2), randint(1, self.w-2))
            self.fruit_lst.append(fruit)
            self.map[fruit[0]][fruit[1]] = '$'
            self.i = 0

        self.i += 1
        if self.i > 20 and len(self.fruit_lst) < self.max_fruit:
            add_fruit()
        if self.key:
            new_direct = translate(self.key)
            if new_direct is not None and new_direct[0] + self.direct[0] != 0 and new_direct[1] + self.direct[1] != 0:
                self.direct = new_direct

        self.move(self.direct)

#tf is going on here
    def move(self, d):
        pos = self.pos_lst[-1] # all snake's body
        pos = (pos[0] + d[0], pos[1] + d[1])
        h_flag = 2 < pos[0] < self.h-1 # flags if snake in borders
        w_flag = 0 < pos[1] < self.w-1
        if not h_flag or not w_flag or pos in self.pos_lst:
            self.end_game_flag = True
            return
        self.map[pos[0]][pos[1]] = 'o' # add to map new head
        self.pos_lst.append(pos)
        if pos in self.fruit_lst: # or not
            self.fruit_lst.remove(pos) 
        else:
            old_pos = self.pos_lst.pop(0) # clear tail
            self.map[old_pos[0]][old_pos[1]] = ' '

    @staticmethod
    def reset_terminal():
        if sys.platform in ("linux", "darwin"):
            import termios
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


if __name__ == '__main__':
    SIZE = [50, 20]
    MAIN_CURRENSY = 'rub'
    CURRENCIES = ('btc', 'usd', 'eur', 'cny')
    COMMANDS = [
        ' ', 
        ' -h, -help :  This.',
        ' ',
        ' window_size : {width}(>=20)x{height}(>=10)',
        ' terminal_size : current terminal size',
        ' ',
        ' list_all_currencies, list',
        ' main_currency {currency} ',
        ' currencies {currency},{currency}',
        ' '
        ]

    def parse_arg():
        global SIZE
        if len(sys.argv) > 1:
            for command in ('list_all_currencies', 'main_currency', 'currencies', 'list'):
                if command in sys.argv:
                    DCT_CURRENCIES = json.loads(request.urlopen("https://cdn.jsdelivr.net/gh/fawazahmed0/currency-api@1/latest/currencies.json").read())
                    break
            if 'currencies' in sys.argv:
                CURRENCIES = []
            size_term = os.get_terminal_size()
            for indx, i in enumerate(sys.argv[1:], 0):
                if i == 'help' or i == 'h' or i == '-help' or i == '-h' :
                    print(*COMMANDS, sep='\n')
                    exit()
                elif i == 'terminal_size':
                    print(*os.get_terminal_size())
                    exit()
                elif i == 'list_all_currencies' or i == 'list':
                    [print(f'{a}: {b}') for a,b in DCT_CURRENCIES.items()]
                    exit()
                elif i == 'window_size':
                    SIZE = []
                    size = sys.argv[indx+2].split('x')
                    if len(size) != 2:
                        print('Error: Wrong size')
                        exit()
                    for indx, j in enumerate(size):
                        if j.isdigit():
                            j = int(j)
                            if j <= size_term[indx] and j >= (20, 10)[indx]:
                                SIZE.append(j)
                            else:
                                print('Error: Wrong size')
                        else:
                            print('Error: Size must be integer')
                            exit()
                elif i == 'main_currency':
                    cur = sys.argv[indx+2]
                    if cur not in DCT_CURRENCIES:
                        print(f'Error: currency "{cur}" not in list')
                        exit()
                    MAIN_CURRENSY = cur
                elif i == 'currencies':
                    for cur in sys.argv[indx+2].split(','):
                        if cur not in DCT_CURRENCIES:
                            print(f'Error: currency "{cur}" not in list')
                            exit()
                    CURRENCIES.append(cur)

    def main():
        snake = Snake(size=SIZE)
        w_min, h_min = SIZE
        w, h = os.get_terminal_size()
        w_old, h_old = w, h
        os.system("")
        print("\033[?1049h")
        exit_flag = False
        while not exit_flag:
            w, h = os.get_terminal_size()
            if w < w_min or h < h_min:
                Window.window_size(SIZE)
            elif w != w_old or h != h_old: 
               snake.map = Window.resize_map(snake.map, (w, h))
            w_old, h_old = w, h
            exit_flag = snake.main()
            sleep(0.05)

    parse_arg()
    try:
        main()
    except KeyboardInterrupt:
        print("\033[?1049l\033[1A\nKeyboardInterrupt")
    finally:
        Snake.reset_terminal()
        print("\033[?1049l\033[1A")
