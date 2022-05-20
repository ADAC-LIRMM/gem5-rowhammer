from m5.params import *
from m5.SimObject import SimObject

class Mitigation(SimObject):
    type = 'Mitigation'
    abstract = True
    cxx_header = "mem_side_effects/mitigation.hh"
    cxx_class = "Mitigation"
