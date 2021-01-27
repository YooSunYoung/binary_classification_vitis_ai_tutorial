#!/bin/bash

# make shared library file (.so)
aarch64-xilinx-linux-gcc -fPIC  \
  -shared ./dpu_simple_net.elf -o ./dpuv2_rundir/libdpumodelsimple_net.so
