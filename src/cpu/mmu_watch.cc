/*
 * Copyright (c) 2002-2005 The Regents of The University of Michigan
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are
 * met: redistributions of source code must retain the above copyright
 * notice, this list of conditions and the following disclaimer;
 * redistributions in binary form must reproduce the above copyright
 * notice, this list of conditions and the following disclaimer in the
 * documentation and/or other materials provided with the distribution;
 * neither the name of the copyright holders nor the names of its
 * contributors may be used to endorse or promote products derived from
 * this software without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 * "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
 * A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
 * OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
 * SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
 * LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
 * DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
 * THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 * (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

#include "cpu/mmu_watch.hh"

#include <algorithm>
#include <string>
#include <utility>

#include "base/debug.hh"
#include "base/trace.hh"
#include "debug/MMUWatch.hh"
#include "mem/translating_port_proxy.hh"
#include "mem/se_translating_port_proxy.hh"
#include "sim/cur_tick.hh"
#include "sim/system.hh"

namespace gem5
{


MMUWatchList::MMUWatchList()
{}

MMUWatchList::~MMUWatchList()
{}

bool
MMUWatchList::close(MMUWatchPoint* event)
{
    int removed = 0;
    for (iterator i =addrMap.begin(); i != addrMap.end(); i++) {
        if (*i == event) {
            DPRINTF(MMUWatch, "MMU watchpoint closed at %#x: %s\n",
                    event->addr(), event->descr());
            i = addrMap.erase(i);
            ++removed;
            break;
        } 
    }

    return removed > 0;
}

bool
MMUWatchList::open(MMUWatchPoint *event)
{
    addrMap.push_back(event);

    DPRINTF(MMUWatch, "MMU watchpoint opened for addr %#x: %s\n",
            event->addr(), event->descr());

    return true;
}

bool
MMUWatchList::doService(Addr vaddr,Addr paddr,size_t size,BaseMMU::Mode mode,Addr pc, ThreadContext *tc)
{
    // Using the raw PC address will fail to break on Alpha PALcode addresses,
    // but that is a rare use case.
    int serviced = 0;
    for (iterator i =addrMap.begin(); i != addrMap.end(); i++) {
        
            if((*i)->process(vaddr,paddr,size,mode,pc,tc)){
                DPRINTF(MMUWatch, "MMU watchpoint serviced at %#x: %s\n",
                    (*i)->addrRange().start(), (*i)->descr());
                ++serviced;
            }
            
        }

    return serviced > 0;
}

void
MMUWatchList::dump() const
{
    const_iterator i = addrMap.begin();
    const_iterator e = addrMap.end();

    for (; i != e; ++i)
        cprintf("%d: point at %#x:%#x %s\n", curTick(), (*i)->addrRange().start(),
                (*i)->addrRange().end(),(*i)->descr());
}



} // namespace gem5
