#include "mem_side_effects/cbf_based.hh"

#include <cmath>
#include <stdexcept>

#include "debug/MemCorruptMitigation.hh"

uint64_t hash(uint64_t value)
{
    uint64_t x = value + 1;
    x = (x ^ (x >> 30)) * 0xbf58476d1ce4e5b9;
    x = (x ^ (x >> 27)) * 0x94d049bb133111eb;
    return (x ^ (x >> 31));
}


CBFBased::CBFBased(const CBFBasedParams& params) :
    Mitigation(params),
    _level(params.level),
    _nb_counters(params.nb_counters),
    _counter_limit(params.counter_limit),
    _threshold(params.threshold),
    _nb_hashes(params.nb_hashes),
    _multipliers(params.nb_hashes),
    _threshold_incr(params.threshold_incr),
    maxCount(0)
{
    if (params.multipliers.size() > this->_nb_hashes) {
        throw std::invalid_argument("cannot have more multipliers"
                                    " than the number of hashes");
    }
    if (params.level > 2) {
        throw std::invalid_argument("level must be 0 (bank), 1 (bank group),"
                                    " 2 (rank) or 3 (channel)");
    }
    int i;
    for (i = 0; i < params.multipliers.size(); i++)
    {
        this->_multipliers[i] = params.multipliers[i];
    }
    for (; i< this->_multipliers.size(); i++)
    {
        this->_multipliers[i] = 1;
    }
}

void CBFBased::init(MemoryCorruption& mem_corrupt)
{
    uint32_t nb_sets = 1;
    const uint32_t bankLevel = mem_corrupt.getBankLevel();
    for(int i=0; i<= bankLevel - this->_level; i++) {
        nb_sets <<= mem_corrupt.get_level_addr_bits(i);
    }
    this->_units.resize(nb_sets);
    for (int i=0; i < nb_sets; i++)
    {
        //this->_units[i].init(this->_nb_counters);
        this->_units[i].counters.resize(this->_nb_counters);
        this->_units[i].row_specific_threshold.clear();
    }
}

void CBFBased::MitigationUnit::init(uint32_t nb_counters)
{
    this->counters.resize(nb_counters);
    this->row_specific_threshold.clear();
}

uint32_t CBFBased::MitigationUnit::row_threshold(uint32_t row,
                                        uint32_t default_threshold) const
{
    if (this->row_specific_threshold.count(row) > 0)
        return this->row_specific_threshold.at(row);
    else
        return default_threshold;
}

CBFBased::MitigationUnit& CBFBased::_getUnit(MemoryCorruption& mem_corrupt,
                                             const std::vector<int>& addr_vec)
{
    const uint32_t level = mem_corrupt.getBankLevel() - this->_level;
    int unit_idx = 0;
    for(int i=0; i <= level; i++) {
        unit_idx = (unit_idx << mem_corrupt.get_level_addr_bits(i)) + addr_vec[i];
    }
    return this->_units[unit_idx];
}

void CBFBased::onACT(MemoryCorruption& mem_corrupt,
                     const std::vector<int>& addr_vec)
{
    int counter_indices[this->_nb_hashes];
    const uint32_t bk_lvl = mem_corrupt.getBankLevel();
    const uint32_t row_lvl = mem_corrupt.getRowLevel();
    uint32_t row = addr_vec[row_lvl];
    MitigationUnit& unit = this->_getUnit(mem_corrupt, addr_vec);

    for(int i=0; i < this->_level; i++) {
        row += addr_vec[bk_lvl-i]<<mem_corrupt.get_level_addr_bits(bk_lvl+1-i);
    }
    const uint32_t t = unit.row_threshold(row, this->_threshold);

    uint64_t h = row;
    bool innocent = false;
    for (int i=0; i < this->_nb_hashes; i++) {
        uint32_t idx;
        int j;
        do {
            h = hash(h);
            idx = h % this->_nb_counters;
            for (j = 0; j < i; j++) {
                if (counter_indices[j] == idx)
                {
                    break;
                }
            }
        } while (j < i);
        counter_indices[i] = idx;
        const uint32_t mul = this->_multipliers[i];
        unit.counters[idx] += mul;
        const uint32_t count = unit.counters[idx] / mul;
        if (count > this->maxCount.value())
            this->maxCount = count;
        if (!innocent && count < t)
            innocent = true;
    }
    if (!innocent)
    {
        // refresh neighbor rows
        std::vector<int> neighbor_vec(addr_vec.size());
        if (this->neighbor_row(mem_corrupt, addr_vec, -1, neighbor_vec))
            this->refresh_row(mem_corrupt, neighbor_vec);
        if (this->neighbor_row(mem_corrupt, addr_vec, +1, neighbor_vec))
            this->refresh_row(mem_corrupt, neighbor_vec);
        // change the row-specific threshold...
        if (this->_threshold_incr > 0)
            unit.row_specific_threshold[row] = t + this->_threshold_incr;
        // ... or substract the threshold from the counters
        else
        {
            for (int i = 0; i < this->_nb_hashes; i++)
            {
                const uint32_t mul = this->_multipliers[i];
                unit.counters[counter_indices[i]] -= t * mul;
            }
        }
    }
}
void CBFBased::onREF(MemoryCorruption& mem_corrupt,
                     const std::vector<int>& addr_vec)
{
    for(int i=0; i< this->_units.size(); i++) {
        MitigationUnit& u = this->_units[i];
        std::fill(u.counters.begin(), u.counters.end(), 0);
        u.row_specific_threshold.clear();
    }
}
void CBFBased::regStats()
{
    Mitigation::regStats();

    this->maxCount
        .name(name() + ".max_count")
        .desc("maximum count registered by the CBF");
}
/*
CBFBased*
CBFBasedParams::create() const
{
    return new CBFBased(*this);
}
*/
