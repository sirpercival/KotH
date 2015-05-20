#!/usr/bin/env python
'''Possible options each turn [output]:
~ Rest (do nothing): 'rest'
~ Move (and possibly fall, if there's no support): 
        ['move up', 'move down', 'move left', 'move right']
~ Drop rock (rocks will fall until they are supported): 
        ['drop left', 'drop up', 'drop down (drops a rock in your space)', 
        drop right']
~ Throw rock (rock max distance based on height; rock impact will break target, 
              killing if bot; throw up is suicide if you're at the top of a 
              pile; throw down destroys the rock below you): 
        ['throw left range', 'throw right range', 'throw up range', 
        'throw down range']

Bot visual range (each side) = 1 + 2*elevation
input is a string representation of the visual range 
(air: '.', rock: '&', self: 's', self&rock: 'S', enemybot: 'e', 
enemy&rock: 'E', boundary: '#', meteor: '@']

Destroying a rock in a stack moves all rocks & bots 
down one elevation level in the stack.'''

import numpy as np
import random
import pdb
from communicator import Communicator

replay = 0
try:
    import matplotlib.pyplot as plt
    from matplotlib import animation
    from distutils.spawn import find_executable
    if find_executable('convert') is None:  #check for ImageMagick install
        replay = -1
        raise ImportError
    replay = True
except ImportError:
    import warnings
    warnings.warn('Replay not supported: ' + ['matplotlib not found',
                                              'ImageMagick not found'][replay],
                  RuntimeWarning)


LEGEND = {'bound': '#',
          'air': '.',
          'rock': '&',
          'bot': 'b',
          'botrock': 'B',
          'self': 's',
          'enemy': 'e',
          'selfrock': 'S',
          'enemyrock': 'E',
          'meteor': '@'}
LOOKUP = {LEGEND[k]: k for k in LEGEND}
ADDBOT = {'.':'b', '&':'B', '@':'@'}
ADDSELF = {'.':'s', '&':'S', '@':'@'}
ADDENEMY = {'.':'e', '&':'E', '@':'@'}

COLOR = {'.': [0.95, 0.95, 0.95],
         '&': [0.2, 0.2, 0.2],
         'b': [0., 1., 0.],
         'B': [0.2, 0.6, 0.6],
         '@': [1., 0., 0.],
         '#': [0., 0., 0.]}

class Bot(object):
    '''the controller-side implementation for a bot (with the bot-side
    implementation contributed by whatever author)'''
    dirs = {'up': (0 , 1),
            'down': (0, -1),
            'left': (-1, 0),
            'right': (1, 0)}

    def __init__(self, logic=None, x=0):
        '''logic is a Communicator'''
        self.logic = logic
        self.name = logic.name
        self.location = x
        self.elevation = 0
        self._dead = False

    @property
    def coords(self):
        '''get the coords'''
        return [self.location, self.elevation]

    @coords.setter
    def coords(self, value):
        '''validate value, then set coords.'''
        if not all([isinstance(value, list),
                    len(value) == 2,
                    all(isinstance(_, int) for _ in value)]):
            raise ValueError('value must be a list of 2 integers')
        self.location, self.elevation = value

    @property
    def dead(self):
        '''am i dead? i might be.'''
        return self._dead

    def kill(self):
        '''suicide, or murder, whatever.'''
        self._dead = True

    def _shift(self, dx, dy):
        '''shift position'''
        self.location += dx
        self.elevation += dy

    def _fall(self, distance):
        '''fall a distance, testing for death'''
        self._shift(0,-distance)
        if distance > 1:
            self.kill()

    def move(self, board, direction='down', *arg):
        '''perform a move in one of the four directions,
        handling falling.'''
        direction = direction.lower()
        x, y = self.coords
        dx, dy = self.dirs[direction]
        if board.boundary(x + dx, y + dy):
            return
        self._shift(dx, dy)
        fall = board.fall_distance(*self.coords)
        self._fall(fall)

    def rest(self, board, *arg):
        '''literally do nothing'''
        pass

    def throw(self, board, direction='down', distance=None, *arg):
        '''throw a rock a distance (in x); if no distance given,
        or if distance > elevation, use elevation. distance=0
        destroys the rock/enemy below you (if any).'''
        direction = direction.lower()
        x, y = self.coords
        if distance == 0 or direction == 'down':
            board.collide(x, y-1)
            return
        if distance is None or distance >= self.elevation:
        #we move out 1 space before falling
            distance = max([self.elevation - 1,0])
        if direction == 'up': #uh oh
            if not board.collide(x, y+1):
                board.collide(x,y)
            return
        dy = float(self.elevation) / float(distance) if distance > 0 else 1
        dx = self.dirs[direction][0]
        x = x + dx
        b = board.find_bot(x, y)
        #if b != None:
        #    pdb.set_trace()
        while not board.collide(x, y):
            x, y = x + dx, int(y - dy)
        if b != None and not b.dead:
            pdb.set_trace()

    def drop(self, board, direction='down', *arg):
        '''drop a rock. dropping 'down' puts the rock in your space
        if there isn't one already there; dropping 'left' or 'right'
        drops the rock to the nearest supported space; dropping 'up'
        puts the rock in the space above you (which could fall and 
        crush you, so beware.)'''
        direction = direction.lower()
        x, y = self.coords
        if direction == 'down':
            if 'rock' in board(x, y):
                return
            board.place_rock(x, y)
        else:
            dx, dy = self.dirs[direction]
            if board.boundary(x + dx, y + dy):
                return
            x_rock = x + dx
            y_rock = y + dy - board.fall_distance(x_rock, y + dy)
            board.crush(x_rock, y_rock)
            board.place_rock(x_rock, y_rock)

    def __call__(self, board):
        '''send the input to the bot code via the Communicator,
        and parse the output for syntactic validity.'''
        view = board.view(*self.coords)
        output = self.logic(view)
        #time to parse the donuts
        output = output.lower().split()
        direction = distance = None
        action = output[0]
        if action not in ['rest','move','drop','throw']:
            action = 'rest'
        if len(output) > 1:
            direction = output[1]
            if direction not in self.dirs.keys():
                action = 'rest'
        try:
            distance = int(output[2])
        except IndexError:
            pass
        except ValueError:
            action = 'rest'
        return action, direction, distance

class Meteor(object):
    '''a quick & dirty meteor, which falls from a random point at
    the top of the board at a speed of 2/step, at a random angle.'''
    def __init__(self):
        from itertools import count
        from math import sin, cos, radians
        r, theta = 2, radians(random.randrange(-180,0))
        self._xpar = count(random.randrange(100), r * cos(theta))
        self._ypar = count(99, r * sin(theta))
        self.x = self.y = None
        self.destroy = False
    
    @property
    def coords(self):
        return int(self.x), int(self.y)
    
    def step(self):
        '''we're using count()s as our parametric equations'''
        self.x = next(self._xpar)
        self.y = next(self._ypar)


class Board(object):
    '''The game itself'''
    def __init__(self, bot_list, mode='free-for-all', max_turns = 500):
        self._botlist = bot_list
        self._board = np.full((100,100),'.',dtype='string_')
        bot_initial_positions = random.sample(xrange(100), len(self._botlist))
        self._bots = [Bot(logic=b, x=bot_initial_positions[i]) for i, b 
                      in enumerate(self._botlist)]
        self._meteors = []
        self.deathturn = []
        self._turn = 0
        self.history = []
        self.save_snapshot()
        self.max_turns = max_turns - 1
        self.done = False

    @property
    def bot_pos(self):
        '''a list of bot positions'''
        return [bot.coords for bot in self._bots]
    
    @property
    def nbot(self):
        '''how many bots are left?'''
        return len(self._bots)

    def __call__(self, x, y):
        '''this gets the description of the thing, not the character,
        which is accessible from self._board'''
        if self.find_bot(x, y) != None:
            return LOOKUP[ADDBOT[self._board[y,x]]]
        return LOOKUP[self._board[y, x]]

    def __repr__(self):
        '''generate a bot-neutral string representation of the board'''
        board = self._board.copy()
        nrow, ncol = board.shape
        for x, y in self.bot_pos:
            if not self.find_bot(x, y).dead:
                board[y, x] = ADDBOT[board[y, x]]
        for m in self._meteors:
            x, y = m.coords
            board[y, x] = LEGEND['meteor']
        rows = ['#%s#' % ''.join(board[row].tolist()) for row in 
                reversed(xrange(nrow))]
        rows = ['#' * (ncol + 2)] + rows + ['#' * (ncol + 2)]
        return '\n'.join(rows)

    def find_bot(self, x, y):
        '''locate a bot or return None if it ain't there.'''
        for bot in self._bots:
            if bot.location == x and bot.elevation == y and not bot.dead:
                return bot
        return None
    
    def boundary(self, x, y):
        '''are we off the edge of the board?'''
        return x < 0 or x > 99 or y < 0 or y > 99
        #return self._board[y, x] == '#'

    def collide(self, x, y):
        '''see if the projectile at this location hits anything.
        if it hits something other than the border, like a rock
        or a bot, the target is destroyed; any rocks or bots supported
        by the destroyed target fall 1 square (we hope, this part isn't
        working yet...)'''
        if any([_ < 0 or _ > 99 for _ in [x, y]]):
            return True
        has = self(x, y)
        if has == 'air':
            return False
        elif has == 'bound':
            return True
        else: #we're gonna destroy one or more things
            self.crush(x, y)
            column = [(ele, self(x, ele)) for ele in range(100)] #grab the whole column
            rocks = [ele for ele, _ in column if 'rock' in _]
            bots = [ele for loc, ele in self.bot_pos if loc == x]
            nrock = max([len(rocks) - 1,0]) #we just destroyed one, maybe
            toprock = max(rocks) if len(rocks) > 0 else 0
            self._board[:,x] = '.'
            self._board[:nrock, x] = '&'
            for bot in bots:
                if bot < y:
                    continue
                if bot < toprock:
                    self.crush(x, bot)
                else:
                    b = self.find_bot(x, bot)
                    if b is not None:
                        b._fall(1)
            return True

    def crush(self, x, y):
        '''kill a bot in this square, if any'''
        bot = self.find_bot(x, y)
        if bot is not None:
            bot.kill()

    def fall_distance(self, x, y):
        '''how far do we have to fall to get to a supported space?'''
        fall = 0
        y0 = lambda t: y - t - 1
        test = lambda s: s not in ('bound', 'rock') and s >= 0 and s <= 99
        while test(self(x, y0(fall))):
            fall += 1
        return fall

    def place_rock(self, x, y):
        '''put a rock here.'''
        self._board[y, x] = '&'            
    
    @staticmethod
    def build_string(b):
        nrow, ncol = b.shape
        return '\n'.join([''.join(b[row].tolist()) 
                            for row in reversed(xrange(nrow))])

    def view(self, x0, y0):
        '''put together a view string to pass to a bot.
        max view distance is 20 squares in any direction (chebyshev).
        we must account for the border as well.'''
        lx, hx, ly, hy = np.clip([x0 - 19, x0 + 21, y0 - 19, y0 + 21], 0, 101)
        board = np.full((102, 102),'#',dtype='string_')
        board[1:101, 1:101] = self._board
        for x, y in self.bot_pos:
            board[y + 1, x + 1] = ADDSELF[board[y + 1, x + 1]] \
                                  if (x, y) == (x0, y0) else \
                                  ADDENEMY[board[y + 1, x + 1]]
        for m in self._meteors:
            x, y = m.coords
            board[y + 1, x + 1] = LEGEND['meteor']
        b = board[ly:hy + 1, lx:hx + 1]
        return self.build_string(b)
    
    def step(self):
        '''priority: rests -> moves -> drops -> throws -> meteors
        priority pt 2: low elevation -> high elevation'''
        self._turn += 1
        actions = [[bot, bot.elevation, bot(self)] for bot in self._bots]
        for act in ('rest', 'move', 'drop', 'throw'):
            these = sorted(filter(lambda b: b[2][0] == act, actions), 
                           key = lambda b: b[1])
            for bot in these:
                if bot[0].dead:
                    continue
                f = getattr(bot[0], act)
                f(self, *bot[2][1:])
        #now we handle bot-bot collisions:
        coords = [(bot, bot.coords) for bot in self._bots]
        while len(coords) > 1:
            b = coords.pop()
            for i, c in enumerate(coords):
                if b[1] == c[1]:
                    b[0].kill()
                    c[0].kill()
                    del coords[i]
        #meteors time!
        self._meteors.append(Meteor())
        for i, m in enumerate(self._meteors):
            m.step()
            m.destroy = self.collide(*m.coords)
        self._meteors = filter(lambda m: not m.destroy, self._meteors)
        #garbage collection
        self.deathturn.append([self._turn, 
                               filter(lambda b: b.dead, self._bots)])
        self._bots = filter(lambda b: not b.dead, self._bots)
        self.save_snapshot()
        if self._turn >= self.max_turns:
            self.deathturn.append([self._turn + 1, self._bots])
            self.done = True
        else:
            self.done = len(self._bots) == 0
        
    def save_snapshot(self):
        '''save a snapshot of the game board, for replays later'''
        nrow, ncol = self._board.shape
        record = {'bots': [tuple(_) for _ in self.bot_pos], 
                  'rocks': [(loc, ele) for ele in xrange(nrow) 
                            for loc in xrange(ncol) 
                            if self._board[ele, loc] == LEGEND['rock']],
                  'meteors': [tuple(m.coords) for m in self._meteors]}
        self.history.append(record)

class Controller(object):
    '''this loads the bots and runs the games.'''
    def __init__(self, botdir):
        self.botdir = botdir
        self.bot_names = Communicator.read_bot_list(botdir)
        self.bots = []
        self.load_bots()
        
    def load_bots(self):
        bd = self.botdir
        for d in self.bot_names:
            with open(os.path.join(bd, d, "command.txt"), 'r') as f:
                commands = f.read().splitlines()
            if commands:
                for command in commands[0:-1]:
                    subprocess.call(command.split(" "), 
                                    cwd=os.path.join(bd, d))
                if WINDOWS:
                    commands[-1] = commands[-1].replace("./", 
                                                        os.path.join(bd, d)
                                                        + "/")
                #no_print = os.path.isfile(botdir+d+"/noprint")
                no_print = True
                self.bots.append(Communicator(bot_name=d, 
                                              command=commands[-1],
                                              no_print=no_print,
                                              botdir = bd))
        self.scores = {b:[] for b in self.bot_names}

    def run(self, ngame=1):
        '''run some number of games.'''
        self.games = [Board(self.bots) for _ in xrange(ngame)]
        for game in self.games:
            if debug: print 'Running the next game!'
            while not game.done:
                game.step()
                #print 'Turn %i, living bots: %s' % (game._turn, 
                #                ', '.join([b.logic.name for b in game._bots]))
            for turn, dead in game.deathturn:
                for bot in dead:
                    self.scores[bot.name].append(turn)

    def leaderboard(self):
        '''accumulate all the bots' scores across all games
        and return an ok-formatted leaderboard'''
        score_accum = {bot: sum(score) for bot, score in self.scores.items()}
        rows = []
        for bot in sorted(score_accum, reverse=True, 
                          key=lambda x: score_accum[x]):
            iscores = '+'.join(['{:3d}'.format(s) for s in self.scores[bot]])
            rows.append('{:20} -> {} = {:d}'.format(bot, iscores,
                                                    score_accum[bot]))
        return '\n'.join(rows)
    
    def save_replay(self, gid, filename='Abotalypse_Replay'):
        '''use a matplotlib animation (output to webm) to show
        a replay of a game's history.'''
        if replay < 1:
            return
        history = self.games[gid].history
        fig = plt.figure(figsize=(6, 6))
        plt.axis('off')
        blank = np.full((100,100,3), COLOR['.'])
        im = plt.imshow(blank, interpolation='nearest')
        def init():
            im.set_array(blank)
            return [im]
        def animate(i):
            turn = history[i]
            img = np.full((100,100,3), COLOR['.'])
            all_things = {xy:'&' for xy in turn['rocks']}
            all_things.update({xy:'@' for xy in turn['meteors']})
            all_things.update({xy:ADDBOT[all_things.get(xy,'.')] 
                                for xy in turn['bots']})
            for (x, y), char in all_things.items():
                img[y, x] = COLOR[char]
            img = img[::-1,...]
            im.set_array(img)
            return [im]
        anim = animation.FuncAnimation(fig, animate, init_func=init,
                                       frames=len(history), interval=20,
                                       blit=True)
        anim.save('replays/' + filename + '.webm', writer='ffmpeg',
                  fps=30, extra_args=['-vcodec', 'libvpx'])

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Run ABOTCALYPSE')
    parser.add_argument('-n', '--ngame', type=int, dest='ngame', default=20)
    parser.add_argument('--default', action='store_true')
    parser.add_argument('-r', '--replay', action='store_true')
    parser.add_argument('botdir', nargs='?', default='bots/')
    parser.add_argument('--ndefault', type=int, default=2)
    
    args = parser.parse_args()
    botdir = 'default_bots/' if args.default else args.botdir
    ng = args.ngame
    print 'Playing {:d} games, with bots from the folder: {}'.format(ng,botdir)
    if args.default:
        import tempfile, shutil
        available = [x for x in os.listdir(botdir) 
                     if os.path.isdir(os.path.join(botdir, x))]
        bot_names = [random.choice(available) 
                     for _ in xrange(args.ndefault)]
        defdir = tempfile.mkdtemp(dir='.')
        for i,b in enumerate(bot_names):
            src = os.path.join(botdir, b)
            dst = os.path.join(defdir, str(i) + '_' + b)
            os.mkdir(dst)
            for item in os.listdir(src):
                s = os.path.join(src, item)
                d = os.path.join(dst, item)
                if os.path.isdir(s):
                    shutil.copytree(s, d)
                else:
                    shutil.copy2(s, d)
        botdir = defdir
    game = Controller(botdir = botdir)
    print 'Game created!'
    game.run(ng)
    print game.leaderboard()
    if args.replay:
        for i in range(ng):
            print 'saving replay for game #'+str(i+1)
            game.save_replay(i, 
                             filename='Abotcalypse_Replay_' + str(i + 1)
                                      + '_of_' + str(ng))
    if args.default:
        pass
        #shutil.rmtree(botdir)
