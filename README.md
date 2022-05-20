This is the gem5 simulator.

The main website can be found at http://www.gem5.org

A good starting point is http://www.gem5.org/about, and for
more information about building the simulator and getting started
please see http://www.gem5.org/documentation and
http://www.gem5.org/documentation/learning_gem5/introduction.

To build gem5, you will need the following software: g++ or clang,
Python (gem5 links in the Python interpreter), SCons, SWIG, zlib, m4,
and lastly protobuf if you want trace capture and playback
support. Please see http://www.gem5.org/documentation/general_docs/building
for more details concerning the minimum versions of the aforementioned tools.

Once you have all dependencies resolved, type 'scons
build/<ARCH>/gem5.opt' where ARCH is one of ARM, NULL, MIPS, POWER, SPARC,
or X86. This will build an optimized version of the gem5 binary (gem5.opt)
for the the specified architecture. See
http://www.gem5.org/documentation/general_docs/building for more details and
options.

The basic source release includes these subdirectories:
   - configs: example simulation configuration scripts
   - ext: less-common external packages needed to build gem5
   - src: source code of the gem5 simulator
   - system: source for some optional system software for simulated systems
   - tests: regression tests
   - util: useful utility programs and files

To run full-system simulations, you will need compiled system firmware
(console and PALcode for Alpha), kernel binaries and one or more disk
images.

If you have questions, please send mail to gem5-users@gem5.org

Enjoy using gem5 and please share your modifications and extensions.

# Use the Rowhammer simulation

As of yet, the module can only be used with Ramulator and DDR4

## using example files `fs.py` or `se.py`

Use the following arguments to configure the memory corruption module:

- `-rowhammer-enable`: 
   Necessary to enable the module.

- `--rowhammer-threshold=50000`:
   The corruption threshold is the number of ACT needed on the neighbors of a victim row to corrupt it. If the threshold is e.g. 50000, then the sum of the activations in this row's neighbors must be at least 50000 for a corruption to happen. Default value is 50000.

- `--rowhammer-enable-corruption`:
   If set, the attack will affect the bits in the memory.
   Otherwise, there will only be a message in the standard output.

- `--dram-layout=path/to/file.csv`:
   Used to change the organization of rows in the DRAM banks.
   The file must be a csv file where the nth value is the placement of the nth logical row.
   If the file contains `4,5,0,2,1,3`, then the logical row 0 will be placed at position 4, the row 1 position 5, etc. The logical row 0 have the rows 1 and 5 as its neighbors.
   The remaining rows are placed at their original positions (row 6 at position 6, row 7 at position 7, etc.)

- `--rowhammer-bit-flip-polynomial=0,0,3e-6,-2e-9`:
   A polynomial law that defines the theoretical percentage of bits that are flipped after every ACT on a neighbor of a victim once the threshold is reached.
   Default value is the constant 1.
   E.g., if the polynomial is `0,0,3e-6,-2e-9` (-2e-9x^3 + 3e-6x^2), then after 200 ACTs passed the threshold, each bit has around 10.5% chance of being flipped. After 1000 ACTs passed the threshold, all bits are flipped.


