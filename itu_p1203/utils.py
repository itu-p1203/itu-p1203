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

import json
import os
import re
import sys

import numpy as np

from . import log
from .errors import P1203StandaloneError

logger = log.setup_custom_logger("itu_p1203")


MOS_MAX = 4.9
MOS_MIN = 1.05

R_FROM_MOS_KEYS = [
    1.05,
    1.050214703125,
    1.051169875,
    1.052255859375,
    1.0534720000000002,
    1.054817640625,
    1.0562921250000001,
    1.0578947968749999,
    1.059625,
    1.061482078125,
    1.0634653750000003,
    1.065574234375,
    1.067808,
    1.0701660156250001,
    1.072647625,
    1.075252171875,
    1.077979,
    1.0808274531250002,
    1.083796875,
    1.086886609375,
    1.0900960000000002,
    1.093424390625,
    1.096871125,
    1.100435546875,
    1.104117,
    1.1079148281250002,
    1.111828375,
    1.1158569843750001,
    1.12,
    1.124256765625,
    1.128626625,
    1.1331089218750001,
    1.1377030000000001,
    1.1424082031250002,
    1.147223875,
    1.152149359375,
    1.157184,
    1.1623271406250002,
    1.167578125,
    1.1729362968750001,
    1.178401,
    1.1839715781250002,
    1.189647375,
    1.1954277343750002,
    1.201312,
    1.2072995156250002,
    1.2133896250000002,
    1.219581671875,
    1.2258750000000003,
    1.2322689531250002,
    1.2387628750000002,
    1.2453561093750003,
    1.2520480000000003,
    1.2588378906250002,
    1.2657251250000001,
    1.2727090468750002,
    1.279789,
    1.286964328125,
    1.2942343750000003,
    1.3015984843750001,
    1.309056,
    1.3166062656250002,
    1.324248625,
    1.331982421875,
    1.339807,
    1.347721703125,
    1.3557258750000003,
    1.363818859375,
    1.3720000000000003,
    1.380268640625,
    1.3886241250000002,
    1.3970657968750002,
    1.4055930000000003,
    1.414205078125,
    1.4229013750000004,
    1.431681234375,
    1.4405440000000003,
    1.449489015625,
    1.4585156250000002,
    1.4676231718750001,
    1.476811,
    1.4860784531250002,
    1.4954248750000003,
    1.5048496093750003,
    1.5143520000000001,
    1.5239313906250003,
    1.5335871250000002,
    1.5433185468750004,
    1.553125,
    1.5630058281250003,
    1.572960375,
    1.5829879843750003,
    1.5930880000000003,
    1.6032597656249998,
    1.6135026250000002,
    1.6238159218750003,
    1.6341990000000002,
    1.644651203125,
    1.6551718750000002,
    1.6657603593750003,
    1.6764160000000001,
    1.687138140625,
    1.6979261250000002,
    1.7087792968750004,
    1.719697,
    1.7306785781249998,
    1.7417233750000005,
    1.7528307343750003,
    1.764,
    1.7752305156250003,
    1.786521625,
    1.7978726718750002,
    1.809283,
    1.8207519531250003,
    1.8322788750000005,
    1.8438631093750002,
    1.855504,
    1.8672008906250004,
    1.8789531250000004,
    1.8907600468750003,
    1.902621,
    1.9145353281250002,
    1.9265023750000005,
    1.9385214843750003,
    1.9505919999999999,
    1.9627132656250001,
    1.9748846250000005,
    1.9871054218750002,
    1.9993750000000003,
    2.011692703125,
    2.0240578750000005,
    2.0364698593750004,
    2.048928,
    2.061431640625001,
    2.0739801250000003,
    2.086572796875,
    2.099209,
    2.1118880781250007,
    2.1246093750000004,
    2.1373722343750003,
    2.150176,
    2.1630200156250003,
    2.175903625,
    2.188826171875,
    2.2017870000000004,
    2.214785453125,
    2.2278208750000004,
    2.240892609375,
    2.2540000000000004,
    2.2671423906250006,
    2.280319125,
    2.293529546875,
    2.306773,
    2.3200488281250005,
    2.333356375,
    2.346694984375,
    2.3600640000000004,
    2.3734627656250007,
    2.3868906250000004,
    2.4003469218750006,
    2.413831,
    2.4273422031250007,
    2.4408798750000003,
    2.454443359375,
    2.468032000000001,
    2.4816451406250004,
    2.495282125,
    2.508942296875,
    2.5226250000000006,
    2.5363295781250006,
    2.5500553750000003,
    2.563801734375,
    2.5775680000000003,
    2.5913535156250003,
    2.6051576250000004,
    2.618979671875,
    2.632819,
    2.6466749531250002,
    2.660546875,
    2.6744341093750004,
    2.688336,
    2.7022518906250004,
    2.7161811250000003,
    2.730123046875,
    2.7440770000000008,
    2.758042328125,
    2.772018375,
    2.7860044843750003,
    2.8000000000000007,
    2.8140042656250004,
    2.8280166250000005,
    2.8420364218750005,
    2.8560630000000007,
    2.870095703125,
    2.884133875,
    2.898176859375001,
    2.9122240000000006,
    2.9262746406250004,
    2.940328125,
    2.9543837968750006,
    2.9684410000000003,
    2.982499078125,
    2.996557375,
    3.010615234375001,
    3.0246720000000002,
    3.038727015625,
    3.052779625,
    3.0668291718750007,
    3.0808750000000003,
    3.094916453125,
    3.108952875000001,
    3.1229836093750007,
    3.1370080000000002,
    3.151025390625,
    3.165035125,
    3.179036546875001,
    3.1930290000000006,
    3.207011828125,
    3.220984375,
    3.234945984375001,
    3.2488960000000002,
    3.262833765625,
    3.276758625,
    3.2906699218750006,
    3.3045670000000005,
    3.318449203125,
    3.332315875000001,
    3.3461663593750006,
    3.3600000000000003,
    3.3738161406250002,
    3.3876141250000007,
    3.4013932968750007,
    3.415153,
    3.428892578125,
    3.4426113750000007,
    3.4563087343750003,
    3.469984,
    3.483636515625,
    3.4972656250000007,
    3.5108706718750007,
    3.5244510000000004,
    3.5380059531250008,
    3.5515348750000006,
    3.5650371093750004,
    3.5785120000000004,
    3.591958890625,
    3.605377125000001,
    3.6187660468750003,
    3.6321250000000003,
    3.645453328125,
    3.6587503750000008,
    3.6720154843750006,
    3.685248,
    3.698447265625,
    3.7116126250000008,
    3.7247434218750004,
    3.737839,
    3.750898703125,
    3.7639218750000007,
    3.7769078593750005,
    3.7898560000000003,
    3.802765640625001,
    3.8156361250000006,
    3.8284667968750004,
    3.841257,
    3.854006078125,
    3.8667133750000007,
    3.8793782343750003,
    3.892000000000001,
    3.9045780156250007,
    3.9171116250000004,
    3.929600171875,
    3.942043,
    3.954439453125001,
    3.9667888750000007,
    3.9790906093750005,
    3.9913440000000002,
    4.003548390625,
    4.015703125000001,
    4.0278075468750005,
    4.039861,
    4.051862828125,
    4.063812375,
    4.075708984375,
    4.087552,
    4.099340765625,
    4.1110746250000005,
    4.1227529218750005,
    4.134375000000001,
    4.145940203125001,
    4.157447875000001,
    4.168897359375,
    4.180288,
    4.191619140625001,
    4.202890125000001,
    4.214100296875001,
    4.225249000000001,
    4.236335578125001,
    4.247359375,
    4.258319734375,
    4.269216000000001,
    4.280047515625,
    4.290813625,
    4.301513671875001,
    4.312147,
    4.322712953125,
    4.333210875000001,
    4.343640109375,
    4.354000000000001,
    4.364289890625001,
    4.374509125,
    4.384657046875,
    4.394733,
    4.404736328125001,
    4.414666375,
    4.424522484375001,
    4.434304000000001,
    4.444010265625001,
    4.453640625,
    4.463194421875,
    4.472671000000001,
    4.482069703125,
    4.491389875,
    4.500630859375001,
    4.509792000000001,
    4.518872640625,
    4.527872125,
    4.536789796875,
    4.545625,
    4.554377078125,
    4.5630453750000015,
    4.571629234375001,
    4.580128,
    4.588541015625,
    4.596867625,
    4.605107171875001,
    4.613259,
    4.621322453125001,
    4.6292968750000005,
    4.637181609375,
    4.644976000000001,
    4.652679390625001,
    4.6602911250000005,
    4.667810546875001,
    4.675237000000001,
    4.6825698281250006,
    4.689808375,
    4.696951984375,
    4.704000000000001,
    4.710951765625,
    4.717806625000001,
    4.724563921875001,
    4.731223000000001,
    4.737783203125001,
    4.744243875,
    4.750604359375001,
    4.756864,
    4.763022140625,
    4.769078125000001,
    4.775031296875,
    4.780881000000001,
    4.786626578125,
    4.792267375,
    4.797802734375001,
    4.803232,
    4.808554515625001,
    4.813769625000001,
    4.8188766718750005,
    4.823875,
    4.828763953125001,
    4.833542875000001,
    4.838211109375001,
    4.842768,
    4.847212890625,
    4.851545125,
    4.8557640468750005,
    4.859869000000001,
    4.863859328125001,
    4.867734375000001,
    4.871493484375001,
    4.875136,
    4.878661265625,
    4.8820686250000005,
    4.885357421875001,
    4.888527000000001,
    4.891576703125001,
    4.894505875000001,
    4.897313859375001,
    4.9,
]
R_FROM_MOS_VALUES = [
    0,
    3.25,
    3.5,
    3.75,
    4.0,
    4.25,
    4.5,
    4.75,
    5.0,
    5.25,
    5.5,
    5.75,
    6.0,
    6.25,
    6.5,
    6.75,
    7.0,
    7.25,
    7.5,
    7.75,
    8.0,
    8.25,
    8.5,
    8.75,
    9.0,
    9.25,
    9.5,
    9.75,
    10.0,
    10.25,
    10.5,
    10.75,
    11.0,
    11.25,
    11.5,
    11.75,
    12.0,
    12.25,
    12.5,
    12.75,
    13.0,
    13.25,
    13.5,
    13.75,
    14.0,
    14.25,
    14.5,
    14.75,
    15.0,
    15.25,
    15.5,
    15.75,
    16.0,
    16.25,
    16.5,
    16.75,
    17.0,
    17.25,
    17.5,
    17.75,
    18.0,
    18.25,
    18.5,
    18.75,
    19.0,
    19.25,
    19.5,
    19.75,
    20.0,
    20.25,
    20.5,
    20.75,
    21.0,
    21.25,
    21.5,
    21.75,
    22.0,
    22.25,
    22.5,
    22.75,
    23.0,
    23.25,
    23.5,
    23.75,
    24.0,
    24.25,
    24.5,
    24.75,
    25.0,
    25.25,
    25.5,
    25.75,
    26.0,
    26.25,
    26.5,
    26.75,
    27.0,
    27.25,
    27.5,
    27.75,
    28.0,
    28.25,
    28.5,
    28.75,
    29.0,
    29.25,
    29.5,
    29.75,
    30.0,
    30.25,
    30.5,
    30.75,
    31.0,
    31.25,
    31.5,
    31.75,
    32.0,
    32.25,
    32.5,
    32.75,
    33.0,
    33.25,
    33.5,
    33.75,
    34.0,
    34.25,
    34.5,
    34.75,
    35.0,
    35.25,
    35.5,
    35.75,
    36.0,
    36.25,
    36.5,
    36.75,
    37.0,
    37.25,
    37.5,
    37.75,
    38.0,
    38.25,
    38.5,
    38.75,
    39.0,
    39.25,
    39.5,
    39.75,
    40.0,
    40.25,
    40.5,
    40.75,
    41.0,
    41.25,
    41.5,
    41.75,
    42.0,
    42.25,
    42.5,
    42.75,
    43.0,
    43.25,
    43.5,
    43.75,
    44.0,
    44.25,
    44.5,
    44.75,
    45.0,
    45.25,
    45.5,
    45.75,
    46.0,
    46.25,
    46.5,
    46.75,
    47.0,
    47.25,
    47.5,
    47.75,
    48.0,
    48.25,
    48.5,
    48.75,
    49.0,
    49.25,
    49.5,
    49.75,
    50.0,
    50.25,
    50.5,
    50.75,
    51.0,
    51.25,
    51.5,
    51.75,
    52.0,
    52.25,
    52.5,
    52.75,
    53.0,
    53.25,
    53.5,
    53.75,
    54.0,
    54.25,
    54.5,
    54.75,
    55.0,
    55.25,
    55.5,
    55.75,
    56.0,
    56.25,
    56.5,
    56.75,
    57.0,
    57.25,
    57.5,
    57.75,
    58.0,
    58.25,
    58.5,
    58.75,
    59.0,
    59.25,
    59.5,
    59.75,
    60.0,
    60.25,
    60.5,
    60.75,
    61.0,
    61.25,
    61.5,
    61.75,
    62.0,
    62.25,
    62.5,
    62.75,
    63.0,
    63.25,
    63.5,
    63.75,
    64.0,
    64.25,
    64.5,
    64.75,
    65.0,
    65.25,
    65.5,
    65.75,
    66.0,
    66.25,
    66.5,
    66.75,
    67.0,
    67.25,
    67.5,
    67.75,
    68.0,
    68.25,
    68.5,
    68.75,
    69.0,
    69.25,
    69.5,
    69.75,
    70.0,
    70.25,
    70.5,
    70.75,
    71.0,
    71.25,
    71.5,
    71.75,
    72.0,
    72.25,
    72.5,
    72.75,
    73.0,
    73.25,
    73.5,
    73.75,
    74.0,
    74.25,
    74.5,
    74.75,
    75.0,
    75.25,
    75.5,
    75.75,
    76.0,
    76.25,
    76.5,
    76.75,
    77.0,
    77.25,
    77.5,
    77.75,
    78.0,
    78.25,
    78.5,
    78.75,
    79.0,
    79.25,
    79.5,
    79.75,
    80.0,
    80.25,
    80.5,
    80.75,
    81.0,
    81.25,
    81.5,
    81.75,
    82.0,
    82.25,
    82.5,
    82.75,
    83.0,
    83.25,
    83.5,
    83.75,
    84.0,
    84.25,
    84.5,
    84.75,
    85.0,
    85.25,
    85.5,
    85.75,
    86.0,
    86.25,
    86.5,
    86.75,
    87.0,
    87.25,
    87.5,
    87.75,
    88.0,
    88.25,
    88.5,
    88.75,
    89.0,
    89.25,
    89.5,
    89.75,
    90.0,
    90.25,
    90.5,
    90.75,
    91.0,
    91.25,
    91.5,
    91.75,
    92.0,
    92.25,
    92.5,
    92.75,
    93.0,
    93.25,
    93.5,
    93.75,
    94.0,
    94.25,
    94.5,
    94.75,
    95.0,
    95.25,
    95.5,
    95.75,
    96.0,
    96.25,
    96.5,
    96.75,
    97.0,
    97.25,
    97.5,
    97.75,
    98.0,
    98.25,
    98.5,
    98.75,
    99.0,
    99.25,
    99.5,
    99.75,
    100.0,
]


def which(program):
    """
    Find a program in PATH and return path
    From: http://stackoverflow.com/q/377017/
    """

    def is_exe(fpath):
        found = os.path.isfile(fpath) and os.access(fpath, os.X_OK)
        if not found and sys.platform == "win32":
            fpath = fpath + ".exe"
            found = os.path.isfile(fpath) and os.access(fpath, os.X_OK)
        return found

    fpath, _ = os.path.split(program)
    if fpath:
        if is_exe(program):
            logger.debug("found executable: " + str(program))
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                logger.debug("found executable: " + str(exe_file))
                return exe_file

    return None


def calculate_compensated_size(frame_type, size, dts=None):
    """
    Compensate the wrongly reported sizes from ffmpeg, because they contain AUDs, SPS, and PPS.

    frame_type: "I" or anything else ("Non-I", "P", "B", ...)
    size:       size in bytes from VFI File
    dts:        DTS from VFI or none, but then it will assume that it's a regular frame within the file

    From internal tests, we know that the difference between "real" payload length and reported size is
    the following, where the reported size is always higher than the real payload:

      type_bs first_frame_pvs Min. 1st Qu. Median   Mean 3rd Qu. Max.
    1   Non-I           FALSE   11    11.0     11  11.00      11   11
    2       I           FALSE   50    50.0     51  51.69      52   55
    3       I            TRUE  786   787.2    788 788.40     789  791

    Returns the new size of the frame in KB.
    """
    # first frame in an entire PVS has SPS/PPS mixed into it
    if dts is not None and int(dts) == 0:
        size_compensated = int(size) - 800
    else:
        if frame_type == "I":
            size_compensated = int(size) - 55
        else:
            size_compensated = int(size) - 11

    return max(size_compensated, 0)


def mos_from_r(Q):
    MOS = (
        MOS_MIN
        + float(MOS_MAX - MOS_MIN) * float(Q) / 100.0
        + float(Q) * float(Q - 60.0) * float(100.0 - Q) * 0.000007
    )
    return min(MOS_MAX, max(MOS, MOS_MIN))


def r_from_mos(MOS):
    if MOS < MOS_MIN:
        MOS = MOS_MIN
    if MOS > MOS_MAX:
        MOS = MOS_MAX

    if MOS in R_FROM_MOS_KEYS:
        Q = R_FROM_MOS_VALUES[R_FROM_MOS_KEYS.index(MOS)]
    else:
        Q = np.interp(MOS, R_FROM_MOS_KEYS, R_FROM_MOS_VALUES)
    return Q


def constrain(x, minimum=0.0, maximum=100.0):
    """
    Constrain a vector input x between a certain minimum and maximum
    """
    return np.maximum(np.minimum(x, maximum), minimum)


def sigmoid(min_x, min_y, sat_bottom, sat_top, x):
    """
    Sigmoid function depending on x.
    Parameters:
    - min y value
    - max y value
    - bottom saturation x value
    - top saturation x value
    """
    scaled_x = 10.0 / (sat_top - sat_bottom)
    middle_x = (sat_bottom + sat_top) / 2.0
    return min_x + (min_y - min_x) / (1 + np.exp(-scaled_x * (x - middle_x)))


def exponential(a, b, c, d, x):
    """
    Return exponential constrained between a range.
    Call with exponential(a, b, c, d, x).
    Parameters:     a: defines left anchor point of function on y-axis
                    b: defines slope of curve
                    c: shifts the anchor point of curve on x-axis (set to 0)
                    d: defines slope of the curve
    Visualization at: https://www.desmos.com/calculator/xsy2xdqmuo
    """
    return b + (a - b) * np.exp(-(x - c) * np.log(0.5) / (-(d - c)))


def resolution_to_number(string):
    """
    Returns the number of pixels for a resolution given as "wxh", e.g. "1920x1080"
    """
    try:
        return int(string.split("x")[0]) * int(string.split("x")[1])
    except Exception as e:
        raise P1203StandaloneError(
            "Wrong specification of resolution {string}: {e}".format(**locals())
        )


def check_segment_continuity(segments, type="video"):
    """
    Check if segments are contiguous, in the sense of each segment
    starting where the last one ended

    Arguments:
        segments {list} -- list of segments
        type {string} -- video or audio
    """
    last_segment_end = 0
    for i in range(1, len(segments)):
        prev_segment = segments[i - 1]
        last_segment_end = round(prev_segment["start"] + prev_segment["duration"], 2)
        this_segment_start = round(segments[i]["start"], 2)
        if last_segment_end != this_segment_start:
            logger.warning(
                "{type} segment starts at {this_segment_start} but last one ended at {last_segment_end}".format(
                    **locals()
                )
            )
    logger.debug("Checked segment continuity")


def get_chunk_hash(frame, type="video"):
    """
    Return a hash value that uniquely identifies a given frame belonging to
    a quality level. This is determined by the frame having a "representation"
    key. If it does not, a quality level is composed of bitrate, codec, fps.
    For audio, only bitrate counts.
    If it is a video frame, and a display resolution is given per-frame, then
    the chunk will additionally consider the display resolution changing.

    Arguments:
        type {str} -- video or audio

    Returns:
        str -- representation ID or hash of the quality level
    """
    if "representation" in frame.keys():
        return frame["representation"]
    if type == "video":
        chunk_hash = str(frame["bitrate"]) + str(frame["codec"]) + str(frame["fps"])
        # WR: this should actually be also checked if we have multiple bitrates per resolution, and a nominal bitrate was given
        # if "resolution" in frame.keys():
        #     chunk_hash += str(frame["resolution"])
        if "displaySize" in frame.keys():
            chunk_hash += str(frame["displaySize"])
        return chunk_hash
    elif type == "audio":
        return str(frame["bitrate"]) + str(frame["codec"])
    else:
        raise P1203StandaloneError("Wrong type for frame: " + str(type))


def get_chunk(frames, output_sample_index, type="video", onlyfirst=False):
    """
    Get chunk with frames with same quality as the frame at the output sample time

    Arguments:
        frames {list} -- list of frame dicts, each carrying at least the keys: "codec", "bitrate", "framerate"
        output_sample_index {int} -- output sample timestamp index
        type {str} -- type of operation (video or audio) (default: {"video"})
        onlyfirst {bool} -- if true, only return the first frame

    Returns:
        list -- list of frames that should be considered for score calculation
    """
    target_frame = frames[output_sample_index]

    # since there is no target quality level with a certain ID, we infer it from the
    # combination of codec, resolution, and framerate
    target_ql = get_chunk_hash(target_frame, type)

    window = [output_sample_index]
    if not onlyfirst:
        hash_i = target_ql
        for j in range(output_sample_index - 1, -1, -1):
            curr_hash = get_chunk_hash(frames[j], type)
            if curr_hash != hash_i:
                break
            window.insert(0, j)
            hash_i = curr_hash

        hash_i = target_ql
        for j in range(output_sample_index + 1, len(frames), +1):
            curr_hash = get_chunk_hash(frames[j], type)
            if curr_hash != hash_i:
                break
            window.append(j)
            hash_i = curr_hash

    result = [frames[w] for w in window]

    return result


def read_json_without_comments(input_file):
    """
    Parses a JSON file, stripping C-style comments.
    Returns an object.
    """
    with open(input_file, "r") as in_f:
        data = in_f.read()
        data = re.sub(r"\\\n", "", data)
        data = re.sub(r"//.*\n", "\n", data)
    return json.loads(data)


if __name__ == "__main__":
    print("this is only a module")
