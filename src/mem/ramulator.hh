/*
 * Copyright (c) 2018 SAFARI Research Group
 * Authors: Minesh Patel
 */

#ifndef RAMULATOR_HH
#define RAMULATOR_HH

#include <deque>
#include <map>
#include <tuple>

#include "Ramulator/src/Config.h"
#include "mem/abstract_mem.hh"
#include "mem_side_effects/memory_corruption.hh"
#include "params/Ramulator.hh"

namespace ramulator
{
    class Request;
    class Gem5Wrapper;
}
using namespace gem5;
using namespace memory;

class Ramulator : public AbstractMemory
{
private:

    class MemoryPort : public SlavePort
    {
    private:
        Ramulator& mem;
    public:
        MemoryPort(const std::string& _name, Ramulator& _mem):
        SlavePort(_name, &_mem), mem(_mem) {}
    protected:
        Tick recvAtomic(PacketPtr pkt) {
            // modified to perform a fixed latency return for
            //atomic packets to enable fast forwarding
            // assert(false && "only accepts functional or timing packets");
            return mem.recvAtomic(pkt);
        }

        void recvFunctional(PacketPtr pkt) {
            mem.recvFunctional(pkt);
        }

        bool recvTimingReq(PacketPtr pkt) {
            return mem.recvTimingReq(pkt);
        }

        void recvRespRetry() {
            mem.recvRespRetry();
        }

        AddrRangeList getAddrRanges() const {
            AddrRangeList ranges;
            ranges.push_back(mem.getAddrRange());
            return ranges;
        }
    };

    MemoryPort port;

    unsigned int requestsInFlight;
    std::map<long, std::deque<PacketPtr> > reads;
    std::map<long, std::deque<PacketPtr> > writes;
    std::deque<PacketPtr> resp_queue;
    std::deque<PacketPtr> pending_del;

    std::string config_file;
    ramulator::Config configs;
    ramulator::Gem5Wrapper *wrapper;
    std::function<void(ramulator::Request&)> read_cb_func;
    std::function<void(ramulator::Request&)> write_cb_func;
    std::function<void(ramulator::Request&)> refresh_cb_func;
    Tick ticks_per_clk;
    bool resp_stall;
    bool req_stall;

    MemoryCorruption *memory_corruption;

    unsigned int numOutstanding() const { return requestsInFlight +
        resp_queue.size(); }

    void sendResponse();
    void tick();

    EventWrapper<Ramulator, &Ramulator::sendResponse> send_resp_event;
    EventWrapper<Ramulator, &Ramulator::tick> tick_event;

public:
    typedef RamulatorParams Params;
    Ramulator(const Params &p);
    virtual void init() override;
    virtual void startup() override;
    DrainState drain() override;
    virtual Port& getPort(const std::string& if_name,
        PortID idx = InvalidPortID) override;

    int getBankLevel();
    int getRowLevel();
    int getColumnLevel();
    int getTxBits();
    int getLevelAddrBits(int level);
    void addr_to_vec(long addr, std::vector<int>& addr_vec);
    long vec_to_addr(const std::vector<int>& addr_vec);
    void refresh_row(const std::vector<int>& addr_vec);
    ~Ramulator();
protected:
    Tick recvAtomic(PacketPtr pkt);
    void recvFunctional(PacketPtr pkt);
    bool recvTimingReq(PacketPtr pkt);
    void recvRespRetry();
    void accessAndRespond(PacketPtr pkt);
    void readComplete(ramulator::Request& req);
    void writeComplete(ramulator::Request& req);
    void refreshComplete(ramulator::Request& req);
};

#endif // RAMULATOR_HH
