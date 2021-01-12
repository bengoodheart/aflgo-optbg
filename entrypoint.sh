#!/bin/sh -l

cd ${AFLGO} && make clean all && cd llvm_mode && make clean all
cd ${AFLGO}/scripts/fuzz && ./libxml2-ef709ce2.sh