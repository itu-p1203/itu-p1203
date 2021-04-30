#!/usr/bin/env bash
#
# Create a profile trace and output PDF

cd "$(dirname "$0")"

rm -f output.cprof output.pdf && \
PYTHONPATH=../ \
python3 \
    -m cProfile \
        -s cumtime \
        -o output.cprof \
    ../itu_p1203/__main__.py \
        --cpu-count 1 \
        --print-intermediate \
        ../examples/request.json \
    > /dev/null 2>&1

gprof2dot -f pstats output.cprof | \
    dot -Tpdf -o output.pdf
