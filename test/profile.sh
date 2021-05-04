#!/usr/bin/env bash
#
# Create a profile trace and output PDF

cd "$(dirname "$0")"

rm -f output*.cprof output*.pdf && \

for f in mode0 mode0_long; do
    echo "Profiling $f"
    PYTHONPATH=../ \
    python3 \
        -m cProfile \
            -s cumtime \
            -o output_"$f".cprof \
        ../itu_p1203/__main__.py \
            --cpu-count 1 \
            --print-intermediate \
            ../examples/"$f".json \
        > /dev/null 2>&1

    gprof2dot -f pstats -s output_"$f".cprof -n 1 | \
        dot -Tpdf -o output_"$f".pdf
done
