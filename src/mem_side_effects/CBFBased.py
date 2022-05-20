from m5.params import *
from .Mitigation import Mitigation

class CBFBased(Mitigation):
    type = 'CBFBased'
    cxx_header = "mem_side_effects/cbf_based.hh"
    cxx_class = "CBFBased"

    nb_counters = Param.Unsigned(1024, "number of counters")
    counter_limit = Param.Unsigned(1<<16, "limit value for one counter")
    threshold = Param.Unsigned(1<<14, "Rowhammer detection threshold")
    nb_hashes = Param.Unsigned(3, "number of counters associated to a row")
    multipliers = VectorParam.Unsigned([], "multipliers for each counter"+
            " increment for all rows")
    threshold_incr = Param.Unsigned(0, "increment the threshold for detected"
            " aggressors after refreshing its neighbors, instead of deleting"
            " the threshold from the counters")
    level = Param.Unsigned(0, "implementation level : 0 for Bank,"
            " 1 for Bank Group, 2 for Rank, 3 for Channel."
            " Default is Bank level")
