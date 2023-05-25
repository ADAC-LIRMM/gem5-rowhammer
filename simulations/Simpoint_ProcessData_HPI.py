import numpy as np
import multiprocessing
import os
import re


#--------------------------------SETUP---------------------- 

#Paths
gem5_opt            = "/auto/qhuppert/workspace/gem5/build/ARM/gem5.opt"
output_repository   = "/auto/qhuppert/workspace/CASES/results/HPI_reference"
syscall             = "/auto/qhuppert/workspace/gem5/configs/example/se.py"

experiment = "HPI"

# Benchmark to simulate

spec_path   = "/home/qhuppert/workspace/CPU2006/"
test_in     = "/data/test/input/"
test_out    = "/data/test/output/"

benchmarks  =  []
benchmarks  += ['401.bzip2']
benchmarks  += ['403.gcc']
benchmarks  += ['429.mcf']
#benchmarks  += ['433.milc']
benchmarks  += ['435.gromacs']
benchmarks  += ['436.cactusADM']
#benchmarks  += ['437.leslie3d']
benchmarks  += ['456.hmmer']
#benchmarks  += ['458.sjeng']
benchmarks  += ['462.libquantum']




#----------------------------------------------------------


simpoint        = 0
bench_check     = []

data    = []
i       = 0

num_instructions    = 10000000
num_cycles          = 0

for it_bench in benchmarks:

    path_to_file = output_repository + "/" + it_bench + "/simpoint.weights"
    file = open(path_to_file,'r')

    data.append([it_bench, 0.0, 0.0, 0.0, 0.0, 0.0])
    
    for line in file:

        re_line = re.search(r'^(\d+).(\d+) (\d+)', line)  
        if re_line:
            simpoint    = int(re_line.group(3)) + 1
            weight      = float(re_line.group(1) + "." + re_line.group(2))

            path_to_simpoint = output_repository + "/" + it_bench + "/" + experiment + "/" + str(simpoint) + "/stats.txt"
            simpoint_file = open(path_to_simpoint,'r')

            warm_up = 0

            for simpoint_line in simpoint_file:

                re_line = re.search(r'^---------- End Simulation Statistics   ----------', simpoint_line)
                if re_line:
                    warm_up = 1

                re_line = re.search(r'^system.switch_cpus.numCycles\s+(\d+)', simpoint_line) 
                if re_line and warm_up:                 
                    data[i][1] += weight * float(re_line.group(1))

                re_line = re.search(r'^system.cpu.dcache.overall_accesses::total\s+(\d+)', simpoint_line) 
                if re_line and warm_up:                   
                    data[i][2] += weight * float(re_line.group(1)) / num_instructions

                re_line = re.search(r'^system.cpu.dcache.overall_misses::total\s+(\d+)', simpoint_line) 
                if re_line and warm_up:                   
                    data[i][3] += weight * float(re_line.group(1)) / num_instructions

                re_line = re.search(r'^system.l2.overall_accesses::total\s+(\d+)', simpoint_line) 
                if re_line and warm_up:                   
                    data[i][4] += weight * float(re_line.group(1)) / num_instructions

                re_line = re.search(r'^system.l2.overall_misses::total\s+(\d+)', simpoint_line) 
                if re_line and warm_up:                   
                    data[i][5] += weight * float(re_line.group(1)) / num_instructions

    data[i][1] = float(num_instructions)/data[i][1]  # IPC
    i += 1

print "benchmarks,IPC,L1_acc/inst,L1_miss/inst,L2_acc/inst,L2_miss/inst"
for i in range(0,len(data)):
    print(str(data[i][0]) + "," + str(data[i][1]) +
        "," + str(data[i][2]) + "," + str(data[i][3]) +
        "," + str(data[i][4]) + "," + str(data[i][5]))



exit(-1)