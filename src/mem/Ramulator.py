# Authors: Minesh Patel

from m5.params import *
from m5.objects.AbstractMemory import AbstractMemory

# A wrapper for Ramulator
class Ramulator(AbstractMemory):
    type = 'Ramulator'
    cxx_header = "mem/ramulator.hh"
    cxx_class = "Ramulator"

    # A single port for now
    port = SlavePort("Slave port")

    num_cpus = Param.Unsigned(1, "Number of CPUs")

    # deviceConfigFile = Param.String("ini/DDR3_micron_32M_8B_x8_sg15.ini",
    #                                 "Device configuration file")
    # systemConfigFile = Param.String("system.ini.example",
    #                                 "Memory organisation configuration file")
    ramulatorConfigFile = Param.String("system.ini.example",
        "Memory organisation configuration file")

    filePath = Param.String("ext/ramulator/Ramulator/",
                            "Directory to prepend to file names")
    traceFile = Param.String("", "Output file for trace generation")
    enableDebug = Param.Bool(False, "Enable Ramulator debug output")

    memoryCorruption = Param.MemoryCorruption(NULL,
                            "Handles memory ACT and REF side-effects")
