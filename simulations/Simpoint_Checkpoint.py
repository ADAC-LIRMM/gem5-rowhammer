import numpy as np
import multiprocessing
import os
import re

#-----------------------------#

class bcolors:
    red 	= '\033[31;40m'
    green 	= '\033[32;40m'
    end 	= '\033[37;39m'

#--------------------------------SETUP----------------------

#Simpoint interval
interval	= "10000000"
warmup		= "10000000"	


#Paths
gem5_opt 			= "/auto/qhuppert/workspace/gem5/build/ARM/gem5.opt"
output_repository  	= "/auto/qhuppert/workspace/Simpoint_Spec/results_SE"
syscall 			= "/auto/qhuppert/workspace/gem5/configs/example/se.py"

# Benchmark to simulate
# Benchmark to simulate

spec_path 	= "/auto/qhuppert/workspace/CPU2006/"
test_in 	= "/data/test/input/"
test_out	= "/data/test/output/"

benchmarks 	=  []
#benchmarks  += ['401.bzip2']
#benchmarks  += ['403.gcc']
#benchmarks  += ['429.mcf']
benchmarks  += ['433.milc']
#benchmarks  += ['435.gromacs']
#benchmarks  += ['436.cactusADM']
benchmarks  += ['437.leslie3d']
#benchmarks  += ['456.hmmer']
#benchmarks  += ['458.sjeng']
#benchmarks  += ['462.libquantum']


bench_cmd =	{	'401.bzip2' : [spec_path + '401.bzip2/bzip2',
					'\"' + spec_path + '401.bzip2' + test_in + 'dryer.jpg 1\"'],	
				'403.gcc' : [spec_path + '403.gcc/gcc',
					'\"' + spec_path + '403.gcc' + test_in + 'cccp.in -o ' +
					spec_path + '403.gcc' + test_out + 'cccp.s \"'],
				'410.bwaves' : [spec_path + '410.bwaves/bwaves'],
				'416.gamess' : [spec_path + '416.gamess/gamess',
					'\"' + spec_path + '416.gamess' + test_in + 'exam29.config\"'],
				'429.mcf' : [spec_path + '429.mcf/mcf',
					'\"' + spec_path + '429.mcf' + test_in + 'inp.in\"'],
				'433.milc' : [spec_path + '433.milc/milc',
					'\"' + spec_path + '433.milc' + test_in + 'su3imp.in\"'],
				'434.zeusmp' : [spec_path + '434.zeusmp/zeusmp'],
				'435.gromacs' : [spec_path + '435.gromacs/gromacs',
					'\"-silent -deffnm ' + spec_path  + '435.gromacs' + test_in + 'gromacs.tpr -nice 0\"'],
				'436.cactusADM' : [spec_path + '436.cactusADM/cactusADM',
					'\"' + spec_path + '436.cactusADM' + test_in + 'benchADM.par\"'],
				'437.leslie3d' : [spec_path + '437.leslie3d/leslie3d',
					'\"' + spec_path + '437.leslie3d' + test_in + 'leslie3d.in\"'],
				'444.namd' : [spec_path + '444.namd/namd',
					'\" --input ' + spec_path + '444.namd/data/all/input/namd.input --iterations 10' + 
					'444.namd/data/test/output/namd.out\"'],
				'445.gobmk' : [spec_path + '445.gobmk/gobmk',
					'\"--quiet --mode gtp\"',
					'\"' + spec_path + '445.gobmk' + test_in + 'capture.tst\"'],
				'453.povray' : [spec_path + '453.povray/povray',
					'\"' + spec_path + '453.povray' + test_in + 'SPEC-benchmark-test.ini\"'],
				'454.calculix' : [spec_path + '454.calculix/calculix',
					'\"-i ' + spec_path + '454.calculix' + test_in + 'beampic\"'],
				'456.hmmer' : [spec_path + '456.hmmer/hmmer',
					'\"' + spec_path + '456.hmmer' + test_in + 'bombesin.hmm\"'],
				'458.sjeng' : [spec_path + '458.sjeng/sjeng',
					'\"' + spec_path + '458.sjeng' + test_in + 'test.txt\"'],
				'459.GemsFDTD' : [spec_path + '459.GemsFDTD/GemsFDTD'],
				'462.libquantum' : [spec_path + '462.libquantum/libquantum',
					'\" 33 5\"'],
				'464.h264ref' : [spec_path + '464.h264ref/h264ref',
					'\"-d ' + spec_path + '464.h264ref' + test_in + 'foreman_test_encoder_baseline.cfg\"'],
				'465.tonto' : [spec_path + '465.tonto/tonto'],
				'471.omnetpp' : [spec_path + '471.omnetpp/omnetpp',
					'\"' + spec_path + '471.omnetpp' + test_in + 'omnetpp.ini\"'],
				'473.astar' : [spec_path + '473.astar/astar',
					'\"' + spec_path + '473.astar' + test_in + 'lake.cfg\"'],
				'481.wrf' : [spec_path + '481.wrf/wrf']}

no_input = ['410.bwaves','434.zeusmp','459.GemsFDTD','465.tonto','481.wrf']
if_input = ['433.milc','437.leslie3d']
if_input_and_options = ['445.gobmk']

# --- Cortex to simulate --- #

# Core 
cpu 			    = "NonCachingSimpleCPU"   
clock 				= "1.391GHz"

# L1 Caches
dL1_size			= "32kB"
dL1_assoc			= "4"
iL1_size			= "32kB"
iL1_assoc			= "2"

# L2 Cache
L2_size				= "512kB"
L2_assoc			= "16"

# Main Memory
main_memory			= "SimpleMemory"

#-----------------------------#



# === Launch Simpoint Simulations ===

def simulation(arg_bench):
		bench = str(arg_bench)
		# check if the output folder's been created 
		os.system("mkdir -p " + output_repository +
					"/"+ bench + "/checkpoints")

		simpoint_file 	= output_repository +"/"+ bench + "/simpoint.file"
		simpoint_weight = output_repository +"/"+ bench + "/simpoint.weights"

		simpoint_opt = simpoint_file + "," + simpoint_weight + "," + interval + "," + warmup


 		cmd	= gem5_opt + " -d " + output_repository + "/"+ bench + "/checkpoints " + syscall \
		+ " --cpu-type=" + cpu \
		+ " --num-cpus=1" \
		+ " --cpu-clock=" + clock \
 		+ " --take-simpoint-checkpoint=" + simpoint_opt \
 		+ " --mem-type=" + main_memory

 		if bench in if_input:
			cmd = cmd +	" --cmd=" + bench_cmd[arg_bench][0] \
				      + " --input=" + bench_cmd[arg_bench][1]

		elif bench in no_input:
			cmd = cmd +	" --cmd=" + bench_cmd[arg_bench][0]

		elif bench in if_input_and_options:
			cmd = cmd +	" --cmd=" + bench_cmd[arg_bench][0] \
				      + " --options=" + bench_cmd[arg_bench][1] \
				      + " --input=" + bench_cmd[arg_bench][2] 

		else:
			cmd = cmd + " --cmd=" + bench_cmd[arg_bench][0] \
					  + " --options=" + bench_cmd[arg_bench][1]


		cmd_txt		= " >" + output_repository + "/" + bench + "/checkpoints/cmd.txt"
		cerr_txt	= " 2>" + output_repository + "/" + bench + "/checkpoints/cerr.txt"

		print(bcolors.red + "Checkpoints with " + bench + " and fast memory Beguins" + bcolors.end) 
		os.system(cmd + cmd_txt + cerr_txt)
		print("Checkpoints with " + bench + " and fast memory Done")
		

argList = []
for it_bench in benchmarks:
	argList.append(it_bench)


#Create a pool of number_processes workers	
print ("\n === Simulation begins === \n")

number_processes = 10
pool = multiprocessing.Pool(number_processes)
results = pool.map_async(simulation, argList)
pool.close()
pool.join()

print ("\n === END === \n")







