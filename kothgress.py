# -*- coding: utf-8 -*-

import random
from string import ascii_uppercase, ascii_lowercase, digits, punctuation
import select
import os
import subprocess
import shlex

debug = __debug__
WINDOWS = False

try:
    select.poll()
except AttributeError:
    WINDOWS = True

all_voices = ascii_uppercase + ascii_lowercase + digits + punctuation
    
class Communicator(object):
    '''a class for handling language-agnostic bot interface, via
    subprocess. commands are handled via a commands.txt file in
    the bot's directory, one command per line, with the last command
    handling the actual interface (everything before it is pre-run).'''
    def __init__(self, bot_name, command, no_print, botdir = "bots/"):
        self.name = bot_name
        self.no_print = no_print
        self.commands = shlex.split(command)
        self.response = None
        self.cwd = os.path.join(botdir, self.name)
    
    def __call__(self, message):
        '''pass the input to the bot, and send back the response.'''
        args = self.commands[:]
        if message is not None:
            args.append(message)
            if debug and not self.no_print:
                print "sent view to " + self.name + " :\n" + message
        with open(os.path.join(self.cwd,'errlog.txt'),'a') as f:
            self.response = subprocess.check_output(args=args, cwd=self.cwd,
                                                stderr=f).strip()
        if debug and not self.no_print:
            print "got response from "+self.name+" : "+self.response
        return self.response
    
    @staticmethod
    def read_bot_list(botdir = 'bots/'):
        '''get a list of all bots in the directory for 
        which we have commands'''
        return [n for n in os.listdir(botdir)
                if os.path.isfile(os.path.join(botdir, n, "command.txt"))]

class Bot(object):
    '''the controller-side implementation for a bot (with the bot-side
    implementation contributed by whatever author)'''
    def __init__(self, logic=None, voice='A', start_pos = []):
        self.logic = logic
        self.voice = voice
        self.name = logic.name
        self.score = 0
        self.pos = start_pos
    
    def __call__(self, register):
        points = 20 * register.count(self.voice)
        output = self.logic(' '.join([self.voice, str(self.bank), str(points), `register`]))
        try:
            bids = dict([map(int,x.split()) for x in output.split('|')])
            bids = {k-1:v for k,v in bids.iteritems()}
            totalbid = sum(bids.values())
            if totalbid > self.points: 1/0
            self.score += self.points - totalbid
            return bids
        except:
            return None
    
    def update_pos(self, new_pos = []):
        self.pos = new_pos
        self.score += sum(self.pos) + len(self.pos)

class Meeting(object):
    '''The game itself'''
    def __init__(self, bot_list, max_turns = 100):
        random.shuffle(bot_list)
        self._botlist = bot_list
        self.len = max(100,4*len(bot_list))
        self._register = [' ']*self.len
        voices = all_voices[:len(bot_list)]
        self._bots = [Bot(logic=b, voice=voices[i]) 
                        for i,b in enumerate(self._botlist)]
        self._turn = 0
        self.history = []
        self.save_snapshot()
        self.max_turns = max_turns - 1
        self.done = False
    
    def __repr__(self):
        return ''.join(self._register)
    
    def step(self):
        if self._turn >= self.max_turns:
            return
        self._turn += 1
        register = `self`
        bids = {bot(register) for bot in self._bots}
        bids = {k:v for k,v in bids.iteritems() if v != None}
        pos = {x:(self._register[x], 0) for x in xrange(self.len)}
        for bot, bid in bids.items():
            for p, b in bid.items():
                if b[1] > pos[p][1]: pos[p] = (bot.voice, b)
                elif b[1] == pos[p][1]: pos[p] = (self._register[p], b)
        self._register = [pos[p][0] for p in xrange(self.len)]
        new_pos = {bot.voice:list() for bot in self._bots}
        for ind, voice in enumerate(self._register):
            new_pos[voice] += ind,
        for bot in self._bots:
            bot.update_pos(new_pos[bot.voice])
        self.save_snapshot()
    
    def save_snaphot(self):
        self.history[self._turn] = (`self`, [(bot.name, 
                                              bot.voice, 
                                              bot.score) for bot in self._bots])