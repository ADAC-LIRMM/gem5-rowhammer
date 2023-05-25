#ifndef __PARA_HH__
#define __PARA_HH__

#include <random>
#include "mem_side_effects/mitigation.hh"
#include "params/PARA.hh"

namespace gem5
{

namespace memory
{

class PARA : public Mitigation {
private:
    float _p;

    std::random_device _rand_device; // TODO inline this attrib used only once
                                // to init the random engine in the constructor
    std::default_random_engine _rand_engine;
    std::uniform_real_distribution<float> _rand_distr;

public:
    typedef PARAParams Params;
    PARA(const Params &params);

    void onACT(MemoryCorruption& mem_corrupt,
               const std::vector<int>& addr_vec);
};

}

}

#endif // __PARA_HH__
