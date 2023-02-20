

#include <iostream>
#include <string>
#include <vector>

#include "mem_side_effects/memory_corruption.hh"
#include "mem_side_effects/mitigation.hh"

#include "base/trace.hh"
#include "debug/MemCorrupt.hh"
#include "debug/MemCorruptDetails.hh"

using namespace std;


unsigned int count_bits_char(unsigned char x)
{
    x = (x & 0x55) + ((x >> 1) & 0xFF);
    x = (x & 0x33) + ((x >> 2) & 0x33);
    x = (x & 0x0f) + ((x >> 4) & 0x0f);
    return x;
}

MemoryCorruption::MemoryCorruption(const MemoryCorruptionParams &params) :
        SimObject(params),
        _hammer_threshold(params.hammer_threshold),
        _enable_corruption(params.enable_corruption),
#if ALL_MEM
#else
        _target_addrs(params.target_addrs),
#endif
        _layout_config(params.layout_config),
        _flip_polynomial(params.flip_polynomial),
        _mitigation(params.mitigation),
        rh_threshold_stat(),
        maxDisturbLevel(0),
        bitFlipsCount(0)
{
    this->rh_threshold_stat.scalar(params.hammer_threshold);
#if ALL_MEM
#else
    DPRINTF(MemCorrupt, "targets: %d.\n", _target_addrs.size());
    _target_ACT_counter.resize(_target_addrs.size());
    for (int i=0; i < _target_ACT_counter.size(); i++) {
        _target_ACT_counter[i] = 0;
        DPRINTF(MemCorrupt, "target %d: %xh\n", i, _target_addrs[i]);
    }
#endif
    if (_layout_config.size() > 0) {
        DPRINTF(MemCorruptDetails,
                "use dram layout config file with %d rows\n",
                _layout_config.size());
    }
    else {
        DPRINTF(MemCorruptDetails, "use consecutive rows dram layout\n");
    }
    _refresh_count_down = 8196-1;
}

void MemoryCorruption::init(Ramulator& ramulator)
{
    this->_ramulator = &ramulator;
    if (this->_mitigation != nullptr)
    {
        this->_mitigation->init(*this);
    }
}

bool MemoryCorruption::neighbor(const std::vector<int>& addr_vec,
                                int offset, std::vector<int>& neighbor_vec)
{
    //get address row location

    const unsigned int row_level = this->_ramulator->getRowLevel();
    unsigned int row = addr_vec[row_level];
    if (row < _layout_config.size()) {
        row = _layout_config[row];
    }

    //get neighbor row location
    if (row < -offset)
        return false;

    unsigned int neighbor_row = row + offset;

    const unsigned int row_bits =
            this->_ramulator->getLevelAddrBits(row_level);
    const unsigned int row_mask = (1 << row_bits) - 1;
    if ((neighbor_row & row_mask) != neighbor_row)
        return false;

    for (int i=0; i< _layout_config.size(); i++) {
        if (neighbor_row == _layout_config[i]) {
            neighbor_row = i;
            break;
        }
    }

    // set neighbor addr vector to addr_vec, except row

    if (addr_vec.size() != neighbor_vec.size())
        neighbor_vec.resize(addr_vec.size());

    for (int i=0; i < row_level; i++)
        neighbor_vec[i] = addr_vec[i];

    neighbor_vec[row_level] = neighbor_row;

    for (int i=row_level+1; i < addr_vec.size(); i++)
        neighbor_vec[i] = addr_vec[i];

    return true;
}

int MemoryCorruption::getMapKey(const std::vector<int>& addr_vec,
                                int neighbor_rows[2],
                                int neighbor_keys[2])
{
    const unsigned int rowLevel = this->_ramulator->getRowLevel();
    unsigned int row = addr_vec[rowLevel];

    if (row < _layout_config.size()) {
        row = _layout_config[row];
    }
    unsigned int bank_id = 0;
    for (int i=0; i<rowLevel; i++) {
        bank_id = (bank_id << this->_ramulator->getLevelAddrBits(i))
                | addr_vec[i];
    }
    const unsigned int rowBits = this->_ramulator->getLevelAddrBits(rowLevel);
    bank_id <<= rowBits;
    const unsigned int rowMask = (1 << rowBits) - 1;
    neighbor_rows[0] = (row == 0) ? -1 : row - 1;
    neighbor_rows[1] = ((row & rowMask) == rowMask) ? -1 : row + 1;
    neighbor_keys[0] = bank_id | neighbor_rows[0];
    neighbor_keys[1] = bank_id | neighbor_rows[1];

    if (_layout_config.size() > 0
            && (neighbor_rows[0] >= 0 || neighbor_rows[1] >= 0)) {
        bool placed[2] = {false, false};
        unsigned int to_place = 2;
        for (int i=0; i<_layout_config.size() && to_place > 0; i++) {
            if (!placed[0] && _layout_config[i] == neighbor_rows[0]) {
                placed[0] = true;
                to_place--;
                neighbor_rows[0] = i;
            } else if (!placed[1] && _layout_config[i] == neighbor_rows[0]) {
                placed[1] = true;
                to_place--;
                neighbor_rows[1] = i;
            }
        }
    }
    return bank_id | (row & rowMask);
}

unsigned int MemoryCorruption::corrupt(Ramulator& ramulator, std::vector<int>& addr_vec,
                               double flip_probability,
                               bool to1, unsigned int random_seed)
{
    static const unsigned int colLvl = ramulator.getColumnLevel();
    static const unsigned int columns = 1 << ramulator.getLevelAddrBits(colLvl);
    static const unsigned int txBits = ramulator.getTxBits();
    int original_col = addr_vec[colLvl];
    addr_vec[colLvl] = 0;
    unsigned int flipped = 0;
    int length = 1 << txBits;
    for(int col = 0; col < columns; col++) {
        addr_vec[colLvl] = col;
        long addr = ramulator.vec_to_addr(addr_vec);
        uint8_t *host_addr = this->_ramulator->toHostAddr(addr);
        if (flip_probability >= 1) {
            uint8_t buffer[length];
            memcpy(buffer, host_addr, length);
            int bits1 = 0;
            for(int i=0; i < length; i++) {
                bits1 += count_bits_char(buffer[i]);
            }
            if (to1) {
                memset(host_addr, 0xFF, length);
                flipped += length *8 - bits1;
            } else {
                memset(host_addr, 0x00, length);
                flipped += bits1;
            }
        } else if (flip_probability > 0) {
            uint8_t buffer[length];
            memcpy(buffer, host_addr, length);
            srand(random_seed + addr);
            const unsigned int rand_threshold =
                    (unsigned int) (flip_probability * RAND_MAX);
            if (to1) {
                for (int i=0; i<length; i++) {
                    for (int j=0; j<8; j++) {
                        if (rand() < rand_threshold &&
                                (buffer[i] & (1 << j)) == 0) {
                            buffer[i] |= 1 << j;
                            flipped++;
                        }
                    }
                }
            } else {
                for (int i=0; i<length; i++) {
                    for (int j=0; j<8; j++) {
                        if (rand() < rand_threshold &&
                                (buffer[i] & (1 << j)) != 0) {
                            buffer[i] &= 0xFF - (1 << j);
                            flipped++;
                        }
                    }
                }
            }
            memcpy(host_addr, buffer, length);
        }
    }
    addr_vec[colLvl] = original_col;
    if (flipped > 0)
        this->bitFlipsCount += flipped;
    return flipped;
}

void MemoryCorruption::onACT(Ramulator& ramulator,
                             const std::vector<int>& addr_vec)
{
#if ALL_MEM
    int neighbor_rows[2];
    int neighbor_keys[2];
    const int key = this->getMapKey(addr_vec, neighbor_rows,
                                    neighbor_keys);

    DPRINTF(MemCorruptDetails, "ACT [%d|%d|%d|%d|%d|%d] neighbor "
            "rows %d and %d\n", addr_vec[0], addr_vec[1], addr_vec[2],
            addr_vec[3], addr_vec[4], addr_vec[5],
            neighbor_rows[0], neighbor_rows[1]);
    if (this->_row_counters.find(key) != this->_row_counters.end())
    {
        const unsigned int val = this->_row_counters[key];
        if (val > this->maxDisturbLevel.value()) {
            this->maxDisturbLevel = val;
        }
        this->_row_counters.erase(key);
    }
    for (int i=0; i<2; i++) {
        if (neighbor_keys[i] >= 0) {
            this->_row_counters[neighbor_keys[i]] += 1;
            std::vector<int> vec = addr_vec;
            const unsigned int rowLvl = ramulator.getRowLevel(),
                               colLvl = ramulator.getColumnLevel();
            vec[rowLvl] = neighbor_rows[i];
            vec[colLvl] = 0;
            if (this->_row_counters[neighbor_keys[i]] >= _hammer_threshold) {
                long addr = ramulator.vec_to_addr(vec);

                if (_row_counters[neighbor_keys[i]] == _hammer_threshold) {
                    DPRINTF(MemCorrupt, "reached hammer threshold for %08xh "
                            "[%d|%d|%d|%d|%d|%d]\n", addr,
                            vec[0], vec[1], vec[2], vec[3], vec[4], vec[5]);
//TEST BEGIN
                    const unsigned int colLvl = ramulator.getColumnLevel();
                    const unsigned int columns = 1 << ramulator.getLevelAddrBits(colLvl);
                    const unsigned int txBits = ramulator.getTxBits();

                    int original_col = vec[colLvl];
                    vec[colLvl] = 0;
                    unsigned int flipped = 0;
                    int length = 1 << txBits;
                    for(int col = 0; col < columns; col++) {
                        vec[colLvl] = col;
                        long addr = ramulator.vec_to_addr(vec);
                        uint8_t *host_addr = this->_ramulator->toHostAddr(addr);

                        for(int i=0; i < length; i++) {
                            printf("%d,", host_addr[i]);
                        }
                    }
                    printf("\n");
                    vec[colLvl] = original_col;
//TEST END
                }

                if (_enable_corruption) {

                    double probability = this->_flip_polynomial[0];
                    if (this->_flip_polynomial.size() > 1) {
                        unsigned int x = this->_row_counters[neighbor_keys[i]]
                                         - _hammer_threshold;
                        for (int i=1; i<this->_flip_polynomial.size(); i++) {
                            probability += this->_flip_polynomial[i]*x;
                            x *= x;
                        }
                    }
                    const int nb_flipped = this->corrupt(ramulator, vec,
                                                        probability, false, 0);

                    if (nb_flipped > 0)
                        DPRINTF(MemCorrupt, "flipped %d bits/(2^(%d+%d)*8) @ %08xh "
                                "[%d|%d|%d|%d|%d|%d] (hammered %d times)\n",
                                nb_flipped, ramulator.getTxBits(), ramulator.getLevelAddrBits(colLvl), addr, vec[0], vec[1], vec[2],
                                vec[3], vec[4], vec[5],
                                this->_row_counters[neighbor_keys[i]]);
                    ((void)nb_flipped);
                }
            } else {
                DPRINTF(MemCorruptDetails, "neighbors of [%d|%d|%d|%d|%d|%d]"\
                        "ACTed %d times\n",
                        vec[0], vec[1], vec[2], vec[3], vec[4], vec[5],
                        this->_row_counters[neighbor_keys[i]]);
            }
        }
    }

#else
    const int rowLevel = ramulator.getRowLevel();
    const int columnLevel = ramulator.getColumnLevel();
    for (int t=0; t<_target_addrs.size(); t++) {
        std::vector<int> trgt_vec;
        ramulator.addr_to_vec(_target_addrs[t], trgt_vec);
        DPRINTF(MemCorruptDetails,
                "ACT [%d|%d|%d|%d|%d|%d], trgt=[%d|%d|%d|%d|%d|%d]\n",
                addr_vec[0], addr_vec[1], addr_vec[2], addr_vec[3],
                addr_vec[4], addr_vec[5], trgt_vec[0], trgt_vec[1],
                trgt_vec[2], trgt_vec[3], trgt_vec[4], trgt_vec[5]
            );
        bool sameBank = true;

        for (int i = 0; i < trgt_vec.size(); i++) {
            if (i != columnLevel && i != rowLevel) {
                if (addr_vec[i] != -1 && trgt_vec[i] != addr_vec[i]) {
                    sameBank = false;
                    break;
                }
            }
        }
        if (!sameBank) {
            DPRINTF(MemCorruptDetails, "not same bank\n");
            continue;
        }

        const int row = addr_vec[rowLevel];
        const int target_row = trgt_vec[rowLevel];
        if (row == -1) {
            if (_refresh_count_down == 0) {
                _refresh_count_down = 8196-1;
                DPRINTF(MemCorrupt, "resetting row %xh counter\n", target_row);
                _target_ACT_counter[t] = 0;
            }
            else
                _refresh_count_down--;
        }

        else if ((row == target_row)) {
            DPRINTF(MemCorrupt, "resetting row %xh counter\n", target_row);
            _target_ACT_counter[t] = 0;
        }
        else {
            bool adjacent;
            if (_layout_config.size() == 0) {
                adjacent = (row == target_row + 1) || (row == target_row - 1);
                DPRINTF(MemCorruptDetails,
                        "rows %d, %d %sadjacent (w/ consecutive config)\n",
                        row, target_row, adjacent ? "" : "not ");
            }
            else {
                if (row < _layout_config.size()
                        && target_row < _layout_config.size()) {

                    unsigned int row_place = _layout_config[row];
                    unsigned int hammer_place = _layout_config[target_row];
                    adjacent = (row_place == hammer_place + 1)
                            || (row_place == hammer_place - 1);
                    DPRINTF(MemCorruptDetails, "rows %d (@%d) and %d (@%d)"\
                            "%sadjacent (w/ config file)\n",
                            row, row_place, target_row, hammer_place,
                            adjacent ? "" : "not ");
                }
                else {
                    adjacent = false;
                    DPRINTF(MemCorruptDetails,
                            "rows %d, %d out of config file range\n",
                            row, target_row);
                }

            }
            if (adjacent) {
                _target_ACT_counter[t]++;
                DPRINTF(MemCorrupt, "hammering @[%d|%d|%d|%d|%d|%d]\n",
                    trgt_vec[0], trgt_vec[1], trgt_vec[2], trgt_vec[3],
                    trgt_vec[4], trgt_vec[5]);
                DPRINTF(MemCorrupt, "from [%d|%d|%d|%d|%d|%d] (%d)\n",
                    addr_vec[0], addr_vec[1], addr_vec[2], addr_vec[3],
                    addr_vec[4], addr_vec[5], _target_ACT_counter[t]);

                if (_target_ACT_counter[t] >= _hammer_threshold) {
                    DPRINTF(MemCorrupt,
                            "reached hammer threshold for row %xh\n",
                            target_row);
                    if (_enable_corruption) {
                        uint8_t *host_addr =
                                ramulator.toHostAddr(_target_addrs[t]);
                        memset(host_addr, 0, 1<<ramulator.getTxBits());
                    }
                    _target_ACT_counter[t] = 0;
                }
            }
        }
    }
#endif // ALL_MEM
    if (this->_mitigation != nullptr) {
        this->_mitigation->onACT(*this, addr_vec);
    }
}
void MemoryCorruption::onREF(Ramulator& ramulator,
                             const std::vector<int>& addr_vec)
{
#if ALL_MEM
    if (addr_vec[ramulator.getRowLevel()] >= 0) { //row-specific refresh
        this->onACT(ramulator, addr_vec);
    }
    else if (_refresh_count_down == 0) {
        _refresh_count_down = 8196-1;
        DPRINTF(MemCorruptDetails,
                "REF cycle complete => reset ACT counters\n");
        this->_row_counters.clear();
        if (this->_mitigation != nullptr) {
            this->_mitigation->onREF(*this, addr_vec);
        }
        for (const auto& kv : this->_row_counters)
        {
            if (kv.second > this->maxDisturbLevel.value()) {
                this->maxDisturbLevel = kv.second;
            }
        }
    }
    else {
        _refresh_count_down--;
        //DPRINTF(MemCorruptDetails,
        //        "%d REF until ACT counters reset\n",
        //        _refresh_count_down);
    }
#else
    this->onACT(ramulator, addr_vec);
#endif // ALL_MEM
}

void MemoryCorruption::refresh_row(const std::vector<int>& addr_vec)
{
    this->_ramulator->refresh_row(addr_vec);
}

void MemoryCorruption::addr_to_vec(unsigned int addr,
                                   std::vector<int> addr_vec)
{
    this->_ramulator->addr_to_vec(addr, addr_vec);
}

unsigned long MemoryCorruption::vec_to_addr(std::vector<int> addr_vec)
{
    return this->_ramulator->vec_to_addr(addr_vec);
}

unsigned int MemoryCorruption::get_level_addr_bits(unsigned int level) const
{
    return this->_ramulator->getLevelAddrBits(level);
}

unsigned int MemoryCorruption::getBankLevel() const
{
    return this->_ramulator->getBankLevel();
}

unsigned int MemoryCorruption::getRowLevel() const
{
    return this->_ramulator->getRowLevel();
}

unsigned int MemoryCorruption::getColumnLevel() const
{
    return this->_ramulator->getColumnLevel();
}

void MemoryCorruption::regStats()
{
    using namespace Stats;
    SimObject::regStats();

    for (const auto& kv : this->_row_counters)
    {
        if (kv.second > this->maxDisturbLevel.value()) {
            this->maxDisturbLevel = kv.second;
        }
    }

    this->rh_threshold_stat
        .name(name() + ".rh_threshold")
        .desc("rowhammer bitflip threshold");
    this->maxDisturbLevel
        .name(name() + ".maxRowDisturb")
        .desc("maximum disturbance count for a memory row");
    this->bitFlipsCount
        .name(name() + ".bit_flips")
        .desc("number of bit-flips in the memory");
}
/*
MemoryCorruption*
MemoryCorruptionParams::create() const
{
    return new MemoryCorruption(*this);
}
*/
