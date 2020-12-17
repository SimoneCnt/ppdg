#!/usr/bin/env python3

import os
import ppdg
import logging
log = logging.getLogger(__name__)

def charmify(fname, nsteps=100):

    basepath = os.getcwd()
    wrkdir, name = os.path.split(fname)

    basename = ''.join(name.split('.')[0:-1]) + '-chm'

    if os.path.isfile(os.path.join(wrkdir, basename+'.psf')):
        #log.info('Charmm outputs already present, recycling data!')
        return
    else:
        log.info("Charmify-ing pdb %s" % (fname))

    os.chdir(wrkdir)

    pdb = ppdg.Pdb(name)
    pdb.fix4charmm()
    pdb.chain2segid()
    pdb.set_occupancy(1.0)
    pdb.set_beta(1.0)
    pdb.remove_hydrogens()

    chains = pdb.split_by_chain()
    nchains = len(chains)
    cmd = os.path.join(ppdg.CHARMM, 'charmm')
    cmd += ' nc=%d ' % nchains
    i=1
    for ch, pdb in chains.items():
        pdb.write("chain_%s.pdb" % (ch.lower()))
        cmd += 'c%d=%s ' % (i, ch)
        i += 1
    cmd += 'name=chain_ out=%s ' % (basename)
    cmd += 'nsteps=%d ' % (nsteps)
    cmd += 'ffpath=%s ' % (ppdg.FFPATH)
    cmd += '-i buildgen.inp >%s 2>&1' % (basename+'.out')

    ppdg.link_data('buildgen.inp')
    ppdg.link_data('disu.str')

    ret = ppdg.tools.execute(cmd)
    os.chdir(basepath)
    if ret!=0:
        raise ValueError("Charmm failed.")


