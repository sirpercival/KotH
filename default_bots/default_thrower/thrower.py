'''A bot which moves around and throws rocks at stuff in its way.

Call with "$ python thrower.py" and then at each prompt, "next <input>"'''

import json
import os

DIRECTIONS = {'left': (-1, 0),
              'right': (1, 0)}
THROW = ['e','E','&']
RUN = ['@', '#']
RUN_DIR = {'left': 'right', 'right':'left'}


class Bot(object):
    def __init__(self, store = 'storage.txt'):
        if not os.path.isfile(store): #ensure existence of store
            open(store,'w').close()
        self.storage = store
        self.x = self.y = 0
        self.previous_xy = (0, 0)
        self.previous_move = 'left'
        self.current_move = 'left'
        self.previous_action = 'rest'
        self.current_action = 'rest'
        self.neighbors = {}
        self.current_symbol = 's'
        self.board = ''
        self.turn = 0
    
    @property
    def current_xy(self):
        return self.x, self.y
        
    def load(self):
        try:
            with open(self.storage, 'r') as f:
                history = json.load(f)
                self.__dict__ = history[-1]
        except ValueError:
            pass
    
    def save(self):
        try:
            with open(self.storage, 'r') as f:
                history = json.load(f)
        except ValueError:
            history = []
        history.append(self.__dict__)
        with open(self.storage, 'w') as f:
            json.dump(history, f)
    
    def read_board(self):
        self.turn += 1
        self.symbol = 's' if self.board.count('s') else 'S'
        self.previous_xy = self.current_xy[:]
        board = self.board.splitlines()
        #find self
        for y, row in enumerate(board):
            x = row.find(self.symbol)
            if x >= 0:
                break
        else:
            self.x, self.y = self.previous_xy
        self.x = x 
        self.y = y
        for d, (dx, dy) in DIRECTIONS.items():
            self.neighbors[d] = board[y-dy][x+dx]
        
    def get_throw(self):
        for d, n in self.neighbors.items():
            if n in THROW:
                return d
        return None
                
    def get_run(self):
        for d, n in self.neighbors.items():
            if n in RUN:
                return d
        return None
    
    def get_move(self):
        return self.previous_move
    
    def action(self):
        self.previous_action = self.current_action
        throw = self.get_throw()
        if throw is not None:
            self.current_action = 'throw ' + throw + ' 1'
            return self.current_action
        run = self.get_run()
        if run is not None:
            self.previous_move = self.current_move
            self.current_move = RUN_DIR[run]
            self.current_action = 'move ' + self.current_move
            return self.current_action
        self.previous_move = self.current_move
        move = self.get_move()
        self.current_move = move
        self.current_action = 'move ' + move
        return self.current_action
    
    def act(self, board):
        self.load()
        self.board = board
        self.read_board()
        action = self.action()
        self.save()
        print action

if __name__ == "__main__":
    import sys
    bot = Bot()
    bot.act(sys.argv[1])
