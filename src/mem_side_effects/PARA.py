from m5.params import *
from .Mitigation import Mitigation

class PARA(Mitigation):
    type = 'PARA'
    cxx_header = "mem_side_effects/para.hh"
    cxx_class = "PARA"

    probability = Param.Float(0.001,"neighbor refresh probability")
