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

import datetime
import json
import logging

from . import log
from .errors import P1203StandaloneError
from .p1203Pa import P1203Pa
from .p1203Pq import P1203Pq
from .p1203Pv import P1203Pv

logger = log.setup_custom_logger("itu_p1203")


class P1203Standalone:
    """
    Class for calculating P1203 based on JSON input files
    """

    def __init__(
        self,
        input_report,
        debug=False,
        Pa=P1203Pa,
        Pv=P1203Pv,
        Pq=P1203Pq,
        quiet=False,
        amendment_1_audiovisual=False,
        amendment_1_stalling=False,
        amendment_1_app_2=False,
    ):
        """
        Initialize a standalone model run based on JSON input files

        Arguments:
            input_report {dict} -- JSON input report, must correspond to specification

        Keyword Arguments:
            debug {bool} -- enable debug output (default: {False})
            Pa -- used short time audio quality estimation module (default P1203Pa)
            Pv -- used short time video quality estimation module (default P1203Pv)
            Pq -- used audio visual integration module (default P1203Pq)
            quiet {bool} -- squelch all logger messages
            amendment_1_audiovisual {bool} -- enable the fix from Amendment 1, Clause 8.2 (default: False)
            amendment_1_stalling {bool} -- enable the fix from Amendment 1, Clause 8.4 (default: False)
            amendment_1_app_2 {bool} -- enable the simplified model from Amendment 1, Appendix 2 (default: False),
                                        ensuring compatibility with P.1204.3
        """
        self.input_report = input_report
        self.debug = debug

        self.audio = None
        self.video = None
        self.integration = None
        self.overall_result = None
        self.Pa = Pa if Pa is not None else P1203Pa
        self.Pv = Pv if Pv is not None else P1203Pv
        self.Pq = Pq if Pq is not None else P1203Pq

        self.amendment_1_audiovisual = amendment_1_audiovisual
        self.amendment_1_stalling = amendment_1_stalling
        self.amendment_1_app_2 = amendment_1_app_2

        if quiet:
            logger.setLevel(logging.CRITICAL)

    def calculate_pa(self, fast_mode=False):
        """
        Calculate Pa and return audio dict

        Keyword Arguments:
            fast_mode {bool} -- use fast mode (default: {False})

        Returns:
            dict {
                "audio": {
                    "streamId": i11["streamId"],
                    "O21": o21,
                }
            }
        """
        logger.debug("Calculating audio scores ...")

        # estimate quality from segments
        if "I11" in self.input_report.keys():
            segments = []
            if "segments" not in self.input_report["I11"]:
                logger.warning("No audio segments specified")
            else:
                segments = self.input_report["I11"]["segments"]

            stream_id = None
            try:
                stream_id = self.input_report["I11"]["streamId"]
            except Exception:
                logger.warning("No stream ID specified")

            self.audio = self.Pa(segments, stream_id).calculate(fast_mode=fast_mode)

        # use existing O21 scores
        elif "O21" in self.input_report.keys():
            self.audio = {"audio": {"streamId": -1, "O21": self.input_report["O21"]}}

        else:
            raise P1203StandaloneError("No 'I11' or 'O21' found in input report")

        if self.debug:
            print(json.dumps(self.audio, indent=True, sort_keys=True))

        return self.audio

    def calculate_pv(self, fast_mode=False):
        """
        Calculate Pv and return video dict

        Keyword Arguments:
            fast_mode {bool} -- use fast mode (default: {False})

        Returns:
            dict {
                "video": {
                    "streamId": i13["streamId"],
                    "O22": o22,
                }
            }
        """
        logger.debug("Calculating video scores ...")

        # estimate quality from segments
        if "I13" in self.input_report.keys():
            if "segments" not in self.input_report["I13"]:
                raise P1203StandaloneError(
                    "No video segments defined, check your input format"
                )

            segments = self.input_report["I13"]["segments"]

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

            device = "pc"
            try:
                device = self.input_report["IGen"]["device"]
            except Exception:
                logger.warning("Device not defined in input report, assuming PC")

            self.video = self.Pv(
                segments=segments,
                display_res=display_res,
                device=device,
                stream_id=stream_id,
            ).calculate(fast_mode=fast_mode)

        # use existing O22 scores
        elif "O22" in self.input_report.keys():
            self.video = {"video": {"streamId": -1, "O22": self.input_report["O22"]}}

        else:
            raise P1203StandaloneError("No 'I13' or 'O22' found in input report")

        if self.debug:
            print(json.dumps(self.video, indent=True, sort_keys=True))

        return self.video

    def calculate_integration(self):
        """
        Calculate Pq and return integration dict

        Returns:
            {
                "O23": O23,
                "O34": O34.tolist(),
                "O35": float(O35),
                "O46": float(O46)
            }
        """
        logger.debug("Calculating integration module ...")

        stalling = []
        if (
            "I23" in self.input_report.keys()
            and "stalling" in self.input_report["I23"].keys()
            and self.input_report["I23"]["stalling"] is not None
        ):
            stalling = self.input_report["I23"]["stalling"]

        device = "pc"
        try:
            device = self.input_report["IGen"]["device"]
        except Exception:
            logger.warning("Device not defined in input report, assuming PC")

        l_buff = [x[1] for x in stalling]
        if stalling and len(stalling[0]) and stalling[0][0] != 0:
            p_buff = [x[0] - stalling[0][0] for x in stalling]
            logger.warning(
                "First stalling event does not start at 0, will shift the position of stalling events. "
                "If you want to avoid this, add a stalling event at position 0 with duration 0. "
                "New stalling positions are: {}".format(p_buff)
            )
        else:
            p_buff = [x[0] for x in stalling]

        if not self.audio:
            raise P1203StandaloneError(
                "No audio scores found, please run calculate_pa() first"
            )
        if not self.video:
            raise P1203StandaloneError(
                "No video scores found, please run calculate_pv() first"
            )

        self.integration = self.Pq(
            O21=self.audio["audio"]["O21"],
            O22=self.video["video"]["O22"],
            l_buff=l_buff,
            p_buff=p_buff,
            device=device,
            amendment_1_audiovisual=self.amendment_1_audiovisual,
            amendment_1_stalling=self.amendment_1_stalling,
            amendment_1_app_2=self.amendment_1_app_2,
        ).calculate()

        return self.integration

    def calculate_complete(
        self,
        print_intermediate=False,
        calculate_pa_kwargs={},
        calculate_pv_kwargs={},
        calculate_integration_kwargs={},
    ):
        """
        Calculates P.1203 scores based on JSON input file

        Arguments:
            print_intermediate {bool} -- print and return intermediate O.21/O.22 values in output dict
            calculate_pa_kwargs {dict} -- kwargs to pass to Pa.calculate()
            calculate_pv_kwargs {dict} -- kwargs to pass to Pv.calculate()
            calculate_integration_kwargs {dict} -- kwargs to pass to Pq.calculate()

        Returns:
            dict -- integration output according to spec:
                {
                    "streamId": video["video"]["streamId"],
                    "mode": video["video"]["mode"],
                    "O23": integration_result["O23"],
                    "O34": integration_result["O34"],
                    "O35": integration_result["O35"],
                    "O46": integration_result["O46"],
                    "O21": audio["audio"]["O21"], (only if print_intermediate is True)
                    "O22": audio["video"]["O22"], (only if print_intermediate is True)
             }
        """
        self.calculate_pa(**calculate_pa_kwargs)
        self.calculate_pv(**calculate_pv_kwargs)
        self.calculate_integration(**calculate_integration_kwargs)

        if not self.audio:
            raise P1203StandaloneError(
                "No audio scores found, has calculate_pa() failed?"
            )
        if not self.video:
            raise P1203StandaloneError(
                "No video scores found, has calculate_pv() failed?"
            )

        # try setting stream ID from input video
        stream_id = -1
        mode = -1
        try:
            stream_id = self.video["video"]["streamId"]
            mode = self.video["video"]["mode"]
        except Exception:
            pass

        if not self.integration:
            raise P1203StandaloneError(
                "No integration scores found, has calculate_integration() failed?"
            )

        # integration usually consists of O23, O34, O35, O46
        self.overall_result = self.integration

        self.overall_result["streamId"] = stream_id
        self.overall_result["mode"] = mode
        self.overall_result["date"] = datetime.datetime.today().isoformat()

        if print_intermediate:
            self.overall_result["O21"] = self.audio["audio"]["O21"]
            self.overall_result["O22"] = self.video["video"]["O22"]

        return self.overall_result
