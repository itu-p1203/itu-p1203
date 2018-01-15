#!/usr/bin/env python3
"""
Copyright 2017 Deutsche Telekom AG, Technische Universität Berlin, Technische
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
import datetime

from itu_p1203 import log
from itu_p1203.p1203Pa import P1203Pa
from itu_p1203.p1203Pv import P1203Pv
from itu_p1203.p1203Pq import P1203Pq

logger = log.setup_custom_logger('main')


class P1203Standalone:
    """
    Class for calculating P1203 based on JSON input files
    """

    def __init__(self, input_report, debug=False):
        """
        Initialize a standalone model run based on JSON input files

        Arguments:
            input_report {dict} -- JSON input report, must correspond to specification

        Keyword Arguments:
            debug {bool} -- enable debug output (default: {False})
        """
        self.input_report = input_report
        self.debug = debug

        self.audio = None
        self.video = None
        self.integration = None
        self.overall_result = None

    def calculate_pa(self):
        """
        Calculate Pa and return audio dict
        """
        logger.debug("Calculating audio scores ...")
        segments = []
        try:
            segments = self.input_report['I11']["segments"]
        except Exception:
            logger.warning("No audio segments specified")

        stream_id = None
        try:
            stream_id = self.input_report["I11"]["streamId"]
        except Exception:
            logger.warning("No stream ID specified")

        self.audio = P1203Pa(segments, stream_id).calculate()

        if self.debug:
            print(json.dumps(self.audio, indent=True, sort_keys=True))

        return self.audio

    def calculate_pv(self):
        """
        Calculate Pv and return video dict
        """
        logger.debug("Calculating video scores ...")
        segments = []
        try:
            segments = self.input_report["I13"]["segments"]
        except Exception:
            logger.error("No video segments defined, check your input format")

        display_res = "1920x1080"
        try:
            display_res = self.input_report["IGen"]["displaySize"]
        except Exception:
            logger.warning("No display resolution specified, assuming full HD")

        stream_id = None
        try:
            stream_id = self.input_report["I13"]["streamId"]
        except Exception:
            logger.warning("No stream ID specified")

        self.video = P1203Pv(
            segments=segments,
            display_res=display_res,
            stream_id=stream_id
        ).calculate()

        if self.debug:
            print(json.dumps(self.video, indent=True, sort_keys=True))

        return self.video

    def calculate_integration(self):
        """
        Calculate Pq and return integration dict
        """
        logger.debug("Calculating integration module ...")

        stalling = []
        if "I23" in self.input_report.keys() and "stalling" in self.input_report["I23"].keys():
            stalling = self.input_report["I23"]["stalling"]

        device = "pc"
        try:
            device = self.input_report["IGen"]["device"]
        except Exception:
            logger.warning("Device not defined in input report, assuming PC")

        self.integration = P1203Pq(
            O21=self.audio["audio"]["O21"],
            O22=self.video["video"]["O22"],
            l_buff=[x[1] for x in stalling],
            p_buff=[x[0] - stalling[0][0] for x in stalling],
            device=device
        ).calculate()

        return self.integration

    def calculate_complete(self):
        """
        Calculates P.1203 scores based on JSON input file

        Returns:
            dict -- integration output according to spec:
                "streamId": video["video"]["streamId"],
                "mode": video["video"]["mode"],
                "O23": integration_result["O23"],
                "O34": integration_result["O34"],
                "O35": integration_result["O35"],
                "O46": integration_result["O46"]
        """
        self.calculate_pa()
        self.calculate_pv()
        self.calculate_integration()

        self.overall_result = {
            "streamId": self.video["video"]["streamId"],
            "mode": self.video["video"]["mode"],
            "O23": self.integration["O23"],
            "O34": self.integration["O34"],
            "O35": self.integration["O35"],
            "O46": self.integration["O46"],
            "date": datetime.datetime.today().isoformat()
        }
        return self.overall_result