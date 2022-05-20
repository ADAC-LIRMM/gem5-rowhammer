/*
 * Copyright (c) 2018 SAFARI Research Group
 * Authors: Minesh Patel
 */

#include "mem/ramulator.hh"

#include "Ramulator/src/Gem5Wrapper.h"
#include "Ramulator/src/Request.h"
#include "base/callback.hh"
#include "debug/Ramulator.hh"
#include "sim/system.hh"

Ramulator::Ramulator(const Params &p):
    AbstractMemory(p),
    port(name() + ".port", *this),
    requestsInFlight(0),
    config_file(p.ramulatorConfigFile),
    configs(p.ramulatorConfigFile),
    wrapper(NULL),
    read_cb_func(std::bind(&Ramulator::readComplete,
    this, std::placeholders::_1)),
    write_cb_func(std::bind(&Ramulator::writeComplete,
    this, std::placeholders::_1)),
    refresh_cb_func(std::bind(&Ramulator::refreshComplete,
    this, std::placeholders::_1)),
    ticks_per_clk(0),
    resp_stall(false),
    req_stall(false),
    memory_corruption(p.memoryCorruption),
    send_resp_event(this),
    tick_event(this)
{
    DPRINTF(Ramulator,
        "Ramulator::Ramulator() called with config file \"%s\" and %d cpus\n",
        config_file.c_str(), p.num_cpus);

    configs.set_core_num(p.num_cpus);
}

Ramulator::~Ramulator()
{
    DPRINTF(Ramulator, "Ramulator::~Ramulator() called\n");
    delete wrapper;
}

void Ramulator::init()
{
    AbstractMemory::init();

    if (!port.isConnected()){
        fatal("Ramulator port %s is not connected\n", name());
    } else {
        port.sendRangeChange();
    }

    // initialize the Ramulator wrapper
    wrapper = new ramulator::Gem5Wrapper(configs, system()->cacheLineSize());
    ticks_per_clk = Tick(wrapper->tCK * SimClock::Float::ns);

    DPRINTF(Ramulator,
    "Initialzed Ramulator with config file '%s' (tCK=%lf, %d ticks per clk)\n",
    config_file.c_str(), wrapper->tCK, ticks_per_clk);

    //Callback* cb = new MakeCallback<ramulator::Gem5Wrapper,
    //&ramulator::Gem5Wrapper::finish>(wrapper);
    //registerExitCallback(cb);
    registerExitCallback([this]() { wrapper->finish(); });

    wrapper->set_refresh_callback(refresh_cb_func);

    memory_corruption->init(*this);
}

void Ramulator::startup() {
    DPRINTF(Ramulator, "Ramulator::startup()\n");
    schedule(tick_event, clockEdge());
}

DrainState Ramulator::drain() {
    DPRINTF(Ramulator,
    "Ramulator draining... numOutstanding() == %d\n", numOutstanding());
    return numOutstanding() != 0 ? DrainState::Draining : DrainState::Drained;
}

Port& Ramulator::getPort(const std::string& if_name,
        PortID idx) {
    if (if_name != "port") {
        return SimObject::getPort(if_name, idx);
    } else {
        return port;
    }
}

void Ramulator::sendResponse() {
    assert(!resp_stall);
    assert(!resp_queue.empty());

    DPRINTF(Ramulator, "Attempting to send response\n");

    long addr = resp_queue.front()->getAddr();
    if (port.sendTimingResp(resp_queue.front()))
    {
        DPRINTF(Ramulator, "Response to %ld sent.\n", addr);
        resp_queue.pop_front();
        if (resp_queue.size() && !send_resp_event.scheduled())
            schedule(send_resp_event, curTick());

        // check if we were asked to drain and if we are now done
        if (numOutstanding() == 0)
            signalDrainDone();
    }
    else
    {
        DPRINTF(Ramulator, "Waiting for response retry for addr %ld\n", addr);
        resp_stall = true;
    }
}

void Ramulator::tick() {
    wrapper->tick();
    if (req_stall){
        req_stall = false;
        port.sendRetryReq();
    }
    schedule(tick_event, curTick() + ticks_per_clk);
}

// added an atomic packet response function to enable fast forwarding
Tick Ramulator::recvAtomic(PacketPtr pkt) {
    access(pkt);

    // set an fixed arbitrary 50ns response time for atomic requests
    return pkt->cacheResponding() ? 0 : 50000;
    // return pkt->memInhibitAsserted() ? 0 : 50000;
}

void Ramulator::recvFunctional(PacketPtr pkt) {
    pkt->pushLabel(name());
    functionalAccess(pkt);
    for (auto i = resp_queue.begin(); i != resp_queue.end(); ++i)
        pkt->trySatisfyFunctional(*i);
    pkt->popLabel();
}

bool Ramulator::recvTimingReq(PacketPtr pkt) {
    // we should never see a new request while in retry
    assert(!req_stall);

    for (PacketPtr pendPkt: pending_del)
        delete pendPkt;
    pending_del.clear();

    if (pkt->cacheResponding()) {
    // if (pkt->memInhibitAsserted()) {
        // snooper will supply based on copy of packet
        // still target's responsibility to delete packet
        pending_del.push_back(pkt);
        return true;
    }

    bool accepted = true;
    if (pkt->isRead()) {
        // DPRINTF(Ramulator, "context id: %d, thread id: %d\n"
        //     , pkt->req->contextId(), pkt->req->threadId());
        DPRINTF(Ramulator, "context id: %d\n", pkt->req->contextId());
        ramulator::Request req(pkt->getAddr(),
        ramulator::Request::Type::READ, read_cb_func, 0);
        accepted = wrapper->send(req);
        if (accepted){
            reads[req.addr].push_back(pkt);
            DPRINTF(Ramulator, "Read to %ld accepted.\n", req.addr);

            // added counter to track requests in flight
            ++requestsInFlight;
        } else {
            req_stall = true;
        }
    } else if (pkt->isWrite()) {
        // Detailed CPU model always comes along with cache model enabled and
        // write requests are caused by cache eviction, so it shouldn't be
        // tallied for any core/thread
        ramulator::Request req(pkt->getAddr(),
        ramulator::Request::Type::WRITE, write_cb_func, 0);
        accepted = wrapper->send(req);
        if (accepted){
            accessAndRespond(pkt);
            DPRINTF(Ramulator,
            "Write to %ld accepted and served.\n", req.addr);

            // added counter to track requests in flight
            ++requestsInFlight;
        } else {
            req_stall = true;
        }
    } else {
        // keep it simple and just respond if necessary
        accessAndRespond(pkt);
    }
    return accepted;
}

void Ramulator::recvRespRetry() {
    DPRINTF(Ramulator, "Retrying\n");

    assert(resp_stall);
    resp_stall = false;
    sendResponse();
}

void Ramulator::accessAndRespond(PacketPtr pkt) {
    bool need_resp = pkt->needsResponse();
    access(pkt);
    if (need_resp) {
        assert(pkt->isResponse());

        // pay for xbar delay and proccess the payload of the packet
        Tick time = curTick() + pkt->headerDelay + pkt->payloadDelay;
        // reset packet timings
        pkt->headerDelay = pkt->payloadDelay = 0;

        DPRINTF(Ramulator, "Queuing response for address %lld\n",
                pkt->getAddr());

        resp_queue.push_back(pkt);
        if (!resp_stall && !send_resp_event.scheduled())
            schedule(send_resp_event, time);
    } else
        pending_del.push_back(pkt);
}

void Ramulator::readComplete(ramulator::Request& req){
    DPRINTF(Ramulator, "Read to %ld completed.\n", req.addr);
    auto& pkt_q = reads.find(req.addr)->second;
    PacketPtr pkt = pkt_q.front();
    pkt_q.pop_front();
    if (!pkt_q.size())
        reads.erase(req.addr);

    // added counter to track requests in flight
    --requestsInFlight;
    if (this->memory_corruption != nullptr
        && req.row_access_result != ramulator::Request::RowAccessResult::HIT) {
        this->memory_corruption->onACT(*this, req.addr_vec);
    }

    accessAndRespond(pkt);
}

void Ramulator::writeComplete(ramulator::Request& req){
    DPRINTF(Ramulator, "Write to addr %ld completed.\n", req.addr);

    // added counter to track requests in flight
    --requestsInFlight;

    if (this->memory_corruption != nullptr
        && req.row_access_result != ramulator::Request::RowAccessResult::HIT) {
        this->memory_corruption->onACT(*this, req.addr_vec);
    }

    if (numOutstanding() == 0)
        signalDrainDone();
}
void Ramulator::refreshComplete(ramulator::Request& req){
    DPRINTF(Ramulator, "Refresh to [%d|%d|%d|%d|%d|%d] completed.\n",
            req.addr_vec[0], req.addr_vec[1], req.addr_vec[2],
            req.addr_vec[3], req.addr_vec[4], req.addr_vec[5]);

    if (this->memory_corruption != nullptr) {
        this->memory_corruption->onREF(*this, req.addr_vec);
    }
}

int Ramulator::getBankLevel(){
    return this->wrapper->getBankLevel();
}
int Ramulator::getRowLevel(){
    return this->wrapper->getRowLevel();
}
int Ramulator::getColumnLevel(){
    return this->wrapper->getColumnLevel();
}
int Ramulator::getTxBits(){
    return this->wrapper->getTxBits();
}
int Ramulator::getLevelAddrBits(int level){
    return this->wrapper->getLevelAddrBits(level);
}
void Ramulator::addr_to_vec(long addr, std::vector<int>& addr_vec){
    this->wrapper->addr_to_vec(addr, addr_vec);
}
long Ramulator::vec_to_addr(const std::vector<int>& addr_vec){
    return this->wrapper->vec_to_addr(addr_vec);
}

void Ramulator::refresh_row(const std::vector<int>& addr_vec){

    long addr = this->vec_to_addr(addr_vec);
    ramulator::Request req(addr, ramulator::Request::Type::READ,
                           refresh_cb_func, 0);
    wrapper->send(req);
}
/*
Ramulator *RamulatorParams::create() const{
    return new Ramulator(*this);
}
*/
