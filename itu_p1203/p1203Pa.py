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

import math
from functools import lru_cache

from . import log, utils
from .errors import P1203StandaloneError
from .measurementwindow import MeasurementWindow

logger = log.setup_custom_logger("itu_p1203")


class P1203Pa(object):

    VALID_CODECS = ["mp2", "ac3", "aaclc", "heaac"]
    COEFFS_A1 = {"mp2": 100.00, "ac3": 100.00, "aaclc": 100.00, "heaac": 100.00}
    COEFFS_A2 = {"mp2": -0.02, "ac3": -0.03, "aaclc": -0.05, "heaac": -0.11}
    COEFFS_A3 = {"mp2": 15.48, "ac3": 15.70, "aaclc": 14.60, "heaac": 20.06}

    @lru_cache()
    def audio_model_function(self, codec, bitrate):
        """
        Calculate MOS value based on codec and bitrate.

        - codec: used audio codec, must be one of mp2, ac3, aaclc, heaac
        - bitrate: used audio bitrate in kBit/s
        """
        if codec not in self.VALID_CODECS:
            raise P1203StandaloneError(
                "Unsupported audio codec {}, use any of {}".format(
                    codec, self.VALID_CODECS
                )
            )

        q_cod_a = (
            self.COEFFS_A1[codec] * math.exp(self.COEFFS_A2[codec] * bitrate)
            + self.COEFFS_A3[codec]
        )
        qa = 100 - q_cod_a
        mos_audio = utils.mos_from_r(qa)
        return mos_audio

    def model_callback(self, output_sample_timestamp, frames):
        """
        Function that receives frames from measurement window, to call the model
        on and produce scores.

        Arguments:
            output_sample_timestamp {int} -- timestamp of the output sample (1, 2, ...)
            frames {list} -- list of frames from measurement window
        """
        output_sample_index = [
            i for i, f in enumerate(frames) if f["dts"] < output_sample_timestamp
        ][-1]
        chunk = utils.get_chunk(
            frames, output_sample_index, type="audio", onlyfirst=True
        )

        # since for audio, only codec and bitrate change per chunk, we don't need individual frame stats,
        # we can can just calculate the score for the whole chunk
        first_frame = chunk[0]
        score = self.audio_model_function(first_frame["codec"], first_frame["bitrate"])
        self.o21.append(score)

    def _calculate_with_measurementwindow(self):
        """
        Calculate the score with the measurement window (standardized) approach.
        """

        measurementwindow = MeasurementWindow()
        measurementwindow.set_score_callback(self.model_callback)

        dts = 0
        warning_shown = False
        for segment in self.segments:
            # generate 100 audio samples per second, should be enough for precision
            sample_rate = 100
            num_frames = int(segment["duration"] * sample_rate)
            frame_duration = 1.0 / sample_rate

            if segment["codec"] == "aac":
                if not warning_shown:
                    logger.warning(
                        "Assumed that 'aac' means 'aaclc'; please fix your input file"
                    )
                    warning_shown = True
                segment["codec"] = "aaclc"

            for i in range(int(num_frames)):
                frame = {
                    "duration": frame_duration,
                    "dts": dts,
                    "bitrate": segment["bitrate"],
                    "codec": segment["codec"],
                }
                if "representation" in segment.keys():
                    frame.update({"representation": segment["representation"]})
                # feed frame to MeasurementWindow
                measurementwindow.add_frame(frame)
                dts += frame_duration
        measurementwindow.stream_finished()

    def _calculate_fast_mode(self):
        """
        Calculate the score using the fast mode.
        This calculates one O21 value per chunk and repeats it for floor(s) where s = segment duration.
        """
        for segment in self.segments:
            score = self.audio_model_function(segment["codec"], segment["bitrate"])
            self.o21.extend([score] * math.floor(segment["duration"]))

    def calculate(self, fast_mode=False):
        """
        Calculate audio MOS

        Returns:
           dict {
                "audio": {
                    "streamId": i11["streamId"],
                    "O21": o21,
                }
            }

        Parameters:
            fast_mode {bool} -- if True, use the fast mode of the model (less precise)
        """
        utils.check_segment_continuity(self.segments, "audio")

        if fast_mode:
            logger.warning(
                "Using fast mode of the model, results may not be accurate to the second"
            )
            self._calculate_fast_mode()
        else:
            self._calculate_with_measurementwindow()

        return {
            "audio": {
                "streamId": self.stream_id,
                "O21": self.o21,
            }
        }

    def __init__(self, segments, stream_id=None):
        """
        Initialize Pa model with input JSON data
        """
        self.segments = segments
        self.stream_id = stream_id
        self.o21 = []


if __name__ == "__main__":
    print("this is just a module")
