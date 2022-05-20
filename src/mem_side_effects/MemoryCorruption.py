from m5.params import *
from m5.SimObject import SimObject

class MemoryCorruption(SimObject):
    type = 'MemoryCorruption'
    cxx_header = "mem_side_effects/memory_corruption.hh"
    cxx_class = "MemoryCorruption"

    target_addrs = VectorParam.Unsigned([],"rowhammer target addresses")
    hammer_threshold = Param.Unsigned(50000, "rowhammer flip threshold")
    enable_corruption = Param.Bool(True, "enable memory corruption")
    layout_config = VectorParam.Unsigned([], "DRAM layout array")
    flip_polynomial = VectorParam.Float([],
        "Rowhammer bit-flip probability polynomial")
    mitigation = Param.Mitigation(NULL, "Mitigation technique")
