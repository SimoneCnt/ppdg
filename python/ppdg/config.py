#!/usr/bin/env python3

import os
import configparser
import ppdg

def cread(fname):
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


def cget():
    config = dict()
    config['WRKDIR']     = ppdg.WRKDIR
    config['RFSPP']      = ppdg.RFSPP
    config['CHARMM']     = ppdg.CHARMM
    config['FFPATH']     = ppdg.FFPATH
    config['ROSETTA']    = ppdg.ROSETTA
    config['ROSETTABIN'] = ppdg.ROSETTABIN
    return config

def cset(config):
    ppdg.WRKDIR     = config['WRKDIR']
    ppdg.RFSPP      = config['RFSPP']
    ppdg.CHARMM     = config['CHARMM']
    ppdg.FFPATH     = config['FFPATH']
    ppdg.ROSETTA    = config['ROSETTA']
    ppdg.ROSETTABIN = config['ROSETTABIN']
    return

def cprint():
    '''
        Print current settings.
    '''
    c = cget()
    for key, value in c.items():
        print("%-10s = %s" % (key, value))

