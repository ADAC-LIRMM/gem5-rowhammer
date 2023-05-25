#ifndef __MEMORY_CORRUPTION_HH__
#define __MEMORY_CORRUPTION_HH__

#include <unordered_map>

#include "sim/sim_object.hh"
#include "base/statistics.hh"

#include "mem/ramulator.hh"

#include "params/MemoryCorruption.hh"

class Ramulator;

namespace gem5
{
namespace memory
{
class Mitigation;

class MemoryCorruption : public SimObject
{
private:

    std::unordered_map<unsigned int, unsigned int> _row_counters;

    unsigned long int _hammer_threshold;
    unsigned long int _refresh_count_down;
    bool _enable_corruption;
    unsigned int _rand_seed;
    std::vector<unsigned int> _layout_config;
    std::vector<double> _flip_polynomial;
    Ramulator* _ramulator;
    Mitigation* _mitigation;

    int getMapKey(const std::vector<int>& addr_vec,
                  int neighbor_rows[2],
                  int neighbor_keys[2]);

    unsigned int corrupt(std::vector<int>& addr_vec,
                         double flip_probability, bool to1);
public:
    typedef MemoryCorruptionParams Params;
    MemoryCorruption(const Params &p);
    void init(Ramulator& ramulator);
    void onACT(const std::vector<int>& addr_vec);
    void onREF(const std::vector<int>& addr_vec);
    bool neighbor(const std::vector<int>& addr_vec, int offset,
                  std::vector<int>& neighbor_vec);
    void refresh_row(const std::vector<int>& addr_vec);
    void addr_to_vec(unsigned int addr, std::vector<int> addr_vec);
    unsigned long vec_to_addr(std::vector<int> addr_vec);
    unsigned int get_level_addr_bits(unsigned int level) const;
    unsigned int getBankLevel() const;
    unsigned int getRowLevel() const;
    unsigned int getColumnLevel() const;

    statistics::Value rh_threshold_stat;
    statistics::Scalar maxDisturbLevel;
    statistics::Scalar bitFlipsCount;

    void regStats() override;
};
}
}

#endif // __MEMORY_CORRUPTION_HH__
