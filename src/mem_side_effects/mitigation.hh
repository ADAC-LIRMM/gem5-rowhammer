#ifndef __MITIGATION_HH__
#define __MITIGATION_HH__

#include "mem_side_effects/memory_corruption.hh"
#include "sim/sim_object.hh"
#include "base/statistics.hh"

class Mitigation : public SimObject
{
protected:
    void refresh_row(MemoryCorruption& mem_corrupt,
                     const std::vector<int>& addr_vec);
    bool neighbor_row(MemoryCorruption& mem_corrupt,
                      const std::vector<int>& addr_vec, int offset,
                      std::vector<int>& neighbor_vec);
    unsigned int addr_vec_to_addr(MemoryCorruption& mem_corrupt,
                                  const std::vector<int>& addr_vec);
    void addr_to_addr_vec(MemoryCorruption& mem_corrupt, unsigned int addr,
                          std::vector<int>& addr_vec);
    Mitigation(const Params &params);
public:
    virtual void init(MemoryCorruption& mem_corrupt) { }

    virtual void onACT(MemoryCorruption& mem_corrupt,
                       const std::vector<int>& addr_vec) { }
    virtual void onREF(MemoryCorruption& mem_corrupt,
                       const std::vector<int>& addr_vec) { }

    Stats::Scalar additionalRefreshesCount;
    virtual void regStats() override;
};

#endif // __MITIGATION_HH__
