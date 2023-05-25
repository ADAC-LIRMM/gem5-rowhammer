import os

#Simpoit interval
simpoint_interval 	= "10000000"
maxK 				= "30"

output_repository  	= "/auto/qhuppert/workspace/Simpoint_Spec/results_SE"

benchmarks 	=  []
benchmarks  += ['401.bzip2']
benchmarks  += ['403.gcc']
benchmarks  += ['429.mcf']
benchmarks  += ['433.milc']
benchmarks  += ['435.gromacs']
benchmarks  += ['436.cactusADM']
benchmarks  += ['437.leslie3d']
benchmarks  += ['456.hmmer']
benchmarks  += ['458.sjeng']
benchmarks  += ['462.libquantum']


print ("\n === Simpoint creating === \n")

for it_bench in benchmarks:

	cmd = "/auto/qhuppert/workspace/simpoint/bin/simpoint" \
		+ " -loadFVFile " + output_repository + "/" + it_bench + "/slices/simpoint.bb.gz" \
		+ " -maxK " + maxK \
		+ " -saveSimpoints " + output_repository + "/" + it_bench + "/simpoint.file" \
		+ " -saveSimpointWeights " + output_repository + "/" + it_bench + "/simpoint.weights" \
		+ " -inputVectorsGzipped"
	
	os.system(cmd)

print("\n === Simpoint Done ===")

exit(-1)