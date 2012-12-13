#!/usr/bin/env python

#
# :copyright: (c) 2012 by Mike Taylor
# :license: BSD 2-Clause
#

__version__   = u'0.5.0'
__copyright__ = u'Copyright (c) 2012 Mike Taylor'
__license__   = u'BSD 2-Clause'
__author__    = u'bear (Mike Taylor) <bear@code-bear.com>'

import os
import os.path
import sys
import json
import types
import logging

from optparse import OptionParser

_ourPath = os.getcwd()
_ourName = os.path.splitext(os.path.basename(sys.argv[0]))[0]
log      = logging.getLogger(_ourName)

def initLogs(logger, echo=True, chatty=False, debug=False, loglevel=logging.INFO, logpath=None, logname=None):
    """ Initialize logging
    """
    if logpath is not None:
        if logname is None:
            logname = _ourName

        fileHandler   = logging.FileHandler(os.path.join(logpath, logname))
        fileFormatter = logging.Formatter('%(asctime)s %(levelname)-7s %(processName)s: %(message)s')

        fileHandler.setFormatter(fileFormatter)

        logger.addHandler(fileHandler)
        logger.fileHandler = fileHandler

    if echo:
        echoHandler = logging.StreamHandler()

        if chatty:
            echoFormatter = logging.Formatter('%(asctime)s %(levelname)-7s %(processName)s[%(process)d]: %(message)s')
        else:
            echoFormatter = logging.Formatter('%(asctime)s %(levelname)-7s %(message)s')

        echoHandler.setFormatter(echoFormatter)

        logger.addHandler(echoHandler)

    if debug:
        logger.setLevel(loglevel)
    else:
        logger.setLevel(logging.DEBUG)

# HACK
# yes, I am loading a custom log config right after defining the helper routine
# that does the log init
# I have not found a way to enable console echoing during the config item creation
# in a way that doesn't completely stink up the room!
initLogs(log, echo=True, debug=True)

class BearConfig(object):
    def __init__(self, configFilename=None):
        """ Parse command line parameters and populate the options object
        """
        self.log            = logging.getLogger(_ourName)
        self.options        = None
        self.appPath        = _ourPath
        self.configFilename = configFilename
        self.config         = {}

        # these are my normal defaults
        self.bears_config   = { 'configFile':  ('-c', '--config',  self.configFilename, 'Configuration Filename (optionally w/path'),
                                'debug':       ('-d', '--debug',   False,               'Enable Debug'),
                                'echo':        ('-e', '--echo',    False,               'Enable log echo to the console'),
                                'logpath':     ('-l', '--logpath', '',                  'Path where log file is to be written'),
                                'logfile':     ('',   '--logfile', '%s.log' % _ourName, 'log filename'),
                                'verbose':     ('-v', '--verbose', False,               'show extra output from remote commands'),
                              }

    def findConfigFile(self, paths=None, envVar=None):
        searchPaths = []

        if paths is not None:
            for path in paths:
                log.debug('adding %s to the search path' % path)
                searchPaths.append(path)

        for path in (_ourPath, os.path.expanduser('~')):
            log.debug('adding %s to the search path' % path)
            searchPaths.append(path)
        
        if envVar is not None and envVar in os.environ:
            path = os.environ[envVar]
            log.debug('adding %s to the search path' % path)
            searchPaths.append(path)

        for path in searchPaths:
            s = os.path.join(path, self.configFilename)
            if os.path.isfile(s):
                log.debug('configuation file found: %s' % s)
                self.options.configFile = s

    def addConfig(self, key, shortCmd='', longCmd='', defaultValue=None, helpText=''):
        if len(shortCmd) + len(longCmd) == 0:
            log.error('You must provide either a shortCmd or a longCmd value - both cannot be empty')
        elif key is None and type(key) is types.StringType:
            log.error('The configuration key must be a string')
        else:
            self.config[key] = (shortCmd, longCmd, defaultValue, helpText)

    def load(self, defaults=None, configPaths=None, configEnvVar=None):
        parser        = OptionParser()
        self.defaults = {}

        if defaults is not None:
            for key in defaults:
                self.defaults[key] = defaults[key]

        # load my config items, but just in case the caller has other ideas
        # do not load them if the key is already present
        # TODO need to add some way to also cross check short/long command values
        for key in self.bears_config:
            if key not in self.config:
                self.config[key] = self.bears_config[key]

        for key in self.config:
            items = self.config[key]

            (shortCmd, longCmd, defaultValue, helpText) = items

            if type(defaultValue) is types.BooleanType:
                parser.add_option(shortCmd, longCmd, dest=key, action='store_true', default=defaultValue, help=helpText)
            else:
                parser.add_option(shortCmd, longCmd, dest=key, default=defaultValue, help=helpText)

        (self.options, self.args) = parser.parse_args()

        if self.options.configFile is not None:
            self.findConfigFile(configPaths, configEnvVar)
            self.options.config = self.loadJSON(self.options.configFile)

        initLogs(self.log, echo=getattr(self.options, 'echo', False), 
                           debug=getattr(self.options, 'debug', False), 
                           logpath=getattr(self.options, 'logpath', None), 
                           logname=getattr(self.options, 'logfile', None))

    def loadJSON(self, filename):
        """ Read, parse and return given config file
        """
        jsonConfig = {}

        if os.path.isfile(filename):
            try:
                log.debug('attempting to load json config file [%s]' % filename)
                jsonConfig = json.loads(' '.join(open(filename, 'r').readlines()))
            except:
                log.error('error during loading of config file [%s]' % filename, exc_info=True)

        return jsonConfig
