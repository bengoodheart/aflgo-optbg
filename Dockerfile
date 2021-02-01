
FROM patoresearch/aflgo-prereq

ENV AFLGO /aflgo

RUN git clone https://github.com/bengoodheart/aflgo-optbg.git ${AFLGO} &&\
   cd ${AFLGO} && make all && cd llvm_mode && make all

WORKDIR ${AFLGO}

# ENTRYPOINT [ "/aflgo/entrypoint.sh" ]

