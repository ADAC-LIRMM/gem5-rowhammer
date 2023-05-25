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

#ifndef __MMU_EVENT_HH__
#define __MMU_EVENT_HH__

#include <vector>

#include "base/logging.hh"
#include "base/types.hh"
#include "base/addr_range.hh"
#include "arch/generic/mmu.hh"

namespace gem5
{

class ThreadContext;
class MMUWatchList;
class System;
class MMUWatchScope;


//MMU watch point that are monitoring mmu translation and are triggered by access to a specific range
/// because mmu access memory for multiple reasons that are not supposed to triggered watchpoint 
//(ex: automatic table walking))
class MMUWatchPoint
{
  protected:
    std::string description;
    MMUWatchScope *scope;
    AddrRange ev_addrRange;
  public:
    MMUWatchPoint(MMUWatchScope *q, const std::string &desc, AddrRange addrRange);

    virtual ~MMUWatchPoint() { if (scope) remove(); }

    // for DPRINTF
    virtual const std::string name() const { return description; }

    std::string descr() const { return description; }
    AddrRange addrRange() const { return ev_addrRange; }
    Addr addr() const { return ev_addrRange.start(); }
    bool remove();
    /**
     * @brief 
     * 
     * @param vaddr 
     * @param paddr 
     * @param size 
     * @param mode 
     * @param tc 
     * @return true if the process really have an effect (
     * considering access math and AddRange intersection)
     */
    virtual bool process(Addr vaddr,Addr paddr,size_t size,BaseMMU::Mode mode,Addr pc,ThreadContext *tc) = 0;
};


//Scope for translation event (ThreadContext is expected to be such a scope)
class MMUWatchScope
{
  public:
    virtual bool close(MMUWatchPoint *wp) = 0;
    virtual bool open(MMUWatchPoint *wp) = 0;
};

class MMUWatchList : public MMUWatchScope
{
  protected:
    typedef std::vector<MMUWatchPoint* > Map;

  public:
    typedef Map::iterator iterator;
    typedef Map::const_iterator const_iterator;


  protected:
    Map addrMap;//TODO: structure exploration of the map 
    //using a range or an other method.

    bool doService(Addr vaddr,Addr paddr,size_t size,BaseMMU::Mode mode, 
      Addr pc,ThreadContext *tc);

  public:
    MMUWatchList();
    ~MMUWatchList();

    bool open(MMUWatchPoint *wp) override;
    bool close(MMUWatchPoint *wp) override;
    bool service(Addr vaddr,Addr paddr,size_t size, 
        BaseMMU::Mode mode, Addr pc,ThreadContext *tc)
    {
        if (addrMap.empty())
            return false;

        return doService(vaddr,paddr,size,mode,pc,tc);
    }

    void dump() const;
};


inline
MMUWatchPoint::MMUWatchPoint(MMUWatchScope *s, const std::string &desc, AddrRange addrRange)
    : description(desc), scope(s), ev_addrRange(addrRange)
{
    scope->open(this);
}

inline bool
MMUWatchPoint::remove()
{
    if (!scope)
        panic("cannot remove an uninitialized event;");

    return scope->close(this);
}



} // namespace gem5

#endif // __MMU_EVENT_HH__
