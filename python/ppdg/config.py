#!/usr/bin/env python3

import os
import configparser
import ppdg

def readconfig(fname):
    '''
        Set some needed variables.
    '''
    defaults = dict(
            WRKDIR      = os.path.join(os.getcwd(), 'models'),
            RFSPP       = "",
            CHARMM      = "",
            FFPATH      = "",
            ROSETTA     = "",
            ROSETTABIN  = ""
        )
    config = configparser.ConfigParser(defaults)
    config.read(fname)
    ppdg.WRKDIR = config.get('ppdg', 'WRKDIR')
    ppdg.RFSPP  = config.get('ppdg', 'RFSPP')
    ppdg.CHARMM = config.get('ppdg', 'CHARMM')
    ppdg.FFPATH = config.get('ppdg', 'FFPATH')
    ppdg.ROSETTA = config.get('ppdg', 'ROSETTA')
    ppdg.ROSETTABIN = config.get('ppdg', 'ROSETTABIN')

def printconfig():
    '''
        Print current settings.
    '''
    for key, value in ppdg.__dict__.items():
        if not (key.startswith('__') or key.startswith('_')) and key==key.upper():
            print("%-10s = %s" % (key, value))

