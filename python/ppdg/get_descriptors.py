#!/usr/bin/env python3

import os, json
import hashlib
import joblib
import numpy as np
from multiprocessing import Pool
import ppdg
import logging
log = logging.getLogger(__name__)

def get_descriptors_average(wrkdir, protocol, desc_list=None, nmodels=None, median=False):
    """
        Return the average and standard error for the descriptors in 
        desc_list for the first nmodels.
        All descriptors have to be already computed by get_descriptors,
        otherwise an error is thrown.
    """
    if not desc_list:
        desc_list = ppdg.scoring.all_descriptors()
    descfile = os.path.join(wrkdir, 'descriptors.json')
    if not os.path.isfile(descfile):
        raise ValueError("Missing file descriptors.json in directory %s\nBe sure to have called get_descriptors before!" % (wrkdir))
    log.info("Reading descriptors from %s" % (descfile))
    with open(descfile, 'r') as fp:
        alldesc = json.load(fp)
    if protocol in alldesc:
        descriptors = alldesc[protocol]
    else:
        raise ValueError("Could not find protocol %s in %s\nBe sure to have called get_descriptors before!" % (protocol, wrkdir))
    scores = dict()
    for desc in desc_list:
        if nmodels:
            lst = list()
            for i in range(nmodels):
                lst.append(descriptors[desc][str(i)])
        else:
            lst = np.array([ v for k,v in descriptors[desc].items() ])
        if median:
            avg = np.median(lst)
        else:
            avg = np.mean(lst)
        std = np.std(lst)
        err = std/np.sqrt(len(lst))
        scores[desc] = [avg, std, err]
    return scores


def get_descriptors(base_wrkdir, protocol, template, sequence, nchains, desc_wanted, nmodels, ncores=1, force_calc=False):
    """
        Main function!
        Given:
            - The working directory to use
            - The protocol to build the atomistic model of the protein-protein complex
            - A PDB file to use as template for the modelling
            - The sequence of the whole protein-protein complex
            - A tuple indicating how many chains are in the receptor and in the ligand [ nchains = ( nchains_rec, nchains_lig) ]
            - Which descriptors do you want to compute
            and
            - How many models you want to make (to make nice averages)
        This function
            - Makes the models
            - Computes the descriptors
        recycling all possible info reading the descriptors.json file in base_wrkdir (if available).
    """
    if nmodels<1:
        raise ValueError('You need at least one model, you asked for %d' % (nmodels))

    # Check template file exists
    if not os.path.isfile(template):
        raise ValueError('Template file %s does not exist!' % (template))

    # Check nchains. A tuple. First is the number of chains in the receptor, 
    # second the number of chains in the ligand.
    if len(nchains)!=2:
        raise ValueError('Cannot understand nchains = %s. Use (nchains_receptor, nchains_ligand).' % (nchains))
    nchains_rec = nchains[0]
    nchains_lig = nchains[1]
    nchains_tot = len(sequence.split('/'))
    if nchains_rec + nchains_lig != nchains_tot:
        raise ValueError('You said the receptor has %d chains and the ligand %d, but the sequence has a total of %d chains.' 
                % (nchains_rec, nchains_lig, nchains_tot))

    # Read the descriptors from file
    alldesc = dict()
    desc = dict()
    descfile = os.path.join(base_wrkdir, 'descriptors.json')
    if os.path.isfile(descfile):
        log.info("Reading descriptors from %s" % (descfile))
        with open(descfile, 'r') as fp:
            alldesc = json.load(fp)
        if protocol in alldesc:
            desc = alldesc[protocol]
    desc_flat = ppdg.tools.switch_desc_format(desc)

    # Make a list of what we need to compute
    to_compute = list()
    for nmodel in range(nmodels):
        if str(nmodel) in desc_flat.keys():
            desc_have = desc_flat[str(nmodel)]
        else:
            desc_have = dict()
        to_compute.append([base_wrkdir, protocol, nmodel, template, sequence, nchains, desc_have, desc_wanted, force_calc])

    # Compute everything, if possibly in parallel
    if ncores<2:
        results = list()
        for compute in to_compute:
            results.append(_get_descriptors_core(*compute))
    else:
        with Pool(ncores) as p:
            results = p.starmap(_get_descriptors_core, to_compute)
    for nmodel, scores in results:
        desc_flat[str(nmodel)] = scores
        
    # Write descriptors to file
    desc2 = ppdg.tools.switch_desc_format(desc_flat)
    if desc2!=desc:
        alldesc[protocol] = desc2
        log.info("Writing descriptors to %s" % (descfile))
        with open(descfile, 'w') as fp:
            json.dump(alldesc, fp, indent=4, sort_keys=True)
    return alldesc


def _get_descriptors_core(base_wrkdir, protocol, nmodel, template, sequence, nchains, desc_have, desc_wanted, force_calc=False):
    """
        Core function to make one model and get the descriptors.
        Do not call this directly, but use get_descriptors.
    """
    desc_set = set()
    for desc in desc_wanted:
        if desc not in desc_have.keys() or force_calc:
            desc_set.add(desc)
    if len(desc_set)==0:
        return (nmodel, desc_have)
    wrkdir = os.path.join(base_wrkdir, protocol+'_%d' % (nmodel))
    scores = ppdg.makemodel.make_model(wrkdir, protocol, template, sequence)
    nchfile = os.path.join(wrkdir, 'nchains.dat')
    if not os.path.isfile(nchfile):
        with open(nchfile,'w') as fp:
            fp.write('%d %d' % nchains)
    if protocol in ['modeller_veryfast']:
        nsteps = 10
    else:
        nsteps = 100
    ppdg.makemodel.charmify(os.path.join(wrkdir, 'model.pdb'), nsteps=nsteps)
    ppdg.makemodel.split_complex(wrkdir, nchains)
    scores2 = ppdg.scoring.evaluate(wrkdir, desc_wanted, desc_have, force_calc)
    scores.update(scores2)
    return (nmodel, scores)


def clean(wrkdir=None):
    # List of files generated during model construction and evaluation of the descriptors.
    # Commented file names should be kept, uncommented ones can be deleted without problems.
    # wrkdir is the same as ppdg.WRKDIR

    if not wrkdir:
        wrkdir = ppdg.WRKDIR

    log.info('Cleaning directory %s' % (wrkdir))

    filelist = [

        ## Modeller
        'complex_seq.D00000000', 'complex_seq.ini', 'complex_seq.rsr', 'complex_seq.sch',
        'complex_seq.V99990000', 'family.mat', 'modeller.out',
        #'complex_seq.B99990000.pdb', 'model.pdb', 'template.pdb', 'sequence.seq', 'sequence.seq.ali',

        ## Charmify
        'add_disulfide.str', 'buildgen.inp',
        # 'chain_a.pdb', 'chain_b.pdb', 'chain_c.pdb',
        'disu.str', 'model-chm.err', 'model-chm.out',
        #'model-chm.cor', 'model-chm.pdb', 'model-chm.psf',
        #'complex-chm.cor', 'complex-chm.pdb', 'complex-chm.psf',

        # Split complex
        'extract.inp', 'ligand-chm.err', 'ligand-chm.out', 'receptor-chm.err', 'receptor-chm.out',
        #'complex.pdb', 'complexAB.pdb', 'ligand.pdb', 'ligandB.pdb', 'receptor.pdb', 'receptorA.pdb',
        #'ligand-chm.psf', 'ligand-chm.cor', 'ligand-chm.pdb', 'receptor-chm.cor', 'receptor-chm.pdb', 'receptor-chm.psf',

        'ligand-chm-facts.pdb', 'ligand-chm-gbsw.pdb', 'ligand-chm-gbmv.pdb',
        'receptor-chm-facts.pdb', 'receptor-chm-gbsw.pdb', 'receptor-chm-gbmv.pdb',
        'complex-chm-facts.pdb', 'complex-chm-gbsw.pdb', 'complex-chm-gbmv.pdb',
    ]

    wrkdir = os.path.abspath(wrkdir)
    sysdir = [os.path.join(wrkdir, o) for o in os.listdir(wrkdir) if os.path.isdir(os.path.join(wrkdir, o))]

    for sysname in sysdir:
        modelsdirs = [os.path.join(sysname, o) for o in os.listdir(sysname) if os.path.isdir(os.path.join(sysname, o))]
        for model in modelsdirs:
            for f in filelist:
                torm = os.path.join(model, f)
                if os.path.isfile(torm):
                    #print("Removing", torm)
                    os.remove(torm)

def eval_pkl(pkl, cpxseq, nchains, template, name=None, wrkdir=None, nmodels=12, ncores=11):
    """
        Evaluate the content of a pkl file given the complex sequence, the 
        number of chains in ligand and receptor, and a template.
        name is the name of the complex. If not given, a name is generate as the
        hash of the sequence. nmodels is how many models to generate, and ncores
        the number of cores to use for parallel execution. Leave at least one free
        core, otherwise the code my deadlock.
        The pkl should contain in order: the protocol to use, the list of needed
        descriptors, a scaler (not implemented!) and the regression model to use.
    """
    unpk = joblib.load(pkl)
    if len(unpk)==4:
        protocol, desclist, scaler, reg = unpk
    elif len(unpk)==6:
        protocol, desclist, scaler, reg, x, y = unpk
        yc = reg.predict(scaler.transform(x))
        rmsd = np.sqrt(np.average(np.square(y-yc)))
        if rmsd>0.001:
            raise ValueError("Checking the pkl failed! RMSE for test set is %lf " % (rmsd))
    else:
        raise ValueError("Error unpacking the pkl file. Should have 4 or 6 elements, but found %d" % (len(unpk)))
    if not name:
        name = hashlib.md5(cpxseq.encode()).hexdigest()
    if not wrkdir:
        wrkdir = os.path.join(ppdg.WRKDIR, name)
    ppdg.get_descriptors(wrkdir, protocol, template, cpxseq, nchains, desclist, nmodels, ncores=ncores)
    scores = ppdg.get_descriptors_average(wrkdir, protocol, desc_list=desclist, nmodels=nmodels, median=True)
    desc = np.array([ scores[d][0] for d in desclist ]).reshape(1, -1)
    if scaler:
        desc = scaler.transform(desc)
    dg = reg.predict(desc)[0]
    return dg

