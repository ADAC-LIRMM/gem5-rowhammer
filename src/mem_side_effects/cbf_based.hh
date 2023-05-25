#ifndef __CBF_BASED_HH__
#define __CBF_BASED_HH__

#include "mem_side_effects/mitigation.hh"
#include "params/CBFBased.hh"

#include <random>
#include <unordered_map>

namespace gem5
{

namespace memory
{

class CBFBased : public Mitigation {
private:

    struct MitigationUnit {
        std::vector<unsigned int> counters;
        std::unordered_map<unsigned int, unsigned int> row_specific_threshold;

        void init(unsigned int nb_counters);
        unsigned int row_threshold(unsigned int row,
                                   unsigned int default_threshold) const;
    };
    unsigned int _level;
    unsigned int _nb_counters;
    unsigned int _counter_limit;
    unsigned int _threshold;
    unsigned int _nb_hashes;
    std::vector<unsigned int> _multipliers;
    unsigned int _threshold_incr;
    std::vector<CBFBased::MitigationUnit> _units;

    MitigationUnit& _getUnit(MemoryCorruption& mem_corrupt,
                             const std::vector<int>& addr_vec);

public:
    typedef CBFBasedParams Params;
    CBFBased(const Params &params);

    virtual void init(MemoryCorruption& mem_corrupt);
    void onACT(MemoryCorruption& mem_corrupt,
               const std::vector<int>& addr_vec);
    void onREFW(MemoryCorruption& mem_corrupt,
               const std::vector<int>& addr_vec);

    statistics::Scalar maxCount;

    void regStats() override;
};

}

}

#endif // __CBF_BASED_HH__
