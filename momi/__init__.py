"""
momi (MOran Models for Inference) is a python package for computing the site frequency spectrum,
a summary statistic commonly used in population genetics, and using it to infer demographic history.

Please refer to examples/tutorial.ipynb for usage & introduction.
"""


from .parse_ms import simulate_ms, run_ms, to_ms_cmd, seg_sites_from_ms
from .demography import make_demography
from .compute_sfs import expected_sfs, expected_total_branch_len, expected_sfs_tensor_prod, expected_tmrca, expected_deme_tmrca
from .likelihood import SfsLikelihoodSurface, ConfidenceRegion
from .tensor import sfs_tensor_prod
from .data_structure import Configs, SegSites, Sfs, write_seg_sites, read_seg_sites, config, make_sfs, make_seg_sites_data
