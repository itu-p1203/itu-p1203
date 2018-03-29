#!/usr/bin/env python3
"""
Copyright 2017-2018 Deutsche Telekom AG, Technische Universität Berlin, Technische
Universität Ilmenau, LM Ericsson

Permission is hereby granted, free of charge, to use the software for research
purposes.

Any other use of the software, including commercial use, merging, publishing,
distributing, sublicensing, and/or selling copies of the Software, is
forbidden. For a commercial license, please contact the respective rights
holders of the standards ITU-T Rec. P.1203, ITU-T Rec. P.1203.1, ITU-T Rec.
P.1203.2, and ITU-T Rec. P.1203.3. See https://www.itu.int/en/ITU-T/ipr/Pages/default.aspx
for more information.

NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY THIS LICENSE.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import os
import argparse
import logging
import sys
import multiprocessing
import json
from multiprocessing import Pool

from . import log
from . import utils
from .itu_p1203 import P1203Standalone
from .extractor import Extractor
from .errors import P1203StandaloneError

logger = log.setup_custom_logger('main')


def extract_from_single_file(input_file, mode, debug=False, only_pa=False, only_pv=False, print_intermediate=False, modules={}):
    """
    Extract the report based on a single input file (JSON or video)

    Arguments:
        input_file {str} -- input file (JSON or video file)
        mode {int} -- 0, 1, 2, 3 depending on extraction mode wanted
        debug {bool} -- whether to run in debug mode
        only_pa {bool} -- only run Pa module
        only_pv {bool} -- only run Pv module
        print_intermediate {bool} -- print intermediate O.21/O.22 values
        modules: you can specify Pa, Pv, Pq classnames, that will be used, default are the P1203 modules
            e.g. modules={"Pa": OtherPaModule}
    """
    if not os.path.isfile(input_file):
        raise P1203StandaloneError("No such file: {input_file}".format(input_file=input_file))

    file_ext = os.path.splitext(input_file)[1].lower()[1:]
    valid_video_exts = ["avi", "mp4", "mkv", "nut", "mpeg", "mpg"]

    # normal case, handle JSON files
    if file_ext == "json":
        input_report = utils.read_json_without_comments(input_file)
    # convert input video to required format
    elif file_ext in valid_video_exts:
        logger.debug("Running extract_from_segment_files to get input report: {} mode {}".format(input_file, mode))
        try:
            input_report = Extractor([input_file], mode).extract()
        except Exception as e:
            raise P1203StandaloneError("Could not auto-generate input report, error: {e.output}".format(e=e))
    else:
        raise P1203StandaloneError("Could not guess what kind of input file this is: {input_file}".format(input_file=input_file))

    # create model ...
    itu_p1203 = P1203Standalone(
        input_report,
        debug,
        Pa=modules.get("Pa", None),
        Pv=modules.get("Pv", None),
        Pq=modules.get("Pq", None),
    )

    # ... and run it
    if only_pa:
        output = itu_p1203.calculate_pa()
    elif only_pv:
        output = itu_p1203.calculate_pv()
    else:
        output = itu_p1203.calculate_complete(print_intermediate)

    return (input_file, output)


def main(modules={}):
    """
    Runs standalone P.1203 version,

    you can specify other Pa, Pv, Pq modules, e.g.
        modules = {"Pa": myownPaModule}
    """
    from . import __version__

    # argument parsing
    parser = argparse.ArgumentParser(
        description='P.1203 standalone implementation, version ' + str(__version__),
        epilog="2017",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        'input',
        type=str,
        nargs="+",
        help="input report JSON file(s) or video file(s), format see README"
    )
    parser.add_argument(
        '-m', '--mode',
        type=int,
        choices=[0, 1, 2, 3],
        default=1,
        help="mode to run for extraction in case video files are loaded"
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help="some debug output"
    )
    parser.add_argument(
        '--only-pa',
        action='store_true',
        help="just print Pa O.21 values"
    )
    parser.add_argument(
        '--only-pv',
        action='store_true',
        help="just print Pv O.22 values"
    )
    parser.add_argument(
        '--print-intermediate',
        action='store_true',
        help="print intermediate O.21/O.22 values"
    )
    parser.add_argument(
        '--cpu-count',
        type=int,
        default=multiprocessing.cpu_count(),
        help='thread/CPU count'
    )
    parser.add_argument(
        '--version',
        action='version',
        version=str(__version__)
    )

    argsdict = vars(parser.parse_args())

    if argsdict["debug"]:
        logger.setLevel(logging.DEBUG)

    output_results = []

    if argsdict["debug"] or argsdict["cpu_count"] == 1:
        use_multiprocessing = False
    else:
        use_multiprocessing = True

    if use_multiprocessing:
        pool = Pool(processes=argsdict["cpu_count"])
        params = [(input_file, argsdict["mode"], argsdict["debug"], argsdict["only_pa"], argsdict["only_pv"], argsdict["print_intermediate"], modules) for input_file in argsdict["input"]]
        try:
            output_results = pool.starmap(extract_from_single_file, params)
        except Exception as e:
            logger.error("Error during processing, exiting")
            sys.exit(1)
    else:
        # iterate over input files
        for input_file in argsdict["input"]:
            try:
                result = extract_from_single_file(input_file, argsdict["mode"], argsdict["debug"], argsdict["only_pa"], argsdict["only_pv"], argsdict["print_intermediate"], modules)
            except Exception as e:
                logger.error("Error during processing, exiting")
                sys.exit(1)
            # append to output
            output_results.append(result)

    output_reports = {k: v for (k, v) in output_results}
    print(json.dumps(output_reports, indent=True, sort_keys=True))


if __name__ == "__main__":
    main()
