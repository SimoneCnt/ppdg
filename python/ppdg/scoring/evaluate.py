#!/usr/bin/env python3

import logging
log = logging.getLogger(__name__)

from . import molecular
from . import statistical_potentials

def all_descriptors():
    desc  = list()
    # Molecular
    desc += ['HB_BH', 'HB_WN', 'HB_KS']
    desc += ['BSA', 'BSA_C', 'BSA_A', 'BSA_P', 'NIS_P', 'NIS_C', 'NIS_A', 'NRES']
    desc += ['sticky_tot', 'sticky_avg']
    desc += ['IC_TOT', 'IC_AA', 'IC_PP', 'IC_CC', 'IC_AP', 'IC_CP', 'IC_AC']
    # Statistical Potentials
    desc += ['RF_HA_SRS', 'RF_CB_SRS_OD']
    return desc

def evaluate(wrkdir, desc_wanted, scores=dict(), force_calc=False):

    desc_set = set()
    for desc in desc_wanted:
        if desc not in scores.keys() or force_calc:
            desc_set.add(desc)
    #print('Wanted : ', desc_wanted)
    #print('Have   : ', scores.keys())
    #print('Calc   : ', desc_set)

    if len(desc_set)>0:
        log.info('Computing new descriptors in %s' % (wrkdir))

    # Molecular descriptors
    if len(desc_set & set(['HB_BH', 'HB_WN', 'HB_KS']))>0:
        scores.update(molecular.hydrogenbond_difference(wrkdir))
    if len(desc_set & set(['BSA', 'BSA_C', 'BSA_A', 'BSA_P', 'NIS_P', 'NIS_C', 'NIS_A', 'NRES']))>0:
        scores.update(molecular.sasa_all(wrkdir))
    if len(desc_set & set(['sticky_tot', 'sticky_avg']))>0:
        scores.update(molecular.stickiness(wrkdir))
    if len(desc_set & set(['IC_TOT', 'IC_AA', 'IC_PP', 'IC_CC', 'IC_AP', 'IC_CP', 'IC_AC']))>0:
        scores.update(molecular.intermolecular_contacts(wrkdir))

    # Statistical Potentials
    if 'RF_HA_SRS' in desc_set:
        scores.update(statistical_potentials.rf_ha_srs(wrkdir))
    if 'RF_CB_SRS_OD' in desc_set:
        scores.update(statistical_potentials.rf_cb_srs_od(wrkdir))

    # Check all descriptors have been calculated
    calculated = set(scores.keys())
    diff = desc_set - calculated
    if len(diff)>0:
        raise ValueError('Unknown descriptors %s. Available descriptors are: %s' % (str(diff), str(all_descriptors())))

    # Return
    return scores

