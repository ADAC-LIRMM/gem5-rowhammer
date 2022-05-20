#ifndef __MEMORY_CORRUPTION_HH__
#define __MEMORY_CORRUPTION_HH__

#include <unordered_map>

#include "sim/sim_object.hh"
#include "base/statistics.hh"

#include "mem/ramulator.hh"

#include "params/MemoryCorruption.hh"

#define ALL_MEM 1

class Ramulator;
class Mitigation;

class MemoryCorruption : public SimObject
{
private:

#if ALL_MEM
    std::unordered_map<unsigned int, unsigned int> _row_counters;
#else
    std::vector<unsigned int> _target_addrs;
    std::vector<unsigned int> _target_ACT_counter;
#endif
    unsigned long int _hammer_threshold;
    unsigned long int _refresh_count_down;
    bool _enable_corruption;
    std::vector<unsigned int> _layout_config;
    std::vector<double> _flip_polynomial;
    Ramulator* _ramulator;
    Mitigation* _mitigation;

    int getMapKey(const std::vector<int>& addr_vec,
                  int neighbor_rows[2],
                  int neighbor_keys[2]);

    unsigned int corrupt(unsigned int address,
                 unsigned int length, double flip_probability,
                 bool to1, unsigned int random_seed);
public:
    MemoryCorruption(const MemoryCorruptionParams &p);
    void init(Ramulator& ramulator);
    void onACT(Ramulator& ramulator, const std::vector<int>& addr_vec);
    void onREF(Ramulator& ramulator, const std::vector<int>& addr_vec);
    bool neighbor(const std::vector<int>& addr_vec, int offset,
                  std::vector<int>& neighbor_vec);
    void refresh_row(const std::vector<int>& addr_vec);
    void addr_to_vec(unsigned int addr, std::vector<int> addr_vec);
    unsigned long vec_to_addr(std::vector<int> addr_vec);
    unsigned int get_level_addr_bits(unsigned int level) const;
    unsigned int getBankLevel() const;
    unsigned int getRowLevel() const;
    unsigned int getColumnLevel() const;

    Stats::Value rh_threshold_stat;
    Stats::Scalar maxDisturbLevel;
    Stats::Scalar bitFlipsCount;

    void regStats() override;
};

#endif // __MEMORY_CORRUPTION_HH__
