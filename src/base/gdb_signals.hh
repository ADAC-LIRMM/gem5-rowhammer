/*
These signals definitions are imported from GDB's include/gdb/signals.def.
*/
#include <cstdint>
#ifndef __BASE_GDB_SIGNALS_HH__
#define __BASE_GDB_SIGNALS_HH__
namespace gem5{
  enum class GDBSignal : uint8_t
  {
    ZERO = 0, //Signal 0
    HUP = 1, //Hangup
    INT = 2, //Interrupt
    QUIT = 3, //Quit
    ILL = 4, //Illegal instruction
    TRAP = 5, //Trace/breakpoint trap
    ABRT = 6, //Aborted
    EMT = 7, //Emulation trap
    FPE = 8, //Arithmetic exception
    KILL = 9, //Killed
    BUS = 10, //Bus error
    SEGV = 11, //Segmentation fault
    SYS = 12, //Bad system call
    PIPE = 13, //Broken pipe
    ALRM = 14, //Alarm clock
    TERM = 15, //Terminated
    URG = 16, //Urgent I/O condition
    STOP = 17, //Stopped (signal)
    TSTP = 18, //Stopped (user)
    CONT = 19, //Continued
    CHLD = 20, //Child status changed
    TTIN = 21, //Stopped (tty input)
    TTOU = 22, //Stopped (tty output)
    IO = 23, //I/O possible
    XCPU = 24, //CPU time limit exceeded
    XFSZ = 25, //File size limit exceeded
    VTALRM = 26, //Virtual timer expired
    PROF = 27, //Profiling timer expired
    WINCH = 28, //Window size changed
    LOST = 29, //Resource lost
    USR1 = 30, //User defined signal 1
    USR2 = 31, //User defined signal 2
    PWR = 32, //Power fail/restart
    /*Similar to SIGIO.  Perhaps they should have the same number.  */
    POLL = 33, //Pollable event occurred
    WIND = 34, //SIGWIND
    PHONE = 35, //SIGPHONE
    WAITING = 36, //Process's LWPs are blocked
    LWP = 37, //Signal LWP
    DANGER = 38, //Swap space dangerously low
    GRANT = 39, //Monitor mode granted
    RETRACT = 40, //Need to relinquish monitor mode
    MSG = 41, //Monitor mode data available
    SOUND = 42, //Sound completed
    SAK = 43, //Secure attention
    PRIO = 44, //SIGPRIO
    SIG33 = 45, //Real-time event 33
    SIG34 = 46, //Real-time event 34
    SIG35 = 47, //Real-time event 35
    SIG36 = 48, //Real-time event 36
    SIG37 = 49, //Real-time event 37
    SIG38 = 50, //Real-time event 38
    SIG39 = 51, //Real-time event 39
    SIG40 = 52, //Real-time event 40
    SIG41 = 53, //Real-time event 41
    SIG42 = 54, //Real-time event 42
    SIG43 = 55, //Real-time event 43
    SIG44 = 56, //Real-time event 44
    SIG45 = 57, //Real-time event 45
    SIG46 = 58, //Real-time event 46
    SIG47 = 59, //Real-time event 47
    SIG48 = 60, //Real-time event 48
    SIG49 = 61, //Real-time event 49
    SIG50 = 62, //Real-time event 50
    SIG51 = 63, //Real-time event 51
    SIG52 = 64, //Real-time event 52
    SIG53 = 65, //Real-time event 53
    SIG54 = 66, //Real-time event 54
    SIG55 = 67, //Real-time event 55
    SIG56 = 68, //Real-time event 56
    SIG57 = 69, //Real-time event 57
    SIG58 = 70, //Real-time event 58
    SIG59 = 71, //Real-time event 59
    SIG60 = 72, //Real-time event 60
    SIG61 = 73, //Real-time event 61
    SIG62 = 74, //Real-time event 62
    SIG63 = 75, //Real-time event 63
    /* Used internally by Solaris threads.  See signal(5) on Solaris.  */
    CANCEL = 76, //LWP internal signal
    /* Yes, this pains me, too.  But LynxOS didn't have SIG32, and now
      GNU/Linux does, and we can't disturb the numbering, since it's
      part of the remote protocol.  Note that in some GDB's
      GDB_SIGNAL_REALTIME_32 is number 76.  */
    SIG32 = 77, //Real-time event 32
    /* Yet another pain, IRIX 6 has SIG64. */
    SIG64 = 78, //Real-time event 64
    /* Yet another pain, GNU/Linux MIPS might go up to 128. */
    SIG65 = 79, //Real-time event 65
    SIG66 = 80, //Real-time event 66
    SIG67 = 81, //Real-time event 67
    SIG68 = 82, //Real-time event 68
    SIG69 = 83, //Real-time event 69
    SIG70 = 84, //Real-time event 70
    SIG71 = 85, //Real-time event 71
    SIG72 = 86, //Real-time event 72
    SIG73 = 87, //Real-time event 73
    SIG74 = 88, //Real-time event 74
    SIG75 = 89, //Real-time event 75
    SIG76 = 90, //Real-time event 76
    SIG77 = 91, //Real-time event 77
    SIG78 = 92, //Real-time event 78
    SIG79 = 93, //Real-time event 79
    SIG80 = 94, //Real-time event 80
    SIG81 = 95, //Real-time event 81
    SIG82 = 96, //Real-time event 82
    SIG83 = 97, //Real-time event 83
    SIG84 = 98, //Real-time event 84
    SIG85 = 99, //Real-time event 85
    SIG86 = 100, //Real-time event 86
    SIG87 = 101, //Real-time event 87
    SIG88 = 102, //Real-time event 88
    SIG89 = 103, //Real-time event 89
    SIG90 = 104, //Real-time event 90
    SIG91 = 105, //Real-time event 91
    SIG92 = 106, //Real-time event 92
    SIG93 = 107, //Real-time event 93
    SIG94 = 108, //Real-time event 94
    SIG95 = 109, //Real-time event 95
    SIG96 = 110, //Real-time event 96
    SIG97 = 111, //Real-time event 97
    SIG98 = 112, //Real-time event 98
    SIG99 = 113, //Real-time event 99
    SIG100 = 114, //Real-time event 100
    SIG101 = 115, //Real-time event 101
    SIG102 = 116, //Real-time event 102
    SIG103 = 117, //Real-time event 103
    SIG104 = 118, //Real-time event 104
    SIG105 = 119, //Real-time event 105
    SIG106 = 120, //Real-time event 106
    SIG107 = 121, //Real-time event 107
    SIG108 = 122, //Real-time event 108
    SIG109 = 123, //Real-time event 109
    SIG110 = 124, //Real-time event 110
    SIG111 = 125, //Real-time event 111
    SIG112 = 126, //Real-time event 112
    SIG113 = 127, //Real-time event 113
    SIG114 = 128, //Real-time event 114
    SIG115 = 129, //Real-time event 115
    SIG116 = 130, //Real-time event 116
    SIG117 = 131, //Real-time event 117
    SIG118 = 132, //Real-time event 118
    SIG119 = 133, //Real-time event 119
    SIG120 = 134, //Real-time event 120
    SIG121 = 135, //Real-time event 121
    SIG122 = 136, //Real-time event 122
    SIG123 = 137, //Real-time event 123
    SIG124 = 138, //Real-time event 124
    SIG125 = 139, //Real-time event 125
    SIG126 = 140, //Real-time event 126
    SIG127 = 141, //Real-time event 127
    INFO = 142, //Information request
    /* Mach exceptions.  In versions of GDB before 5.2, these were just before
       GDB_SIGNAL_INFO if you were compiling on a Mach host (and missing
       otherwise).  */
    EXC_BAD_ACCESS = 145, //Could not access memory
    EXC_BAD_INSTRUCTION = 146, //Illegal instruction/operand
    EXC_ARITHMETIC = 147, //Arithmetic exception
    EXC_EMULATION = 148, //Emulation instruction
    EXC_SOFTWARE = 149, //Software generated exception
    EXC_BREAKPOINT = 150, //Breakpoint
    LIBRT = 151 //librt internal signal
  };
}
#endif /* __BASE_GDB_SIGNALS_HH__ */
