#include "mem_side_effects/para.hh"

#include <random>

using namespace gem5;

using namespace memory;

PARA::PARA(const Params &params) :
    Mitigation(params),
    _p(params.probability),
    _rand_device(),
    _rand_engine(this->_rand_device()),
    _rand_distr(0, 1)
{

}

void PARA::onACT(MemoryCorruption& mem_corrupt,
                 const std::vector<int>& addr_vec)
{
    float random_value = this->_rand_distr(this->_rand_engine);
    //printf("para onACT (%f)\n", random_value);
    if (random_value < this->_p)
    {
        //printf("para onACT (%f)\n", random_value);
        std::vector<int> neighbor_vec(addr_vec.size());
        int offset = (random_value < this->_p/2) ? -1 : +1;
        if (this->neighbor_row(mem_corrupt, addr_vec, offset, neighbor_vec))
        {
            this->refresh_row(mem_corrupt, neighbor_vec);
        }
    }
}
/*
PARA*
PARAParams::create() const
{
    return new PARA(*this);
}
*/
