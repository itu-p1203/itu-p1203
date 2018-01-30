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

from itu_p1203 import log
import itu_p1203.utils as utils
from itu_p1203.measurementwindow import MeasurementWindow

logger = log.setup_custom_logger('main')


class P1203Pa(object):
    @staticmethod
    def audio_model_function(codec, bitrate):
        """
        Calculate MOS value based on codec and bitrate.

        - codec: used audio codec, must be one of mp2, ac3, aaclc, heaac
        - bitrate: used audio bitrate in kBit/s
        """
        codec = codec.lower()
        if codec == "aac":
            logger.debug("assumed that 'aac' means 'aaclc'; please fix your input file")
            codec = "aaclc"
        a1 = {'mp2': 100.00, 'ac3': 100.00, 'aaclc': 100.00, 'heaac': 100.00}
        a2 = {'mp2': -0.02, 'ac3': -0.03, 'aaclc': -0.05, 'heaac': -0.11}
        a3 = {'mp2': 15.48, 'ac3': 15.70, 'aaclc': 14.60, 'heaac': 20.06}
        q_cod_a = a1[codec] * math.exp(a2[codec] * bitrate) + a3[codec]
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
        output_sample_index = [i for i, f in enumerate(frames) if f["dts"] < output_sample_timestamp][-1]
        chunk = utils.get_chunk(frames, output_sample_index, type="audio")

        # since for audio, only codec and bitrate change per chunk, we don't need individual frame stats,
        # we can can just calculate the score for the whole chunk
        first_frame = chunk[0]
        score = P1203Pa.audio_model_function(first_frame["codec"], first_frame["bitrate"])
        self.o21.append(score)

    def calculate(self):
        """
        Calculate audio MOS

        Returns:
           dict {
                "audio": {
                    "streamId": i11["streamId"],
                    "O21": o21,
                }
            }
        """
        utils.check_segment_continuity(self.segments)

        measurementwindow = MeasurementWindow()
        measurementwindow.set_score_callback(self.model_callback)

        dts = 0
        for segment in self.segments:
            # generate 100 audio samples per second, should be enough for precision
            sample_rate = 100
            num_frames = int(segment["duration"] * sample_rate)
            frame_duration = 1.0 / sample_rate
            for i in range(int(num_frames)):
                frame = {
                    "duration": frame_duration,
                    "dts": dts,
                    "bitrate": segment["bitrate"],
                    "codec": segment["codec"]
                }
                if "representation" in segment.keys():
                    frame.update({"representation": segment["representation"]})
                # feed frame to MeasurementWindow
                measurementwindow.add_frame(frame)
                dts += frame_duration
        measurementwindow.stream_finished()

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


if __name__ == '__main__':
    print("this is just a module")
