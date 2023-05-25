/*
 * Copyright (c) 2003-2005 The Regents of The University of Michigan
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

#include <cstring>
#include <iostream>

#include "args.hh"
#include "command.hh"
#include "dispatch_table.hh"

namespace
{

void
 m5_env(const DispatchTable &dt, std::ostream &os,const std::string &varname)
{
    size_t size=1024;
    char* buf=(char*)malloc(size);

    // Touch all buffer pages to ensure they are mapped in the
    // page table. This is required in the case of X86_FS, where
    // Linux does demand paging.
    std::memset(buf, 0, sizeof(buf));

    int len;
    int offset = 0;
    while ((len = (*dt.m5_env)(buf, sizeof(buf), varname.c_str())) >= size) {
        free(buf);
        size=len+1;
        buf=(char*)malloc(size);
    }
    buf[len] = '\0';
    os.write(buf,len);
    os.flush();
    free(buf);
}

bool
do_m5_env(const DispatchTable &dt, Args &args)
{
    if (args.size() !=1)
        return false;
    const std::string &varname = args.pop();
    m5_env(dt, std::cout,varname);

    return true;
}

Command m5_env_cmd = {
    "env", 1, 1, do_m5_env, "\n"
        "        Access from the system environment variable "
            "stdout" };

} // anonymous namespace
