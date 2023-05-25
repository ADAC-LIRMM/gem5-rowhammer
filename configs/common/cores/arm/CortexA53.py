# Copyright (c) 2014-2017 ARM Limited
# All rights reserved.
#
# The license below extends only to copyright in the software and shall
# not be construed as granting a license to any other intellectual
# property including but not limited to intellectual property relating
# to a hardware implementation of the functionality of the software
# licensed hereunder.  You may use the software subject to the license
# terms below provided that you ensure that this notice is replicated
# unmodified and in its entirety in all distributions of the software,
# modified or unmodified, in source code or in binary form.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met: redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer;
# redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution;
# neither the name of the copyright holders nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# Authors:  Quentin Huppert
#           David Novo
#

""" CortexA53 HPI based on HPI model. A calibration has
been done from a real ARM architecture using CortexA53. 
"""

from __future__ import print_function
from __future__ import absolute_import

from m5.objects import *


# Simple function to allow a string of [01x_] to be converted into a
# mask and value for use with MinorFUTiming
def make_implicant(implicant_string):
    ret_mask = 0
    ret_match = 0

    shift = False
    for char in implicant_string:
        char = char.lower()
        if shift:
            ret_mask <<= 1
            ret_match <<= 1

        shift = True
        if char == '_':
            shift = False
        elif char == '0':
            ret_mask |= 1
        elif char == '1':
            ret_mask |= 1
            ret_match |= 1
        elif char == 'x':
            pass
        else:
            print("Can't parse implicant character", char)

    return (ret_mask, ret_match)

#                          ,----- 36 thumb
#                          | ,--- 35 bigThumb
#                          | |,-- 34 aarch64
a64_inst = make_implicant('0_01xx__xxxx_xxxx_xxxx_xxxx__xxxx_xxxx_xxxx_xxxx')
a32_inst = make_implicant('0_00xx__xxxx_xxxx_xxxx_xxxx__xxxx_xxxx_xxxx_xxxx')
t32_inst = make_implicant('1_10xx__xxxx_xxxx_xxxx_xxxx__xxxx_xxxx_xxxx_xxxx')
t16_inst = make_implicant('1_00xx__xxxx_xxxx_xxxx_xxxx__xxxx_xxxx_xxxx_xxxx')
any_inst = make_implicant('x_xxxx__xxxx_xxxx_xxxx_xxxx__xxxx_xxxx_xxxx_xxxx')
#                          | ||
any_a64_inst = \
           make_implicant('x_x1xx__xxxx_xxxx_xxxx_xxxx__xxxx_xxxx_xxxx_xxxx')
any_non_a64_inst = \
           make_implicant('x_x0xx__xxxx_xxxx_xxxx_xxxx__xxxx_xxxx_xxxx_xxxx')

def encode_opcode(pattern):
    def encode(opcode_string):
        a64_mask, a64_match = pattern
        mask, match = make_implicant(opcode_string)
        return (a64_mask | mask), (a64_match | match)
    return encode

a64_opcode = encode_opcode(a64_inst)
a32_opcode = encode_opcode(a32_inst)
t32_opcode = encode_opcode(t32_inst)
t16_opcode = encode_opcode(t16_inst)

# These definitions (in some form) should probably be part of TimingExpr

def literal(value):
    def body(env):
        ret = TimingExprLiteral()
        ret.value = value
        return ret
    return body

def bin(op, left, right):
    def body(env):
        ret = TimingExprBin()
        ret.op = 'timingExpr' + op
        ret.left = left(env)
        ret.right = right(env)
        return ret
    return body

def un(op, arg):
    def body(env):
        ret = TimingExprUn()
        ret.op = 'timingExpr' + op
        ret.arg = arg(env)
        return ret
    return body

def ref(name):
    def body(env):
        if name in env:
            ret = TimingExprRef()
            ret.index = env[name]
        else:
            print("Invalid expression name", name)
            ret = TimingExprNull()
        return ret
    return body

def if_expr(cond, true_expr, false_expr):
    def body(env):
        ret = TimingExprIf()
        ret.cond = cond(env)
        ret.trueExpr = true_expr(env)
        ret.falseExpr = false_expr(env)
        return ret
    return body

def src(index):
    def body(env):
        ret = TimingExprSrcReg()
        ret.index = index
        return ret
    return body

def int_reg(reg):
    def body(env):
        ret = TimingExprReadIntReg()
        ret.reg = reg(env)
        return ret
    return body

def let(bindings, expr):
    def body(env):
        ret = TimingExprLet()
        let_bindings = []
        new_env = {}
        i = 0

        # Make the sub-expression as null to start with
        for name, binding in bindings:
            new_env[name] = i
            i += 1

        defns = []
        # Then apply them to the produced new env
        for i in range(0, len(bindings)):
            name, binding_expr = bindings[i]
            defns.append(binding_expr(new_env))

        ret.defns = defns
        ret.expr = expr(new_env)

        return ret
    return body

def expr_top(expr):
    return expr([])

class CortexA53_DefaultInt(MinorFUTiming):
    description = 'HPI_DefaultInt'
    mask, match = any_non_a64_inst
    srcRegsRelativeLats = [3, 3, 2, 2, 2, 1, 0]

class CortexA53_DefaultA64Int(MinorFUTiming):
    description = 'HPI_DefaultA64Int'
    mask, match = any_a64_inst
    # r, l, (c)
    srcRegsRelativeLats = [2, 2, 2, 0]

class CortexA53_DefaultMul(MinorFUTiming):
    description = 'HPI_DefaultMul'
    mask, match = any_non_a64_inst
    # f, f, f, r, l, a?
    srcRegsRelativeLats = [0, 0, 0, 0, 0, 0, 0]

class CortexA53_DefaultA64Mul(MinorFUTiming):
    description = 'HPI_DefaultA64Mul'
    mask, match = any_a64_inst
    # a (zr for mul), l, r
    srcRegsRelativeLats = [0, 0, 0, 0]
    # extraCommitLat = 1

class CortexA53_DefaultVfp(MinorFUTiming):
    description = 'HPI_DefaultVfp'
    mask, match = any_non_a64_inst
    # cpsr, z, z, z, cpacr, fpexc, l_lo, r_lo, l_hi, r_hi (from vadd2h)
    srcRegsRelativeLats = [5, 5, 5, 5, 5, 5,  2, 2, 2, 2, 2, 2, 2, 2, 0]

class CortexA53_DefaultA64Vfp(MinorFUTiming):
    description = 'HPI_DefaultA64Vfp'
    mask, match = any_a64_inst
    # cpsr, cpacr_el1, fpscr_exc, ...
    srcRegsRelativeLats = [5, 5, 5, 2]

class CortexA53_FMADD_A64(MinorFUTiming):
    description = 'HPI_FMADD_A64'
    mask, match = a64_opcode('0001_1111_0x0x_xxxx__0xxx_xxxx_xxxx_xxxx')
    #                                    t
    # cpsr, cpacr_el1, fpscr_exc, 1, 1, 2, 2, 3, 3, fpscr_exc, d, d, d, d
    srcRegsRelativeLats = [5, 5, 5,  0, 0,  0, 0,  1, 1,  0,  0, 0, 0, 0]

class CortexA53_FMSUB_D_A64(MinorFUTiming):
    description = 'HPI_FMSUB_D_A64'
    mask, match = a64_opcode('0001_1111_0x0x_xxxx__1xxx_xxxx_xxxx_xxxx')
    #                                    t
    # cpsr, cpacr_el1, fpscr_exc, 1, 1, 2, 2, 3, 3, fpscr_exc, d, d, d, d
    srcRegsRelativeLats = [5, 5, 5,  0, 0,  0, 0,  1, 1,  0,  0, 0, 0, 0]

class CortexA53_FMOV_A64(MinorFUTiming):
    description = 'HPI_FMOV_A64'
    mask, match = a64_opcode('0001_1110_0x10_0000__0100_00xx_xxxx_xxxx')
    # cpsr, cpacr_el1, fpscr_exc, 1, 1, 2, 2, 3, 3, fpscr_exc, d, d, d, d
    srcRegsRelativeLats = [5, 5, 5, 0]

class CortexA53_ADD_SUB_vector_scalar_A64(MinorFUTiming):
    description = 'HPI_ADD_SUB_vector_scalar_A64'
    mask, match = a64_opcode('01x1_1110_xx1x_xxxx__1000_01xx_xxxx_xxxx')
    # cpsr, z, z, z, cpacr, fpexc, l0, r0, l1, r1, l2, r2, l3, r3 (for vadd2h)
    srcRegsRelativeLats = [5, 5, 5, 4]


class CortexA53_ADD_SUB_vector_vector_A64(MinorFUTiming):
    description = 'HPI_ADD_SUB_vector_vector_A64'
    mask, match = a64_opcode('0xx0_1110_xx1x_xxxx__1000_01xx_xxxx_xxxx')
    # cpsr, z, z, z, cpacr, fpexc, l0, r0, l1, r1, l2, r2, l3, r3 (for vadd2h)
    srcRegsRelativeLats = [5, 5, 5, 4]

class CortexA53_FDIV_scalar_32_A64(MinorFUTiming):
    description = 'HPI_FDIV_scalar_32_A64'
    mask, match = a64_opcode('0001_1110_001x_xxxx__0001_10xx_xxxx_xxxx')
    extraCommitLat = 6
    srcRegsRelativeLats = [0, 0, 0, 20,  4]

class CortexA53_FDIV_scalar_64_A64(MinorFUTiming):
    description = 'HPI_FDIV_scalar_64_A64'
    mask, match = a64_opcode('0001_1110_011x_xxxx__0001_10xx_xxxx_xxxx')
    extraCommitLat = 15
    srcRegsRelativeLats = [0, 0, 0, 20,  4]

# CINC CINV CSEL CSET CSETM CSINC CSINC CSINV CSINV CSNEG
class CortexA53_Cxxx_A64(MinorFUTiming):
    description = 'HPI_Cxxx_A64'
    mask, match = a64_opcode('xx01_1010_100x_xxxx_xxxx__0xxx_xxxx_xxxx')
    srcRegsRelativeLats = [3, 3, 3, 2, 2]

class CortexA53_DefaultMem(MinorFUTiming):
    description = 'HPI_DefaultMem'
    mask, match = any_non_a64_inst
    srcRegsRelativeLats = [1, 1, 1, 1, 1, 2]
    # Assume that LDR/STR take 2 cycles for resolving dependencies
    # (1 + 1 of the FU)
    extraAssumedLat = 2

class CortexA53_DefaultMem64(MinorFUTiming):
    description = 'HPI_DefaultMem64'
    mask, match = any_a64_inst
    srcRegsRelativeLats = [0]
    # Assume that LDR/STR take 2 cycles for resolving dependencies
    # (1 + 1 of the FU)
    extraAssumedLat = 3

class CortexA53_DataProcessingMovShiftr(MinorFUTiming):
    description = 'HPI_DataProcessingMovShiftr'
    mask, match = a32_opcode('xxxx_0001_101x_xxxx__xxxx_xxxx_xxx1_xxxx')
    srcRegsRelativeLats = [3, 3, 2, 2, 2, 1, 0]

class CortexA53_DataProcessingMayShift(MinorFUTiming):
    description = 'HPI_DataProcessingMayShift'
    mask, match = a32_opcode('xxxx_000x_xxxx_xxxx__xxxx_xxxx_xxxx_xxxx')
    srcRegsRelativeLats = [3, 3, 2, 2, 1, 1, 0]

class CortexA53_DataProcessingNoShift(MinorFUTiming):
    description = 'HPI_DataProcessingNoShift'
    mask, match = a32_opcode('xxxx_000x_xxxx_xxxx__xxxx_0000_0xx0_xxxx')
    srcRegsRelativeLats = [3, 3, 2, 2, 2, 1, 0]

class CortexA53_DataProcessingAllowShifti(MinorFUTiming):
    description = 'HPI_DataProcessingAllowShifti'
    mask, match = a32_opcode('xxxx_000x_xxxx_xxxx__xxxx_xxxx_xxx0_xxxx')
    srcRegsRelativeLats = [3, 3, 2, 2, 1, 1, 0]

class CortexA53_DataProcessingSuppressShift(MinorFUTiming):
    description = 'HPI_DataProcessingSuppressShift'
    mask, match = a32_opcode('xxxx_000x_xxxx_xxxx__xxxx_xxxx_xxxx_xxxx')
    srcRegsRelativeLats = []
    suppress = True

class CortexA53_DataProcessingSuppressBranch(MinorFUTiming):
    description = 'HPI_DataProcessingSuppressBranch'
    mask, match = a32_opcode('xxxx_1010_xxxx_xxxx__xxxx_xxxx_xxxx_xxxx')
    srcRegsRelativeLats = []
    suppress = True

class CortexA53_BFI_T1(MinorFUTiming):
    description = 'HPI_BFI_T1'
    mask, match = t32_opcode('1111_0x11_0110_xxxx__0xxx_xxxx_xxxx_xxxx')
    srcRegsRelativeLats = [0, 0, 0, 1, 1, 0]

class CortexA53_BFI_A1(MinorFUTiming):
    description = 'HPI_BFI_A1'
    mask, match = a32_opcode('xxxx_0111_110x_xxxx__xxxx_xxxx_x001_xxxx')
    # f, f, f, dest, src
    srcRegsRelativeLats = [0, 0, 0, 1, 1, 0]

class CortexA53_CLZ_T1(MinorFUTiming):
    description = 'HPI_CLZ_T1'
    mask, match = t32_opcode('1111_1010_1011_xxxx__1111_xxxx_1000_xxxx')
    srcRegsRelativeLats = [3, 3, 2, 2, 2, 1, 0]

class CortexA53_CLZ_A1(MinorFUTiming):
    description = 'HPI_CLZ_A1'
    mask, match = a32_opcode('xxxx_0001_0110_xxxx__xxxx_xxxx_0001_xxxx')
    srcRegsRelativeLats = [3, 3, 2, 2, 2, 1, 0]

class CortexA53_CMN_immediate_A1(MinorFUTiming):
    description = 'HPI_CMN_immediate_A1'
    mask, match = a32_opcode('xxxx_0011_0111_xxxx__xxxx_xxxx_xxxx_xxxx')
    srcRegsRelativeLats = [3, 3, 3, 2, 2, 3, 3, 3, 0]

class CortexA53_CMN_register_A1(MinorFUTiming):
    description = 'HPI_CMN_register_A1'
    mask, match = a32_opcode('xxxx_0001_0111_xxxx__xxxx_xxxx_xxx0_xxxx')
    srcRegsRelativeLats = [3, 3, 3, 2, 2, 3, 3, 3, 0]

class CortexA53_CMP_immediate_A1(MinorFUTiming):
    description = 'HPI_CMP_immediate_A1'
    mask, match = a32_opcode('xxxx_0011_0101_xxxx__xxxx_xxxx_xxxx_xxxx')
    srcRegsRelativeLats = [3, 3, 3, 2, 2, 3, 3, 3, 0]

class CortexA53_CMP_register_A1(MinorFUTiming):
    description = 'HPI_CMP_register_A1'
    mask, match = a32_opcode('xxxx_0001_0101_xxxx__xxxx_xxxx_xxx0_xxxx')
    srcRegsRelativeLats = [3, 3, 3, 2, 2, 3, 3, 3, 0]

class CortexA53_MLA_T1(MinorFUTiming):
    description = 'HPI_MLA_T1'
    mask, match = t32_opcode('1111_1011_0000_xxxx__xxxx_xxxx_0000_xxxx')
    # z, z, z, a, l?, r?
    srcRegsRelativeLats = [0, 0, 0, 0, 0, 2, 0]

class CortexA53_MLA_A1(MinorFUTiming):
    description = 'HPI_MLA_A1'
    mask, match = a32_opcode('xxxx_0000_001x_xxxx__xxxx_xxxx_1001_xxxx')
    # z, z, z, a, l?, r?
    srcRegsRelativeLats = [0, 0, 0, 0, 0, 2, 0]

class CortexA53_MADD_A64(MinorFUTiming):
    description = 'HPI_MADD_A64'
    mask, match = a64_opcode('x001_1011_000x_xxxx__0xxx_xxxx_xxxx_xxxx')
    # a, l?, r?
    srcRegsRelativeLats = [1, 1, 1, 0]
    extraCommitLat = 1

class CortexA53_MLS_T1(MinorFUTiming):
    description = 'HPI_MLS_T1'
    mask, match = t32_opcode('1111_1011_0000_xxxx__xxxx_xxxx_0001_xxxx')
    # z, z, z, l?, a, r?
    srcRegsRelativeLats = [0, 0, 0, 2, 0, 0, 0]

class CortexA53_MLS_A1(MinorFUTiming):
    description = 'HPI_MLS_A1'
    mask, match = a32_opcode('xxxx_0000_0110_xxxx__xxxx_xxxx_1001_xxxx')
    # z, z, z, l?, a, r?
    srcRegsRelativeLats = [0, 0, 0, 2, 0, 0, 0]

class CortexA53_MOVT_A1(MinorFUTiming):
    description = 'HPI_MOVT_A1'
    mask, match = t32_opcode('xxxx_0010_0100_xxxx__xxxx_xxxx_xxxx_xxxx')

class CortexA53_MUL_T1(MinorFUTiming):
    description = 'HPI_MUL_T1'
    mask, match = t16_opcode('0100_0011_01xx_xxxx')
class CortexA53_MUL_T2(MinorFUTiming):
    description = 'HPI_MUL_T2'
    mask, match = t32_opcode('1111_1011_0000_xxxx_1111_xxxx_0000_xxxx')

class CortexA53_PKH_T1(MinorFUTiming):
    description = 'HPI_PKH_T1'
    mask, match = t32_opcode('1110_1010_110x_xxxx__xxxx_xxxx_xxxx_xxxx')
    srcRegsRelativeLats = [0, 0, 0, 2, 1, 0]

class CortexA53_PKH_A1(MinorFUTiming):
    description = 'HPI_PKH_A1'
    mask, match = a32_opcode('xxxx_0110_1000_xxxx__xxxx_xxxx_xx01_xxxx')
    srcRegsRelativeLats = [0, 0, 0, 2, 1, 0]

class CortexA53_QADD_QSUB_T1(MinorFUTiming):
    description = 'HPI_QADD_QSUB_T1'
    mask, match = t32_opcode('1111_1010_1000_xxxx__1111_xxxx_10x0_xxxx')
    srcRegsRelativeLats = [0, 0, 0, 1, 1, 0]

class CortexA53_QADD_QSUB_A1(MinorFUTiming):
    description = 'HPI_QADD_QSUB_A1'
    mask, match = a32_opcode('xxxx_0001_00x0_xxxx__xxxx_xxxx_0101_xxxx')
    srcRegsRelativeLats = [0, 0, 0, 1, 1, 0]

# T1 QADD16 QADD8 QSUB16 QSUB8 UQADD16 UQADD8 UQSUB16 UQSUB8
class CortexA53_QADD_ETC_T1(MinorFUTiming):
    description = 'HPI_QADD_ETC_T1'
    mask, match = t32_opcode('1111_1010_1x0x_xxxx__1111_xxxx_0x01_xxxx')
    srcRegsRelativeLats = [0, 0, 0, 1, 1, 0]

# A1 QADD16 QADD8 QSAX QSUB16 QSUB8 UQADD16 UQADD8 UQASX UQSAX UQSUB16 UQSUB8
class CortexA53_QADD_ETC_A1(MinorFUTiming):
    description = 'HPI_QADD_ETC_A1'
    mask, match = a32_opcode('xxxx_0110_0x10_xxxx__xxxx_xxxx_xxx1_xxxx')
    srcRegsRelativeLats = [0, 0, 0, 1, 1, 0]

class CortexA53_QASX_QSAX_UQASX_UQSAX_T1(MinorFUTiming):
    description = 'HPI_QASX_QSAX_UQASX_UQSAX_T1'
    mask, match = t32_opcode('1111_1010_1x10_xxxx__1111_xxxx_0x01_xxxx')
    srcRegsRelativeLats = [0, 0, 0, 1, 1, 0]

class CortexA53_QDADD_QDSUB_T1(MinorFUTiming):
    description = 'HPI_QDADD_QDSUB_T1'
    mask, match = t32_opcode('1111_1010_1000_xxxx__1111_xxxx_10x1_xxxx')
    srcRegsRelativeLats = [0, 0, 0, 0, 1, 0]

class CortexA53_QDADD_QDSUB_A1(MinorFUTiming):
    description = 'HPI_QDADD_QSUB_A1'
    mask, match = a32_opcode('xxxx_0001_01x0_xxxx__xxxx_xxxx_0101_xxxx')
    srcRegsRelativeLats = [0, 0, 0, 0, 1, 0]

class CortexA53_RBIT_A1(MinorFUTiming):
    description = 'HPI_RBIT_A1'
    mask, match = a32_opcode('xxxx_0110_1111_xxxx__xxxx_xxxx_0011_xxxx')
    srcRegsRelativeLats = [0, 0, 0, 1, 0]

class CortexA53_REV_REV16_A1(MinorFUTiming):
    description = 'HPI_REV_REV16_A1'
    mask, match = a32_opcode('xxxx_0110_1011_xxxx__xxxx_xxxx_x011_xxxx')
    srcRegsRelativeLats = [0, 0, 0, 1, 0]

class CortexA53_REVSH_A1(MinorFUTiming):
    description = 'HPI_REVSH_A1'
    mask, match = a32_opcode('xxxx_0110_1111_xxxx__xxxx_xxxx_1011_xxxx')
    srcRegsRelativeLats = [0, 0, 0, 1, 0]

class CortexA53_ADD_ETC_A1(MinorFUTiming):
    description = 'HPI_ADD_ETC_A1'
    mask, match = a32_opcode('xxxx_0110_0xx1_xxxx__xxxx_xxxx_x001_xxxx')
    srcRegsRelativeLats = [0, 0, 0, 2, 2, 0]

class CortexA53_ADD_ETC_T1(MinorFUTiming):
    description = 'HPI_ADD_ETC_A1'
    mask, match = t32_opcode('1111_1010_100x_xxxx__1111_xxxx_0xx0_xxxx')
    srcRegsRelativeLats = [0, 0, 0, 2, 2, 0]

class CortexA53_SASX_SHASX_UASX_UHASX_A1(MinorFUTiming):
    description = 'HPI_SASX_SHASX_UASX_UHASX_A1'
    mask, match = a32_opcode('xxxx_0110_0xx1_xxxx__xxxx_xxxx_0011_xxxx')
    srcRegsRelativeLats = [3, 3, 2, 2, 2, 1, 0]

class CortexA53_SBFX_UBFX_A1(MinorFUTiming):
    description = 'HPI_SBFX_UBFX_A1'
    mask, match = a32_opcode('xxxx_0111_1x1x_xxxx__xxxx_xxxx_x101_xxxx')
    srcRegsRelativeLats = [0, 0, 0, 1, 0]

### SDIV

sdiv_lat_expr = expr_top(let([
    ('left', un('SignExtend32To64', int_reg(src(4)))),
    ('right', un('SignExtend32To64', int_reg(src(3)))),
    ('either_signed', bin('Or',
        bin('SLessThan', ref('left'), literal(0)),
        bin('SLessThan', ref('right'), literal(0)))),
    ('left_size', un('SizeInBits', un('Abs', ref('left')))),
    ('signed_adjust', if_expr(ref('either_signed'), literal(1), literal(0))),
    ('right_size', un('SizeInBits',
        bin('UDiv', un('Abs', ref('right')),
            if_expr(ref('either_signed'), literal(4), literal(2))))),
    ('left_minus_right', if_expr(
        bin('SLessThan', ref('left_size'), ref('right_size')),
        literal(0),
        bin('Sub', ref('left_size'), ref('right_size'))))
    ],
    bin('Add',
        ref('signed_adjust'),
        if_expr(bin('Equal', ref('right'), literal(0)),
            literal(0),
            bin('UDiv', ref('left_minus_right'), literal(4))))
    ))

sdiv_lat_expr64 = expr_top(let([
    ('left', un('SignExtend32To64', int_reg(src(0)))),
    ('right', un('SignExtend32To64', int_reg(src(1)))),
    ('either_signed', bin('Or',
        bin('SLessThan', ref('left'), literal(0)),
        bin('SLessThan', ref('right'), literal(0)))),
    ('left_size', un('SizeInBits', un('Abs', ref('left')))),
    ('signed_adjust', if_expr(ref('either_signed'), literal(1), literal(0))),
    ('right_size', un('SizeInBits',
        bin('UDiv', un('Abs', ref('right')),
            if_expr(ref('either_signed'), literal(4), literal(2))))),
    ('left_minus_right', if_expr(
        bin('SLessThan', ref('left_size'), ref('right_size')),
        literal(0),
        bin('Sub', ref('left_size'), ref('right_size'))))
    ],
    bin('Add',
        ref('signed_adjust'),
        if_expr(bin('Equal', ref('right'), literal(0)),
            literal(0),
            bin('UDiv', ref('left_minus_right'), literal(4))))
    ))

class CortexA53_SDIV_A1(MinorFUTiming):
    description = 'HPI_SDIV_A1'
    mask, match = a32_opcode('xxxx_0111_0001_xxxx__xxxx_xxxx_0001_xxxx')
    extraCommitLat = 0
    srcRegsRelativeLats = []
    extraCommitLatExpr = sdiv_lat_expr

class CortexA53_SDIV_A64(MinorFUTiming):
    description = 'HPI_SDIV_A64'
    mask, match = a64_opcode('x001_1010_110x_xxxx__0000_11xx_xxxx_xxxx')
    extraCommitLat = 0
    srcRegsRelativeLats = []
    extraCommitLatExpr = sdiv_lat_expr64

### SEL

class CortexA53_SEL_A1(MinorFUTiming):
    description = 'HPI_SEL_A1'
    mask, match = a32_opcode('xxxx_0110_1000_xxxx__xxxx_xxxx_1011_xxxx')
    srcRegsRelativeLats = [0, 0, 0, 0, 2, 2, 0]

class CortexA53_SEL_A1_Suppress(MinorFUTiming):
    description = 'HPI_SEL_A1_Suppress'
    mask, match = a32_opcode('xxxx_0110_1000_xxxx__xxxx_xxxx_1011_xxxx')
    srcRegsRelativeLats = []
    suppress = True

class CortexA53_SHSAX_SSAX_UHSAX_USAX_A1(MinorFUTiming):
    description = 'HPI_SHSAX_SSAX_UHSAX_USAX_A1'
    mask, match = a32_opcode('xxxx_0110_0xx1_xxxx__xxxx_xxxx_0101_xxxx')
    # As Default
    srcRegsRelativeLats = [3, 3, 2, 2, 2, 1, 0]

class CortexA53_USUB_ETC_A1(MinorFUTiming):
    description = 'HPI_USUB_ETC_A1'
    mask, match = a32_opcode('xxxx_0110_0xx1_xxxx__xxxx_xxxx_x111_xxxx')
    srcRegsRelativeLats = [0, 0, 0, 2, 2, 0]

class CortexA53_SMLABB_T1(MinorFUTiming):
    description = 'HPI_SMLABB_T1'
    mask, match = t32_opcode('1111_1011_0001_xxxx__xxxx_xxxx_00xx_xxxx')
    srcRegsRelativeLats = [0, 0, 0, 0, 0, 2, 0]

class CortexA53_SMLABB_A1(MinorFUTiming):
    description = 'HPI_SMLABB_A1'
    mask, match = a32_opcode('xxxx_0001_0000_xxxx__xxxx_xxxx_1xx0_xxxx')
    srcRegsRelativeLats = [0, 0, 0, 0, 0, 2, 0]

class CortexA53_SMLAD_T1(MinorFUTiming):
    description = 'HPI_SMLAD_T1'
    mask, match = t32_opcode('1111_1011_0010_xxxx__xxxx_xxxx_000x_xxxx')
    srcRegsRelativeLats = [0, 0, 0, 0, 0, 2, 0]

class CortexA53_SMLAD_A1(MinorFUTiming):
    description = 'HPI_SMLAD_A1'
    mask, match = a32_opcode('xxxx_0111_0000_xxxx__xxxx_xxxx_00x1_xxxx')
    # z, z, z, l, r, a
    srcRegsRelativeLats = [0, 0, 0, 0, 0, 2, 0]

class CortexA53_SMLAL_T1(MinorFUTiming):
    description = 'HPI_SMLAL_T1'
    mask, match = t32_opcode('1111_1011_1100_xxxx__xxxx_xxxx_0000_xxxx')
class CortexA53_SMLAL_A1(MinorFUTiming):
    description = 'HPI_SMLAL_A1'
    mask, match = a32_opcode('xxxx_0000_111x_xxxx__xxxx_xxxx_1001_xxxx')

class CortexA53_SMLALBB_T1(MinorFUTiming):
    description = 'HPI_SMLALBB_T1'
    mask, match = t32_opcode('1111_1011_1100_xxxx__xxxx_xxxx_10xx_xxxx')
class CortexA53_SMLALBB_A1(MinorFUTiming):
    description = 'HPI_SMLALBB_A1'
    mask, match = a32_opcode('xxxx_0001_0100_xxxx__xxxx_xxxx_1xx0_xxxx')

class CortexA53_SMLALD_T1(MinorFUTiming):
    description = 'HPI_SMLALD_T1'
    mask, match = t32_opcode('1111_1011_1100_xxxx__xxxx_xxxx_110x_xxxx')
class CortexA53_SMLALD_A1(MinorFUTiming):
    description = 'HPI_SMLALD_A1'
    mask, match = a32_opcode('xxxx_0111_0100_xxxx__xxxx_xxxx_00x1_xxxx')

class CortexA53_SMLAWB_T1(MinorFUTiming):
    description = 'HPI_SMLAWB_T1'
    mask, match = t32_opcode('1111_1011_0011_xxxx__xxxx_xxxx_000x_xxxx')
    srcRegsRelativeLats = [0, 0, 0, 0, 0, 2, 0]

class CortexA53_SMLAWB_A1(MinorFUTiming):
    description = 'HPI_SMLAWB_A1'
    mask, match = a32_opcode('xxxx_0001_0010_xxxx__xxxx_xxxx_1x00_xxxx')
    srcRegsRelativeLats = [0, 0, 0, 0, 0, 2, 0]

class CortexA53_SMLSD_A1(MinorFUTiming):
    description = 'HPI_SMLSD_A1'
    mask, match = a32_opcode('xxxx_0111_0000_xxxx__xxxx_xxxx_01x1_xxxx')

class CortexA53_SMLSLD_T1(MinorFUTiming):
    description = 'HPI_SMLSLD_T1'
    mask, match = t32_opcode('1111_1011_1101_xxxx__xxxx_xxxx_110x_xxxx')
class CortexA53_SMLSLD_A1(MinorFUTiming):
    description = 'HPI_SMLSLD_A1'
    mask, match = a32_opcode('xxxx_0111_0100_xxxx__xxxx_xxxx_01x1_xxxx')

class CortexA53_SMMLA_T1(MinorFUTiming):
    description = 'HPI_SMMLA_T1'
    mask, match = t32_opcode('1111_1011_0101_xxxx__xxxx_xxxx_000x_xxxx')
    #                                              ^^^^ != 1111
    srcRegsRelativeLats = [0, 0, 0, 2, 0, 0, 0]

class CortexA53_SMMLA_A1(MinorFUTiming):
    description = 'HPI_SMMLA_A1'
    # Note that this must be after the encoding for SMMUL
    mask, match = a32_opcode('xxxx_0111_0101_xxxx__xxxx_xxxx_00x1_xxxx')
    #                                              ^^^^ != 1111
    srcRegsRelativeLats = [0, 0, 0, 2, 0, 0, 0]

class CortexA53_SMMLS_T1(MinorFUTiming):
    description = 'HPI_SMMLS_T1'
    mask, match = t32_opcode('1111_1011_0110_xxxx__xxxx_xxxx_000x_xxxx')
    srcRegsRelativeLats = [0, 0, 0, 2, 0, 0, 0]

class CortexA53_SMMLS_A1(MinorFUTiming):
    description = 'HPI_SMMLS_A1'
    mask, match = a32_opcode('xxxx_0111_0101_xxxx__xxxx_xxxx_11x1_xxxx')
    srcRegsRelativeLats = [0, 0, 0, 2, 0, 0, 0]

class CortexA53_SMMUL_T1(MinorFUTiming):
    description = 'HPI_SMMUL_T1'
    mask, match = t32_opcode('1111_1011_0101_xxxx__1111_xxxx_000x_xxxx')
    srcRegsRelativeLats = [0, 0, 0, 0, 0, 0]

class CortexA53_SMMUL_A1(MinorFUTiming):
    description = 'HPI_SMMUL_A1'
    mask, match = a32_opcode('xxxx_0111_0101_xxxx__1111_xxxx_00x1_xxxx')
    srcRegsRelativeLats = [0, 0, 0, 0, 0, 0]

class CortexA53_SMUAD_T1(MinorFUTiming):
    description = 'HPI_SMUAD_T1'
    mask, match = t32_opcode('1111_1011_0010_xxxx__1111_xxxx_000x_xxxx')
class CortexA53_SMUAD_A1(MinorFUTiming):
    description = 'HPI_SMUAD_A1'
    mask, match = a32_opcode('xxxx_0111_0000_xxxx__1111_xxxx_00x1_xxxx')

class CortexA53_SMULBB_T1(MinorFUTiming):
    description = 'HPI_SMULBB_T1'
    mask, match = t32_opcode('1111_1011_0001_xxxx__1111_xxxx_00xx_xxxx')
class CortexA53_SMULBB_A1(MinorFUTiming):
    description = 'HPI_SMULBB_A1'
    mask, match = a32_opcode('xxxx_0001_0110_xxxx__xxxx_xxxx_1xx0_xxxx')

class CortexA53_SMULL_T1(MinorFUTiming):
    description = 'HPI_SMULL_T1'
    mask, match = t32_opcode('1111_1011_1000_xxxx__xxxx_xxxx_0000_xxxx')
class CortexA53_SMULL_A1(MinorFUTiming):
    description = 'HPI_SMULL_A1'
    mask, match = a32_opcode('xxxx_0000_110x_xxxx__xxxx_xxxx_1001_xxxx')

class CortexA53_SMULWB_T1(MinorFUTiming):
    description = 'HPI_SMULWB_T1'
    mask, match = t32_opcode('1111_1011_0011_xxxx__1111_xxxx_000x_xxxx')
class CortexA53_SMULWB_A1(MinorFUTiming):
    description = 'HPI_SMULWB_A1'
    mask, match = a32_opcode('xxxx_0001_0010_xxxx__xxxx_xxxx_1x10_xxxx')

class CortexA53_SMUSD_T1(MinorFUTiming):
    description = 'HPI_SMUSD_T1'
    mask, match = t32_opcode('1111_1011_0100_xxxx__1111_xxxx_000x_xxxx')
class CortexA53_SMUSD_A1(MinorFUTiming):
    description = 'HPI_SMUSD_A1'
    mask, match = a32_opcode('xxxx_0111_0000_xxxx__1111_xxxx_01x1_xxxx')

class CortexA53_SSAT_USAT_no_shift_A1(MinorFUTiming):
    description = 'HPI_SSAT_USAT_no_shift_A1'
    # Order *before* shift
    mask, match = a32_opcode('xxxx_0110_1x1x_xxxx__xxxx_0000_0001_xxxx')
    srcRegsRelativeLats = [0, 0, 0, 2, 0]

class CortexA53_SSAT_USAT_shift_A1(MinorFUTiming):
    description = 'HPI_SSAT_USAT_shift_A1'
    # Order after shift
    mask, match = a32_opcode('xxxx_0110_1x1x_xxxx__xxxx_xxxx_xx01_xxxx')
    srcRegsRelativeLats = [0, 0, 0, 1, 0]

class CortexA53_SSAT16_USAT16_A1(MinorFUTiming):
    description = 'HPI_SSAT16_USAT16_A1'
    mask, match = a32_opcode('xxxx_0110_1x10_xxxx__xxxx_xxxx_0011_xxxx')
    srcRegsRelativeLats = [0, 0, 0, 2, 0]

class CortexA53_SXTAB_T1(MinorFUTiming):
    description = 'HPI_SXTAB_T1'
    mask, match = t32_opcode('1111_1010_0100_xxxx__1111_xxxx_1xxx_xxxx')
    srcRegsRelativeLats = [0, 0, 0, 1, 2, 0]

class CortexA53_SXTAB_SXTAB16_SXTAH_UXTAB_UXTAB16_UXTAH_A1(MinorFUTiming):
    description = 'HPI_SXTAB_SXTAB16_SXTAH_UXTAB_UXTAB16_UXTAH_A1'
    # Place AFTER CortexA53_SXTB_SXTB16_SXTH_UXTB_UXTB16_UXTH_A1
    # e6[9d][^f]0070 are undefined
    mask, match = a32_opcode('xxxx_0110_1xxx_xxxx__xxxx_xxxx_0111_xxxx')
    srcRegsRelativeLats = [0, 0, 0, 1, 2, 0]

class CortexA53_SXTAB16_T1(MinorFUTiming):
    description = 'HPI_SXTAB16_T1'
    mask, match = t32_opcode('1111_1010_0010_xxxx__1111_xxxx_1xxx_xxxx')
    srcRegsRelativeLats = [0, 0, 0, 1, 2, 0]

class CortexA53_SXTAH_T1(MinorFUTiming):
    description = 'HPI_SXTAH_T1'
    mask, match = t32_opcode('1111_1010_0000_xxxx__1111_xxxx_1xxx_xxxx')
    srcRegsRelativeLats = [0, 0, 0, 1, 2, 0]

class CortexA53_SXTB_T1(MinorFUTiming):
    description = 'HPI_SXTB_T1'
    mask, match = t16_opcode('1011_0010_01xx_xxxx')
class CortexA53_SXTB_T2(MinorFUTiming):
    description = 'HPI_SXTB_T2'
    mask, match = t32_opcode('1111_1010_0100_1111__1111_xxxx_1xxx_xxxx')
    srcRegsRelativeLats = [0, 0, 0, 1, 2, 0]

class CortexA53_SXTB_SXTB16_SXTH_UXTB_UXTB16_UXTH_A1(MinorFUTiming):
    description = 'HPI_SXTB_SXTB16_SXTH_UXTB_UXTB16_UXTH_A1'
    # e6[9d]f0070 are undefined
    mask, match = a32_opcode('xxxx_0110_1xxx_1111__xxxx_xxxx_0111_xxxx')
    srcRegsRelativeLats = [0, 0, 0, 2, 0]

class CortexA53_SXTB16_T1(MinorFUTiming):
    description = 'HPI_SXTB16_T1'
    mask, match = t32_opcode('1111_1010_0010_1111__1111_xxxx_1xxx_xxxx')
    srcRegsRelativeLats = [0, 0, 0, 1, 2, 0]

class CortexA53_SXTH_T1(MinorFUTiming):
    description = 'HPI_SXTH_T1'
    mask, match = t16_opcode('1011_0010_00xx_xxxx')
class CortexA53_SXTH_T2(MinorFUTiming):
    description = 'HPI_SXTH_T2'
    mask, match = t32_opcode('1111_1010_0000_1111__1111_xxxx_1xxx_xxxx')
    srcRegsRelativeLats = [0, 0, 0, 1, 2, 0]

class CortexA53_UDIV_T1(MinorFUTiming):
    description = 'HPI_UDIV_T1'
    mask, match = t32_opcode('1111_1011_1011_xxxx__xxxx_xxxx_1111_xxxx')

udiv_lat_expr = expr_top(let([
    ('left', int_reg(src(4))),
    ('right', int_reg(src(3))),
    ('left_size', un('SizeInBits', ref('left'))),
    ('right_size', un('SizeInBits',
        bin('UDiv', ref('right'), literal(2)))),
    ('left_minus_right', if_expr(
        bin('SLessThan', ref('left_size'), ref('right_size')),
        literal(0),
        bin('Sub', ref('left_size'), ref('right_size'))))
    ],
    if_expr(bin('Equal', ref('right'), literal(0)),
        literal(0),
        bin('UDiv', ref('left_minus_right'), literal(4)))
    ))

class CortexA53_UDIV_A1(MinorFUTiming):
    description = 'HPI_UDIV_A1'
    mask, match = a32_opcode('xxxx_0111_0011_xxxx__xxxx_xxxx_0001_xxxx')
    extraCommitLat = 0
    srcRegsRelativeLats = []
    extraCommitLatExpr = udiv_lat_expr

class CortexA53_UMAAL_T1(MinorFUTiming):
    description = 'HPI_UMAAL_T1'
    mask, match = t32_opcode('1111_1011_1110_xxxx__xxxx_xxxx_0110_xxxx')
    # z, z, z, dlo, dhi, l, r
    extraCommitLat = 1
    srcRegsRelativeLats = [0, 0, 0, 0, 0, 0, 0, 0]

class CortexA53_UMAAL_A1(MinorFUTiming):
    description = 'HPI_UMAAL_A1'
    mask, match = a32_opcode('xxxx_0000_0100_xxxx__xxxx_xxxx_1001_xxxx')
    # z, z, z, dlo, dhi, l, r
    extraCommitLat = 1
    srcRegsRelativeLats = [0, 0, 0, 0, 0, 0, 0, 0]

class CortexA53_UMLAL_T1(MinorFUTiming):
    description = 'HPI_UMLAL_T1'
    mask, match = t32_opcode('1111_1011_1110_xxxx__xxxx_xxxx_0000_xxxx')

class CortexA53_UMLAL_A1(MinorFUTiming):
    description = 'HPI_UMLAL_A1'
    mask, match = t32_opcode('xxxx_0000_101x_xxxx__xxxx_xxxx_1001_xxxx')

class CortexA53_UMULL_T1(MinorFUTiming):
    description = 'HPI_UMULL_T1'
    mask, match = t32_opcode('1111_1011_1010_xxxx__xxxx_xxxx_0000_xxxx')

class CortexA53_UMULL_A1(MinorFUTiming):
    description = 'HPI_UMULL_A1'
    mask, match = a32_opcode('xxxx_0000_100x_xxxx__xxxx_xxxx_1001_xxxx')

class CortexA53_USAD8_USADA8_A1(MinorFUTiming):
    description = 'HPI_USAD8_USADA8_A1'
    mask, match = a32_opcode('xxxx_0111_1000_xxxx__xxxx_xxxx_0001_xxxx')
    srcRegsRelativeLats = [0, 0, 0, 0, 0, 2, 0]

class CortexA53_USAD8_USADA8_A1_Suppress(MinorFUTiming):
    description = 'HPI_USAD8_USADA8_A1_Suppress'
    mask, match = a32_opcode('xxxx_0111_1000_xxxx__xxxx_xxxx_0001_xxxx')
    srcRegsRelativeLats = []
    suppress = True

class CortexA53_VMOV_immediate_A1(MinorFUTiming):
    description = 'HPI_VMOV_register_A1'
    mask, match = a32_opcode('1111_0010_0x10_xxxx_xxxx_0001_xxx1_xxxx')
    # cpsr, z, z, z, hcptr, nsacr, cpacr, fpexc, scr
    srcRegsRelativeLats = [5, 5, 5, 5, 5, 5, 5, 5, 5, 0]

class CortexA53_VMRS_A1(MinorFUTiming):
    description = 'HPI_VMRS_A1'
    mask, match = a32_opcode('xxxx_1110_1111_0001_xxxx_1010_xxx1_xxxx')
    # cpsr,z,z,z,hcptr,nsacr,cpacr,scr,r42
    srcRegsRelativeLats = [5, 5, 5, 5, 5, 5, 5, 5, 5, 0]

class CortexA53_VMOV_register_A2(MinorFUTiming):
    description = 'HPI_VMOV_register_A2'
    mask, match = a32_opcode('xxxx_1110_1x11_0000_xxxx_101x_01x0_xxxx')
    # cpsr, z, r39, z, hcptr, nsacr, cpacr, fpexc, scr, f4, f5, f0, f1
    srcRegsRelativeLats = \
        [5, 5, 5, 5, 5, 5, 5, 5, 5, 4, 4, 4, 4, 4, 4, 4, 4, 0]

# VADD.I16 D/VADD.F32 D/VADD.I8 D/VADD.I32 D
class CortexA53_VADD2H_A32(MinorFUTiming):
    description = 'Vadd2hALU'
    mask, match = a32_opcode('1111_0010_0xxx_xxxx__xxxx_1000_xxx0_xxxx')
    # cpsr, z, z, z, cpacr, fpexc, l0, r0, l1, r1, l2, r2, l3, r3 (for vadd2h)
    srcRegsRelativeLats = [0, 0, 0, 0, 0, 0,  4, 4, 4, 4, 4, 4, 4, 4, 0]

# VAQQHN.I16 Q/VAQQHN.I32 Q/VAQQHN.I64 Q
class CortexA53_VADDHN_A32(MinorFUTiming):
    description = 'VaddhnALU'
    mask, match = a32_opcode('1111_0010_1xxx_xxxx__xxxx_0100_x0x0_xxxx')
    # cpsr, z, z, z, cpacr, fpexc, l0, l1, l2, l3, r0, r1, r2, r3
    srcRegsRelativeLats = [0, 0, 0, 0, 0, 0,  3, 3, 3, 3, 3, 3, 3, 3, 0]

class CortexA53_VADDL_A32(MinorFUTiming):
    description = 'VaddlALU'
    mask, match = a32_opcode('1111_001x_1xxx_xxxx__xxxx_0000_x0x0_xxxx')
    srcRegsRelativeLats = [0, 0, 0, 0, 0, 0,  3, 3, 3, 3, 3, 3, 3, 3, 0]

class CortexA53_VADDW_A32(MinorFUTiming):
    description = 'HPI_VADDW_A32'
    mask, match = a32_opcode('1111_001x_1xxx_xxxx__xxxx_0001_x0x0_xxxx')
    # cpsr, z, z, z, cpacr, fpexc, l0, l1, l2, l3, r0, r1
    srcRegsRelativeLats = [0, 0, 0, 0, 0, 0,  4, 4, 4, 4, 3, 3, 0]

# VHADD/VHSUB S8,S16,S32,U8,U16,U32 Q and D
class CortexA53_VHADD_A32(MinorFUTiming):
    description = 'HPI_VHADD_A32'
    mask, match = a32_opcode('1111_001x_0xxx_xxxx__xxxx_00x0_xxx0_xxxx')
    srcRegsRelativeLats = [0, 0, 0, 0, 0, 0,  4, 4, 4, 4, 4, 4, 4, 4, 0]

class CortexA53_VPADAL_A32(MinorFUTiming):
    description = 'VpadalALU'
    mask, match = a32_opcode('1111_0011_1x11_xx00__xxxx_0110_xxx0_xxxx')
    srcRegsRelativeLats = [0, 0, 0, 0, 0, 0,  2, 2, 2, 2, 2, 2, 2, 2, 0]

# VPADDH.I16
class CortexA53_VPADDH_A32(MinorFUTiming):
    description = 'VpaddhALU'
    mask, match = a32_opcode('1111_0010_0xxx_xxxx__xxxx_1011_xxx1_xxxx')
    srcRegsRelativeLats = [0, 0, 0, 0, 0, 0,  3, 3, 3, 3, 3, 3, 3, 3, 0]

# VPADDH.F32
class CortexA53_VPADDS_A32(MinorFUTiming):
    description = 'VpaddsALU'
    mask, match = a32_opcode('1111_0011_0x0x_xxxx__xxxx_1101_xxx0_xxxx')
    srcRegsRelativeLats = [0, 0, 0, 0, 0, 0,  2, 2, 2, 2, 2, 2, 2, 2, 0]

# VPADDL.S16
class CortexA53_VPADDL_A32(MinorFUTiming):
    description = 'VpaddlALU'
    mask, match = a32_opcode('1111_0011_1x11_xx00__xxxx_0010_xxx0_xxxx')
    srcRegsRelativeLats = [0, 0, 0, 0, 0, 0,  3, 3, 3, 3, 3, 3, 3, 3, 0]

# VRADDHN.I16
class CortexA53_VRADDHN_A32(MinorFUTiming):
    description = 'HPI_VRADDHN_A32'
    mask, match = a32_opcode('1111_0011_1xxx_xxxx__xxxx_0100_x0x0_xxxx')
    # cpsr, z, z, z, cpacr, fpexc, l0, l1, l2, l3, r0, r1, r2, r3
    srcRegsRelativeLats = [0, 0, 0, 0, 0, 0,  4, 4, 4, 4, 4, 4, 4, 4, 0]

class CortexA53_VRHADD_A32(MinorFUTiming):
    description = 'VrhaddALU'
    mask, match = a32_opcode('1111_001x_0xxx_xxxx__xxxx_0001_xxx0_xxxx')
    srcRegsRelativeLats = [0, 0, 0, 0, 0, 0,  4, 4, 4, 4, 4, 4, 4, 4, 0]

class CortexA53_VQADD_A32(MinorFUTiming):
    description = 'VqaddALU'
    mask, match = a32_opcode('1111_001x_0xxx_xxxx__xxxx_0000_xxx1_xxxx')
    srcRegsRelativeLats = [0, 0, 0, 0, 0, 0,  3, 3, 3, 3, 3, 3, 3, 3, 0]

class CortexA53_VANDQ_A32(MinorFUTiming):
    description = 'VandqALU'
    mask, match = a32_opcode('1111_0010_0x00_xxxx__xxxx_0001_xxx1_xxxx')
    srcRegsRelativeLats = [0, 0, 0, 0, 0, 0,  5, 5, 5, 5, 5, 5, 5, 5, 0]

# VMUL (integer)
class CortexA53_VMULI_A32(MinorFUTiming):
    description = 'VmuliALU'
    mask, match = a32_opcode('1111_001x_0xxx_xxxx__xxxx_1001_xxx1_xxxx')
    srcRegsRelativeLats = [0, 0, 0, 0, 0, 0,  2, 2, 2, 2, 2, 2, 2, 2, 0]

# VBIC (reg)
class CortexA53_VBIC_A32(MinorFUTiming):
    description = 'VbicALU'
    mask, match = a32_opcode('1111_0010_0x01_xxxx__xxxx_0001_xxx1_xxxx')
    srcRegsRelativeLats = [0, 0, 0, 0, 0, 0,  5, 5, 5, 5, 5, 5, 5, 5, 0]

# VBIF VBIT VBSL
class CortexA53_VBIF_ETC_A32(MinorFUTiming):
    description = 'VbifALU'
    mask, match = a32_opcode('1111_0011_0xxx_xxxx__xxxx_0001_xxx1_xxxx')
    srcRegsRelativeLats = \
        [0, 0, 0, 0, 0, 0,  5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 0]

class CortexA53_VACGE_A32(MinorFUTiming):
    description = 'VacgeALU'
    mask, match = a32_opcode('1111_0011_0xxx_xxxx__xxxx_1110_xxx1_xxxx')
    srcRegsRelativeLats = [0, 0, 0, 0, 0, 0,  4, 4, 4, 4, 4, 4, 4, 4, 4, 0]

# VCEQ.F32
class CortexA53_VCEQ_A32(MinorFUTiming):
    description = 'VceqALU'
    mask, match = a32_opcode('1111_0010_0x0x_xxxx__xxxx_1110_xxx0_xxxx')
    srcRegsRelativeLats = [0, 0, 0, 0, 0, 0,  4, 4, 4, 4, 4, 4, 4, 4, 4, 0]

# VCEQ.[IS]... register
class CortexA53_VCEQI_A32(MinorFUTiming):
    description = 'VceqiALU'
    mask, match = a32_opcode('1111_0011_0xxx_xxxx__xxxx_1000_xxx1_xxxx')
    srcRegsRelativeLats = [0, 0, 0, 0, 0, 0,  4, 4, 4, 4, 4, 4, 4, 4, 4, 0]

# VCEQ.[IS]... immediate
class CortexA53_VCEQII_A32(MinorFUTiming):
    description = 'HPI_VCEQII_A32'
    mask, match = a32_opcode('1111_0011_1x11_xx01__xxxx_0x01_0xx0_xxxx')
    srcRegsRelativeLats = [0, 0, 0, 0, 0, 0,  4, 4, 4, 4, 4, 4, 4, 4, 4, 0]

class CortexA53_VTST_A32(MinorFUTiming):
    description = 'HPI_VTST_A32'
    mask, match = a32_opcode('1111_0010_0xxx_xxxx__xxxx_1000_xxx1_xxxx')
    srcRegsRelativeLats = [0, 0, 0, 0, 0, 0,  3, 3, 3, 3, 3, 3, 3, 3, 3, 0]

class CortexA53_VCLZ_A32(MinorFUTiming):
    description = 'HPI_VCLZ_A32'
    mask, match = a32_opcode('1111_0011_1x11_xx00__xxxx_0100_1xx0_xxxx')
    srcRegsRelativeLats = [0, 0, 0, 0, 0, 0,  4, 4, 4, 4, 4, 4, 4, 4, 4, 0]

class CortexA53_VCNT_A32(MinorFUTiming):
    description = 'HPI_VCNT_A32'
    mask, match = a32_opcode('1111_0011_1x11_xx00__xxxx_0101_0xx0_xxxx')
    srcRegsRelativeLats = [0, 0, 0, 0, 0, 0,  4, 4, 4, 4, 4, 4, 4, 4, 4, 0]

class CortexA53_VEXT_A32(MinorFUTiming):
    description = 'HPI_VCNT_A32'
    mask, match = a32_opcode('1111_0010_1x11_xxxx__xxxx_xxxx_xxx0_xxxx')
    srcRegsRelativeLats = [0, 0, 0, 0, 0, 0,  4, 4, 4, 4, 4, 4, 4, 4, 4, 0]

# VMAX VMIN integer
class CortexA53_VMAXI_A32(MinorFUTiming):
    description = 'HPI_VMAXI_A32'
    mask, match = a32_opcode('1111_001x_0xxx_xxxx__xxxx_0110_xxxx_xxxx')
    srcRegsRelativeLats = [0, 0, 0, 0, 0, 0,  4, 4, 4, 4, 4, 4, 4, 4, 4, 0]

# VMAX VMIN float
class CortexA53_VMAXS_A32(MinorFUTiming):
    description = 'HPI_VMAXS_A32'
    mask, match = a32_opcode('1111_0010_0xxx_xxxx__xxxx_1111_xxx0_xxxx')
    srcRegsRelativeLats = [0, 0, 0, 0, 0, 0,  2, 2, 2, 2, 2, 2, 2, 2, 2, 0]

# VNEG integer
class CortexA53_VNEGI_A32(MinorFUTiming):
    description = 'HPI_VNEGI_A32'
    mask, match = a32_opcode('1111_0011_1x11_xx01__xxxx_0x11_1xx0_xxxx')
    srcRegsRelativeLats = [0, 0, 0, 0, 0, 0,  4, 4, 4, 4, 4, 4, 4, 4, 4, 0]

# VNEG float
class CortexA53_VNEGF_A32(MinorFUTiming):
    description = 'HPI_VNEGF_A32'
    mask, match = a32_opcode('xxxx_1110_1x11_0001__xxxx_101x_01x0_xxxx')
    srcRegsRelativeLats = [0, 0, 0, 0, 0, 0,  2, 2, 2, 2, 2, 2, 2, 2, 2, 0]

# VREV16 VREV32 VREV64
class CortexA53_VREVN_A32(MinorFUTiming):
    description = 'HPI_VREVN_A32'
    mask, match = a32_opcode('1111_0011_1x11_xx00__xxxx_000x_xxx0_xxxx')
    srcRegsRelativeLats = [0, 0, 0, 0, 0, 0,  4, 4, 4, 4, 4, 4, 4, 4, 4, 0]

class CortexA53_VQNEG_A32(MinorFUTiming):
    description = 'HPI_VQNEG_A32'
    mask, match = a32_opcode('1111_0011_1x11_xx00__xxxx_0111_1xx0_xxxx')
    srcRegsRelativeLats = [0, 0, 0, 0, 0, 0,  3, 3, 3, 3, 3, 3, 3, 3, 3, 0]

class CortexA53_VSWP_A32(MinorFUTiming):
    description = 'HPI_VSWP_A32'
    mask, match = a32_opcode('1111_0011_1x11_xx10__xxxx_0000_0xx0_xxxx')
    srcRegsRelativeLats = [0, 0, 0, 0, 0, 0,  4, 4, 4, 4, 4, 4, 4, 4, 0]

class CortexA53_VTRN_A32(MinorFUTiming):
    description = 'HPI_VTRN_A32'
    mask, match = a32_opcode('1111_0011_1x11_xx10__xxxx_0000_1xx0_xxxx')
    # cpsr, z, z, z, cpact, fpexc, o0, d0, o1, d1, o2, d2, o3, d3
    srcRegsRelativeLats = [0, 0, 0, 0, 0, 0,  2, 2, 2, 2, 2, 2, 2, 2, 0]

# VQMOVN VQMOVUN
class CortexA53_VQMOVN_A32(MinorFUTiming):
    description = 'HPI_VQMOVN_A32'
    mask, match = a32_opcode('1111_0011_1x11_xx10__xxxx_0010_xxx0_xxxx')
    # cpsr, z, z, z, cpact, fpexc, o[0], o[1], o[2], o[3], fpscr
    srcRegsRelativeLats = [0, 0, 0, 0, 0, 0,  2, 2, 2, 2,  2, 0]

# VUZP double word
class CortexA53_VUZP_A32(MinorFUTiming):
    description = 'HPI_VUZP_A32'
    mask, match = a32_opcode('1111_0011_1x11_xx10__xxxx_0001_00x0_xxxx')
    srcRegsRelativeLats = [0, 0, 0, 0, 0, 0,  3, 3, 3, 3, 3, 3, 3, 3, 0]

# VDIV.F32
class CortexA53_VDIV32_A32(MinorFUTiming):
    description = 'HPI_VDIV32_A32'
    mask, match = a32_opcode('xxxx_1110_1x00_xxxx__xxxx_1010_x0x0_xxxx')
    # cpsr, z, z, z, cpact, fpexc, fpscr_exc, l, r
    extraCommitLat = 9
    srcRegsRelativeLats = [0, 0, 0, 0, 0, 0, 20,  4, 4, 0]

# VDIV.F64
class CortexA53_VDIV64_A32(MinorFUTiming):
    description = 'HPI_VDIV64_A32'
    mask, match = a32_opcode('xxxx_1110_1x00_xxxx__xxxx_1011_x0x0_xxxx')
    # cpsr, z, z, z, cpact, fpexc, fpscr_exc, l, r
    extraCommitLat = 18
    srcRegsRelativeLats = [0, 0, 0, 0, 0, 0, 20,  4, 4, 0]

class CortexA53_VZIP_A32(MinorFUTiming):
    description = 'HPI_VZIP_A32'
    mask, match = a32_opcode('1111_0011_1x11_xx10__xxxx_0001_1xx0_xxxx')
    srcRegsRelativeLats = [0, 0, 0, 0, 0, 0,  4, 4, 4, 4, 4, 4, 4, 4, 0]

# VPMAX integer
class CortexA53_VPMAX_A32(MinorFUTiming):
    description = 'HPI_VPMAX_A32'
    mask, match = a32_opcode('1111_001x_0xxx_xxxx__xxxx_1010_xxxx_xxxx')
    # cpsr, z, z, z, cpact, fpexc, l0, r0, l1, r1, fpscr
    srcRegsRelativeLats = [0, 0, 0, 0, 0, 0,  4, 4, 4, 4,  4, 0]

# VPMAX float
class CortexA53_VPMAXF_A32(MinorFUTiming):
    description = 'HPI_VPMAXF_A32'
    mask, match = a32_opcode('1111_0011_0xxx_xxxx__xxxx_1111_xxx0_xxxx')
    srcRegsRelativeLats = [0, 0, 0, 0, 0, 0,  2, 2, 2, 2, 0]

class CortexA53_VMOVN_A32(MinorFUTiming):
    description = 'HPI_VMOVN_A32'
    mask, match = a32_opcode('1111_0011_1x11_xx10__xxxx_0010_00x0_xxxx')
    srcRegsRelativeLats = [0, 0, 0, 0, 0, 0,  4, 4, 4, 4, 0]

class CortexA53_VMOVL_A32(MinorFUTiming):
    description = 'HPI_VMOVL_A32'
    mask, match = a32_opcode('1111_001x_1xxx_x000__xxxx_1010_00x1_xxxx')
    srcRegsRelativeLats = [0, 0, 0, 0, 0, 0,  4, 4, 4, 4, 0]

# VSQRT.F64
class CortexA53_VSQRT64_A32(MinorFUTiming):
    description = 'HPI_VSQRT64_A32'
    mask, match = a32_opcode('xxxx_1110_1x11_0001__xxxx_1011_11x0_xxxx')
    extraCommitLat = 18
    srcRegsRelativeLats = []

# VSQRT.F32
class CortexA53_VSQRT32_A32(MinorFUTiming):
    description = 'HPI_VSQRT32_A32'
    mask, match = a32_opcode('xxxx_1110_1x11_0001__xxxx_1010_11x0_xxxx')
    extraCommitLat = 9
    srcRegsRelativeLats = []

class CortexA53_FloatSimdFU(MinorFU):
    opClasses = minorMakeOpClassSet([
        'FloatAdd', 'FloatCmp', 'FloatCvt', 'FloatMult', 'FloatDiv',
        'FloatSqrt', 'FloatMisc', 'FloatMultAcc',
        'SimdAdd', 'SimdAddAcc', 'SimdAlu', 'SimdCmp', 'SimdCvt',
        'SimdMisc', 'SimdMult', 'SimdMultAcc', 'SimdShift', 'SimdShiftAcc',
        'SimdSqrt', 'SimdFloatAdd', 'SimdFloatAlu', 'SimdFloatCmp',
        'SimdFloatCvt', 'SimdFloatDiv', 'SimdFloatMisc', 'SimdFloatMult',
        'SimdFloatMultAcc', 'SimdFloatSqrt'])

    timings = [
        # VUZP and VZIP must be before VADDW/L
        CortexA53_VUZP_A32(), CortexA53_VZIP_A32(),
        CortexA53_VADD2H_A32(), CortexA53_VADDHN_A32(),
        CortexA53_VADDL_A32(), CortexA53_VADDW_A32(),
        CortexA53_VHADD_A32(), CortexA53_VPADAL_A32(),
        CortexA53_VPADDH_A32(), CortexA53_VPADDS_A32(),
        CortexA53_VPADDL_A32(), CortexA53_VRADDHN_A32(),
        CortexA53_VRHADD_A32(), CortexA53_VQADD_A32(),
        CortexA53_VANDQ_A32(), CortexA53_VBIC_A32(),
        CortexA53_VBIF_ETC_A32(), CortexA53_VACGE_A32(),
        CortexA53_VCEQ_A32(), CortexA53_VCEQI_A32(),
        CortexA53_VCEQII_A32(), CortexA53_VTST_A32(),
        CortexA53_VCLZ_A32(), CortexA53_VCNT_A32(),
        CortexA53_VEXT_A32(), CortexA53_VMAXI_A32(),
        CortexA53_VMAXS_A32(), CortexA53_VNEGI_A32(),
        CortexA53_VNEGF_A32(), CortexA53_VREVN_A32(),
        CortexA53_VQNEG_A32(), CortexA53_VSWP_A32(),
        CortexA53_VTRN_A32(), CortexA53_VPMAX_A32(),
        CortexA53_VPMAXF_A32(), CortexA53_VMOVN_A32(),
        CortexA53_VMRS_A1(),
        CortexA53_VMOV_immediate_A1(),
        CortexA53_VMOV_register_A2(),
        CortexA53_VQMOVN_A32(), CortexA53_VMOVL_A32(),
        CortexA53_VDIV32_A32(), CortexA53_VDIV64_A32(),
        CortexA53_VSQRT32_A32(), CortexA53_VSQRT64_A32(),
        CortexA53_VMULI_A32(),
        # Add before here
        CortexA53_FMADD_A64(),
        CortexA53_FMSUB_D_A64(),
        CortexA53_FMOV_A64(),
        CortexA53_ADD_SUB_vector_scalar_A64(),
        CortexA53_ADD_SUB_vector_vector_A64(),
        CortexA53_FDIV_scalar_32_A64(), CortexA53_FDIV_scalar_64_A64(),
        CortexA53_DefaultA64Vfp(),
        CortexA53_DefaultVfp()]

    opLat = 6

class CortexA53_IntFU(MinorFU):
    opClasses = minorMakeOpClassSet(['IntAlu'])
    # IMPORTANT! Keep the order below, add new entries *at the head*
    timings = [
        CortexA53_SSAT_USAT_no_shift_A1(),
        CortexA53_SSAT_USAT_shift_A1(),
        CortexA53_SSAT16_USAT16_A1(),
        CortexA53_QADD_QSUB_A1(),
        CortexA53_QADD_QSUB_T1(),
        CortexA53_QADD_ETC_A1(),
        CortexA53_QASX_QSAX_UQASX_UQSAX_T1(),
        CortexA53_QADD_ETC_T1(),
        CortexA53_USUB_ETC_A1(),
        CortexA53_ADD_ETC_A1(),
        CortexA53_ADD_ETC_T1(),
        CortexA53_QDADD_QDSUB_A1(),
        CortexA53_QDADD_QDSUB_T1(),
        CortexA53_SASX_SHASX_UASX_UHASX_A1(),
        CortexA53_SHSAX_SSAX_UHSAX_USAX_A1(),
        CortexA53_SXTB_SXTB16_SXTH_UXTB_UXTB16_UXTH_A1(),

        # Must be after CortexA53_SXTB_SXTB16_SXTH_UXTB_UXTB16_UXTH_A1
        CortexA53_SXTAB_SXTAB16_SXTAH_UXTAB_UXTAB16_UXTAH_A1(),

        CortexA53_SXTAB_T1(),
        CortexA53_SXTAB16_T1(),
        CortexA53_SXTAH_T1(),
        CortexA53_SXTB_T2(),
        CortexA53_SXTB16_T1(),
        CortexA53_SXTH_T2(),

        CortexA53_PKH_A1(),
        CortexA53_PKH_T1(),
        CortexA53_SBFX_UBFX_A1(),
        CortexA53_SEL_A1(),
        CortexA53_RBIT_A1(),
        CortexA53_REV_REV16_A1(),
        CortexA53_REVSH_A1(),
        CortexA53_USAD8_USADA8_A1(),
        CortexA53_BFI_A1(),
        CortexA53_BFI_T1(),

        CortexA53_CMN_register_A1(),
        CortexA53_CMN_immediate_A1(),
        CortexA53_CMP_register_A1(),
        CortexA53_CMP_immediate_A1(),

        CortexA53_DataProcessingNoShift(),
        CortexA53_DataProcessingMovShiftr(),
        CortexA53_DataProcessingMayShift(),

        CortexA53_Cxxx_A64(),

        CortexA53_DefaultA64Int(),
        CortexA53_DefaultInt()]
    opLat = 3

class CortexA53_Int2FU(MinorFU):
    opClasses = minorMakeOpClassSet(['IntAlu'])
    # IMPORTANT! Keep the order below, add new entries *at the head*
    timings = [
        CortexA53_SSAT_USAT_no_shift_A1(),
        CortexA53_SSAT_USAT_shift_A1(),
        CortexA53_SSAT16_USAT16_A1(),
        CortexA53_QADD_QSUB_A1(),
        CortexA53_QADD_QSUB_T1(),
        CortexA53_QADD_ETC_A1(),
        CortexA53_QASX_QSAX_UQASX_UQSAX_T1(),
        CortexA53_QADD_ETC_T1(),
        CortexA53_USUB_ETC_A1(),
        CortexA53_ADD_ETC_A1(),
        CortexA53_ADD_ETC_T1(),
        CortexA53_QDADD_QDSUB_A1(),
        CortexA53_QDADD_QDSUB_T1(),
        CortexA53_SASX_SHASX_UASX_UHASX_A1(),
        CortexA53_SHSAX_SSAX_UHSAX_USAX_A1(),
        CortexA53_SXTB_SXTB16_SXTH_UXTB_UXTB16_UXTH_A1(),

        # Must be after CortexA53_SXTB_SXTB16_SXTH_UXTB_UXTB16_UXTH_A1
        CortexA53_SXTAB_SXTAB16_SXTAH_UXTAB_UXTAB16_UXTAH_A1(),

        CortexA53_SXTAB_T1(),
        CortexA53_SXTAB16_T1(),
        CortexA53_SXTAH_T1(),
        CortexA53_SXTB_T2(),
        CortexA53_SXTB16_T1(),
        CortexA53_SXTH_T2(),

        CortexA53_PKH_A1(),
        CortexA53_PKH_T1(),
        CortexA53_SBFX_UBFX_A1(),
        CortexA53_SEL_A1_Suppress(),
        CortexA53_RBIT_A1(),
        CortexA53_REV_REV16_A1(),
        CortexA53_REVSH_A1(),
        CortexA53_USAD8_USADA8_A1_Suppress(),
        CortexA53_BFI_A1(),
        CortexA53_BFI_T1(),

        CortexA53_CMN_register_A1(), # Need to check for shift
        CortexA53_CMN_immediate_A1(),
        CortexA53_CMP_register_A1(), # Need to check for shift
        CortexA53_CMP_immediate_A1(),

        CortexA53_DataProcessingNoShift(),
        CortexA53_DataProcessingAllowShifti(),
        # CortexA53_DataProcessingAllowMovShiftr(),

        # Data processing ops that match SuppressShift but are *not*
        # to be suppressed here
        CortexA53_CLZ_A1(),
        CortexA53_CLZ_T1(),
        CortexA53_DataProcessingSuppressShift(),
        # Can you dual issue a branch?
        # CortexA53_DataProcessingSuppressBranch(),
        CortexA53_Cxxx_A64(),

        CortexA53_DefaultA64Int(),
        CortexA53_DefaultInt()]
    opLat = 3

class CortexA53_IntMulFU(MinorFU):
    opClasses = minorMakeOpClassSet(['IntMult'])
    timings = [
        CortexA53_MLA_A1(), CortexA53_MLA_T1(),
        CortexA53_MLS_A1(), CortexA53_MLS_T1(),
        CortexA53_SMLABB_A1(), CortexA53_SMLABB_T1(),
        CortexA53_SMLAWB_A1(), CortexA53_SMLAWB_T1(),
        CortexA53_SMLAD_A1(), CortexA53_SMLAD_T1(),
        CortexA53_SMMUL_A1(), CortexA53_SMMUL_T1(),
        # SMMUL_A1 must be before SMMLA_A1
        CortexA53_SMMLA_A1(), CortexA53_SMMLA_T1(),
        CortexA53_SMMLS_A1(), CortexA53_SMMLS_T1(),
        CortexA53_UMAAL_A1(), CortexA53_UMAAL_T1(),

        CortexA53_MADD_A64(),
        CortexA53_DefaultA64Mul(),
        CortexA53_DefaultMul()]
    opLat = 3
    cantForwardFromFUIndices = [0, 1, 5] # Int1, Int2, Mem

class CortexA53_IntDivFU(MinorFU):
    opClasses = minorMakeOpClassSet(['IntDiv'])
    timings = [CortexA53_SDIV_A1(), CortexA53_UDIV_A1(),
        CortexA53_SDIV_A64()]
    issueLat = 3
    opLat = 3

class CortexA53_MemFU(MinorFU):
    opClasses = minorMakeOpClassSet(['MemRead', 'MemWrite', 'FloatMemRead',
                                     'FloatMemWrite'])
    timings = [CortexA53_DefaultMem(), CortexA53_DefaultMem64()]
    opLat = 1
    cantForwardFromFUIndices = [5] # Mem (this FU)

class CortexA53_MiscFU(MinorFU):
    opClasses = minorMakeOpClassSet(['IprAccess', 'InstPrefetch'])
    opLat = 1

class CortexA53_FUPool(MinorFUPool):
    funcUnits = [CortexA53_IntFU(), # 0
        CortexA53_Int2FU(), # 1
        CortexA53_IntMulFU(), # 2
        CortexA53_IntDivFU(), # 3
        CortexA53_FloatSimdFU(), # 4
        CortexA53_MemFU(), # 5
        CortexA53_MiscFU() # 6
        ]

class CortexA53_DTB(ArmTLB):
    size = 256

class CortexA53_ITB(ArmTLB):
    size = 256

class CortexA53_WalkCache(Cache):
    data_latency = 4
    tag_latency = 4
    response_latency = 4
    mshrs = 6
    tgts_per_mshr = 8
    size = '1kB'
    assoc = 8
    write_buffers = 16

class CortexA53_BP(TournamentBP):
    localPredictorSize = 64
    localCtrBits = 2
    localHistoryTableSize = 64
    globalPredictorSize = 1024
    globalCtrBits = 2
    choicePredictorSize = 1024
    choiceCtrBits = 2
    BTBEntries = 128
    BTBTagSize = 18
    RASSize = 8
    instShiftAmt = 2

class CortexA53_ICache(Cache):
    data_latency = 1
    tag_latency = 1
    response_latency = 1
    mshrs = 2
    tgts_per_mshr = 8
    size = '32kB'
    assoc = 2
    # No prefetcher, this is handled by the core

class CortexA53_DCache(Cache):
    data_latency = 1
    tag_latency = 1
    response_latency = 1
    mshrs = 8  
    demand_mshr_reserve = 3
    tgts_per_mshr = 8
    size = '32kB'
    assoc = 4
    write_buffers = 4
    prefetcher = StridePrefetcher(
        queue_size=4,
        degree=4)
    replacement_policy = RandomRP()
    writeback_clean = True
    clusivity = 'mostly_excl'
    sequential_access = True
    #prefetcher = MultiPrefetcher(
    #    prefetchers = [ StridePrefetcher(),
    #                    TaggedPrefetcher()])
    #prefetch_on_access = True

class CortexA53_L2(Cache):
    data_latency = 10
    tag_latency = 10
    response_latency = 5
    mshrs = 16
    tgts_per_mshr = 8
    size = '512kB'
    assoc = 16
    write_buffers = 16
    replacement_policy = RandomRP()
    # prefetcher FIXME

class CortexA53(MinorCPU):
    # Inherit the doc string from the module to avoid repeating it
    # here.
    __doc__ = __doc__

    fetch1LineSnapWidth = 0
    fetch1LineWidth = 0
    fetch1FetchLimit = 1
    fetch1ToFetch2ForwardDelay = 1
    fetch1ToFetch2BackwardDelay = 1

    fetch2InputBufferSize = 2
    fetch2ToDecodeForwardDelay = 1
    fetch2CycleInput = True

    decodeInputBufferSize = 3
    decodeToExecuteForwardDelay = 1
    decodeInputWidth = 2
    decodeCycleInput = True

    executeInputWidth = 2
    executeCycleInput = True
    executeIssueLimit = 2

    # Only allow one ld/st to be issued but the second ld/st FU allows
    # back-to-back loads
    executeMemoryIssueLimit = 1

    executeCommitLimit = 2
    executeMemoryCommitLimit = 1
    executeInputBufferSize = 7

    executeMaxAccessesInMemory = 3

    executeLSQMaxStoreBufferStoresPerCycle = 2
    executeLSQRequestsQueueSize = 1
    executeLSQTransfersQueueSize = 3
    executeLSQStoreBufferSize = 5
    executeBranchDelay = 1
    executeFuncUnits = CortexA53_FUPool()
    executeSetTraceTimeOnCommit = True
    executeSetTraceTimeOnIssue = False

    executeAllowEarlyMemoryIssue = True

    enableIdling = False

    branchPred = CortexA53_BP()

    itb = CortexA53_ITB()
    dtb = CortexA53_DTB()

__all__ = [
    "CortexA53_BP",
    "CortexA53_ITB", "CortexA53_DTB", "CortexA53_WalkCache",
    "CortexA53_ICache", "CortexA53_DCache", "CortexA53_L2",
    "CortexA53",
]
