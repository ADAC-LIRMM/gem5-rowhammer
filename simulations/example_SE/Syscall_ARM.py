import os
import sys

from path_init import *


# Path initialization:
gem5 		= gem5_ARM_binary()
output 		= gem5_output("results/example_SE")
simulation 	= gem5_file("configs/example/se.py")


# Benchmark to simulate
benchmark 	= gem5_file("tests/test-progs/hello/bin/arm/linux/hello")


### --- Architecture to simulate --- ###

# Core
cpu 			= "HPI"
nbr_cpu			= "1"
clock 			= "1.391GHz"

# L1 Caches
dL1_size		= "32kB"
dL1_assoc		= "4"
iL1_size		= "32kB"
iL1_assoc		= "2"

# L2 Cache
L2_size			= "512kB"
L2_assoc		= "16"

# Main Memory
main_memory		= "Ramulator"

# If Ramulator is used we need to choose a config file
ramulator_cfg 	= gem5_file("ext/ramulator/Ramulator/configs/DDR4-config.cfg")


### --- Simulation --- ###

# To execute gem5 the usage is:
#      gem5.opt [gem5 options] script.py [script options]
#
cmd	= gem5 + " -d " + output + " " + simulation \
        + " --cmd=" + benchmark \
        + " --cpu-type=" + cpu \
        + " --num-cpus=" + nbr_cpu \
        + " --cpu-clock=" + clock \
        + " --caches" \
        + " --l1d_size=" + dL1_size \
        + " --l1i_size=" + iL1_size \
        + " --l1d_assoc=" + dL1_assoc \
        + " --l1i_assoc=" + iL1_assoc \
        + " --l2cache" \
        + " --l2_size=" + L2_size \
        + " --l2_assoc=" + L2_assoc \
        + " --mem-type=" + main_memory

if main_memory == "Ramulator":
        cmd += " --ramulator-config=" + ramulator_cfg

"""
cmd		+= " >" + output + "/cmd.txt"
cmd 	+= " 2>" + output + "/cerr.txt"
"""

os.system(cmd)

exit(-1)





