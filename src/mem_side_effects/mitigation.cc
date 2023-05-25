
#include "mem_side_effects/mitigation.hh"

#include "base/trace.hh"
#include "debug/MemCorruptMitigation.hh"

using namespace gem5;
using namespace memory;

Mitigation::Mitigation(const Params &params) : SimObject(params)
{

}

void Mitigation::refresh_row(MemoryCorruption& mem_corrupt,
                             const std::vector<int>& addr_vec)
{
    DPRINTF(MemCorruptMitigation, "refresh row [%d|%d|%d|%d|%d|%d]\n",
            addr_vec[0], addr_vec[1], addr_vec[2], addr_vec[3], addr_vec[4],
            addr_vec[5]);
    mem_corrupt.refresh_row(addr_vec);
    this->additionalRefreshesCount++;
}

bool Mitigation::neighbor_row(MemoryCorruption& mem_corrupt,
                              const std::vector<int>& addr_vec, int offset,
                              std::vector<int>& neighbor_vec)
{
    return mem_corrupt.neighbor(addr_vec, offset, neighbor_vec);
}
unsigned int Mitigation::addr_vec_to_addr(MemoryCorruption& mem_corrupt,
                                    const std::vector<int>& addr_vec)
{
    return mem_corrupt.vec_to_addr(addr_vec);
}
void Mitigation::addr_to_addr_vec(MemoryCorruption& mem_corrupt,
                        unsigned int addr, std::vector<int>& addr_vec)
{
    mem_corrupt.addr_to_vec(addr, addr_vec);
}

void Mitigation::regStats()
{
    SimObject::regStats();

    this->additionalRefreshesCount
        .name(name() + ".additional_refs")
        .desc("Additional REFs performed by the rowhammer mitigation");
}
