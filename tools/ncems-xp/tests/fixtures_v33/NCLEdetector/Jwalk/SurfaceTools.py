"""SYNTHETIC TEST BACKEND ONLY: declares fixture sites accessible."""
from ._synthetic import trace


def check_solvent_accessibility_freesasa_both(pdb, first, second, pair_file, aa, ncpus):
    trace("check_solvent_accessibility_freesasa_both")
    return first, second


def update_crosslink_pairs(pairs, first, second, removed_first, removed_second):
    trace("update_crosslink_pairs")
    return pairs
