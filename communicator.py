# -*- coding: utf-8 -*-

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
