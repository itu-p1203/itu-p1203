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
import numpy as np
import json

from . import log
from . import utils
from .errors import P1203StandaloneError
from .measurementwindow import MeasurementWindow

logger = log.setup_custom_logger('main')


class P1203Pv(object):
    VIDEO_COEFFS = (4.66, -0.07, 4.06, 0.642, -2.293, 0.186)
    MOBILE_COEFFS = (0.7, 0.85)

    # non-standard codec mapping
    COEFFS_VP9 = [-0.04129014, 0.30953836, 0.32314399, 0.5284358]
    COEFFS_H265 = [-0.05196039, 0.39430046, 0.17486221, 0.50008018]

    @staticmethod
    def degradation_due_to_upscaling(coding_res, display_res):
        """
        Degradation due to upscaling
        """
        scale_factor = display_res / coding_res
        scale_factor = max(scale_factor, 1)
        u1 = 72.61
        u2 = 0.32
        deg_scal_v = u1 * np.log10(u2 * (scale_factor - 1.0) + 1.0)
        deg_scal_v = utils.constrain(deg_scal_v, 0.0, 100.0)
        return deg_scal_v

    @staticmethod
    def degradation_due_to_frame_rate_reduction(deg_cod_v, deg_scal_v, framerate):
        """
        Degradation due to frame rate reduction
        """
        t1 = 30.98
        t2 = 1.29
        t3 = 64.65
        deg_frame_rate_v = 0
        if framerate < 24:
            deg_frame_rate_v = (100 - deg_cod_v - deg_scal_v) * (t1 - t2 * framerate) / (t3 + framerate)
        deg_frame_rate_v = utils.constrain(deg_frame_rate_v, 0.0, 100.0)
        return deg_frame_rate_v

    @staticmethod
    def degradation_integration(mos_cod_v, deg_cod_v, deg_scal_v, deg_frame_rate_v):
        """
        Integrate the three degradations
        """
        deg_all = utils.constrain(deg_cod_v + deg_scal_v + deg_frame_rate_v, 0.0, 100.0)
        qv = 100 - deg_all
        return utils.mos_from_r(qv)

    @staticmethod
    def video_model_function_mode0(coding_res, display_res, bitrate_kbps_segment_size, framerate):
        """
        Mode 0 model

        Arguments:
            coding_res {int} -- number of pixels in coding resolution
            display_res {int} -- number of display resolution pixels
            bitrate_kbps_segment_size {float} -- bitrate in kBit/s
            framerate {float} -- frame rate

        Returns:
            float -- O22 score
        """

        # compression degradation
        a1 = 11.9983519
        a2 = -2.99991847
        a3 = 41.2475074001
        a4 = 0.13183165961
        q1 = 4.66
        q2 = -0.07
        q3 = 4.06
        quant = a1 + a2 * np.log(a3 + np.log(bitrate_kbps_segment_size) + np.log(bitrate_kbps_segment_size * bitrate_kbps_segment_size / (coding_res * framerate) + a4))
        mos_cod_v = q1 + q2 * np.exp(q3 * quant)
        mos_cod_v = utils.constrain(mos_cod_v, 1.0, 5.0)
        deg_cod_v = 100.0 - utils.r_from_mos(mos_cod_v)
        deg_cod_v = utils.constrain(deg_cod_v, 0.0, 100.0)

        # scaling, framerate degradation
        deg_scal_v = P1203Pv.degradation_due_to_upscaling(coding_res, display_res)
        deg_frame_rate_v = P1203Pv.degradation_due_to_frame_rate_reduction(deg_cod_v, deg_scal_v, framerate)

        # degradation integration
        score = P1203Pv.degradation_integration(mos_cod_v, deg_cod_v, deg_scal_v, deg_frame_rate_v)

        logger.debug(json.dumps({
            'coding_res': round(coding_res, 2),
            'display_res': round(display_res, 2),
            'bitrate_kbps_segment_size': round(bitrate_kbps_segment_size, 2),
            'framerate': round(framerate, 2),
            'mos_cod_v': round(mos_cod_v, 2),
            'deg_cod_v': round(deg_cod_v, 2),
            'deg_scal_v': round(deg_scal_v, 2),
            'deg_frame_rate_v': round(deg_frame_rate_v, 2),
            'score': round(score, 2)
        }, indent=True))

        return score

    @staticmethod
    def video_model_function_mode1(coding_res, display_res, bitrate_kbps_segment_size, framerate, frames, iframe_ratio=None):
        """
        Mode 1 model

        Arguments:
            coding_res {int} -- number of pixels in coding resolution
            display_res {int} -- number of display resolution pixels
            bitrate_kbps_segment_size {float} -- bitrate in kBit/s
            framerate {float} -- frame rate
            frames {list} -- frames
            iframe_ratio {float} -- iframe ratio, only for debugging

        Returns:
            float -- O22 score
        """
        # compression degradation
        a1 = 5.00011566
        a3 = 41.3585049
        a2 = -1.19630824
        a4 = 0
        q1 = 4.66
        q2 = -0.07
        q3 = 4.06
        quant = a1 + a2 * np.log(a3 + np.log(bitrate_kbps_segment_size) + np.log(bitrate_kbps_segment_size * bitrate_kbps_segment_size / (coding_res * framerate) + a4))
        mos_cod_v = q1 + q2 * np.exp(q3 * quant)
        mos_cod_v = utils.constrain(mos_cod_v, 1.0, 5.0)

        # if iframe ratio is already set (debug mode)

        # complexity correction
        c0 = -0.91562479
        c1 = 0
        c2 = -3.28579526
        c3 = 20.4098663
        if not iframe_ratio:
            i_sizes = []
            noni_sizes = []
            for frame in frames:
                frame_size = utils.calculate_compensated_size(frame["type"], frame["size"], frame["dts"])
                if frame["type"] == "I":
                    i_sizes.append(int(frame_size))
                else:
                    noni_sizes.append(int(frame_size))

            # only compute ratio when there are frames of both types
            if i_sizes and noni_sizes:
                iframe_ratio = np.mean(i_sizes) / np.mean(noni_sizes)
            else:
                iframe_ratio = 0
        complexity = utils.sigmoid(c0, c1, c2, c3, iframe_ratio)
        mos_cod_v += complexity

        deg_cod_v = 100.0 - utils.r_from_mos(mos_cod_v)
        deg_cod_v = utils.constrain(deg_cod_v, 0.0, 100.0)

        # scaling, framerate degradation
        deg_scal_v = P1203Pv.degradation_due_to_upscaling(coding_res, display_res)
        deg_frame_rate_v = P1203Pv.degradation_due_to_frame_rate_reduction(deg_cod_v, deg_scal_v, framerate)

        # degradation integration
        score = P1203Pv.degradation_integration(mos_cod_v, deg_cod_v, deg_scal_v, deg_frame_rate_v)

        logger.debug(json.dumps({
            'coding_res': round(coding_res, 2),
            'display_res': round(display_res, 2),
            'bitrate_kbps_segment_size': round(bitrate_kbps_segment_size, 2),
            'framerate': round(framerate, 2),
            'mos_cod_v': round(mos_cod_v, 2),
            'deg_cod_v': round(deg_cod_v, 2),
            'iframe_ratio': round(iframe_ratio, 2),
            'complexity': round(complexity, 2),
            'deg_scal_v': round(deg_scal_v, 2),
            'deg_frame_rate_v': round(deg_frame_rate_v, 2),
            'score': round(score, 2)
        }, indent=True))

        return score

    @staticmethod
    def video_model_function_mode3(coding_res, display_res, framerate, frames, quant=None, avg_qp_per_frame=[]):
        """
        Mode 1 model

        Arguments:
            coding_res {int} -- number of pixels in coding resolution
            display_res {int} -- number of display resolution pixels
            framerate {float} -- frame rate
            frames {list} -- frames
            quant {float} -- quant parameter, only used for debugging [default: None]
            avg_qp_per_frame {list} -- average QP per frame, only used for debugging [default: []]
        Returns:
            float -- O22 score
        """

        if not quant:
            # iterate through all frames and collect information
            if not avg_qp_per_frame:
                sizes = []
                types = []
                qp_values = []
                for frame in frames:
                    frame_size = utils.calculate_compensated_size(frame["type"], frame["size"], frame["dts"])
                    sizes.append(int(frame_size))
                    qp_values.append(frame["qpValues"])

                    frame_type = frame["type"]
                    if frame_type not in ["I", "P", "B"]:
                        raise P1203StandaloneError("frame type " + str(frame_type) + " not valid; must be I/P/B")
                    types.append(frame_type)

                qppb = []
                for index, frame_type in enumerate(types):
                    if frame_type == "P" or frame_type == "B":
                        qppb.extend(qp_values[index])
                    elif frame_type == "I" and len(qppb) > 0:
                        if len(qppb) > 1:
                            # replace QP value of last P-frame before I frame with QP value of previous P-frame if there
                            # are more than one stored P frames
                            qppb[-1] = qppb[-2]
                        else:
                            # if there is only one stored P frame before I-frame, remove it
                            qppb = []
                avg_qp = np.mean(qppb)
            else:
                avg_qp = np.mean(avg_qp_per_frame)
            quant = avg_qp / 51.0

        mos_cod_v = P1203Pv.VIDEO_COEFFS[0] + P1203Pv.VIDEO_COEFFS[1] * math.exp(P1203Pv.VIDEO_COEFFS[2] * quant)
        mos_cod_v = max(min(mos_cod_v, 5), 1)
        deg_cod_v = 100 - utils.r_from_mos(mos_cod_v)
        deg_cod_v = max(min(deg_cod_v, 100), 0)

        # scaling, framerate degradation
        deg_scal_v = P1203Pv.degradation_due_to_upscaling(coding_res, display_res)
        deg_frame_rate_v = P1203Pv.degradation_due_to_frame_rate_reduction(deg_cod_v, deg_scal_v, framerate)

        # degradation integration
        score = P1203Pv.degradation_integration(mos_cod_v, deg_cod_v, deg_scal_v, deg_frame_rate_v)

        logger.debug(json.dumps({
            'coding_res': round(coding_res, 2),
            'display_res': round(display_res, 2),
            'framerate': round(framerate, 2),
            'quant': round(quant, 2),
            'mos_cod_v': round(mos_cod_v, 2),
            'deg_cod_v': round(deg_cod_v, 2),
            'deg_scal_v': round(deg_scal_v, 2),
            'deg_frame_rate_v': round(deg_frame_rate_v, 2),
            'score': round(score, 2)
        }, indent=True))

        return score

    def model_callback(self, output_sample_timestamp, frames):
        """
        Function that receives frames from measurement window, to call the model
        on and produce scores.

        Arguments:
            output_sample_timestamp {int} -- timestamp of the output sample (1, 2, ...)
            frames {list} -- list of all frames from measurement window
        """
        logger.debug("Output score at timestamp " + str(output_sample_timestamp))
        output_sample_index = [i for i, f in enumerate(frames) if f["dts"] < output_sample_timestamp][-1]

        # only get the relevant frames from the chunk
        frames = utils.get_chunk(frames, output_sample_index, type="video")

        first_frame = frames[0]
        if self.mode == 0:
            # average the bitrate for all of the segments
            bitrate = np.mean([f["bitrate"] for f in frames])
            score = P1203Pv.video_model_function_mode0(
                utils.resolution_to_number(first_frame["resolution"]),
                utils.resolution_to_number(self.display_res),
                bitrate,
                first_frame["fps"]
            )
            self.o22.append(score)

        elif self.mode == 1:
            # average the bitrate based on the frame sizes, as implemented
            # in submitted model code
            compensated_sizes = [
                utils.calculate_compensated_size(f["type"], f["size"], f["dts"]) for f in frames
            ]
            duration = np.sum([f["duration"] for f in frames])
            bitrate = np.sum(compensated_sizes) * 8 / duration / 1000
            score = P1203Pv.video_model_function_mode1(
                utils.resolution_to_number(first_frame["resolution"]),
                utils.resolution_to_number(self.display_res),
                bitrate,
                first_frame["fps"],
                frames
            )
            self.o22.append(score)

        elif self.mode == 3:
            score = P1203Pv.video_model_function_mode3(
                utils.resolution_to_number(first_frame["resolution"]),
                utils.resolution_to_number(self.display_res),
                first_frame["fps"],
                frames
            )

        else:
            raise P1203StandaloneError("Unsupported mode: {}".format(self.mode))

        # non-standard codec mapping
        codec_list = list(set([f["codec"] for f in frames]))
        if len(codec_list) > 1:
            raise P1203StandaloneError("Codec switching between frames in measurement window detected.")
        elif codec_list[0] != "h264":
            def correction_func(x, a, b, c, d):
                return a * x * x * x + b * x * x + c * x + d
            if codec_list[0] in ["hevc", "h265"]:
                coeffs = self.COEFFS_H265
            elif codec_list[0] == "vp9":
                coeffs = self.COEFFS_VP9
            else:
                logger.error("Unsupported codec in measurement window: {}".format(codec_list[0]))
            # compensate score
            score = max(1, min(correction_func(score, *coeffs), 5))

        self.o22.append(score)

    def calculate(self):
        """
        Calculate video MOS

        Returns:
            dict {
                "video": {
                    "streamId": i13["streamId"],
                    "mode": mode,
                    "O22": o22,
                }
            }
        """

        utils.check_segment_continuity(self.segments)

        measurementwindow = MeasurementWindow()
        measurementwindow.set_score_callback(self.model_callback)

        # check which mode can be run
        # TODO: make this switchable by command line option
        self.mode = 0
        for segment in self.segments:
            if "frames" not in segment.keys():
                self.mode = 0
                break
            if "frames" in segment:
                for frame in segment["frames"]:
                    if "frameType" not in frame.keys() or "frameSize" not in frame.keys():
                        raise P1203StandaloneError("Frame definition must have at least 'frameType' and 'frameSize'")
                    if "qpValues" in frame.keys():
                        self.mode = 3
                    else:
                        self.mode = 1
                        break

        logger.debug("Evaluating stream in mode " + str(self.mode))

        # check for differing or wrong codecs
        codecs = list(set([s["codec"] for s in self.segments]))
        for c in codecs:
            if c not in ["h264", "h265", "hevc", "vp9"]:
                raise P1203StandaloneError("Unsupported codec: {}".format(c))
            elif c != "h264":
                logger.warning("Non-standard codec used. O22 Output will not be ITU-T P.1203 compliant.")
            if self.mode != 0 and c != "h264":
                raise P1203StandaloneError("Non-standard codec calculation only possible with Mode 0.")

        # generate fake frames
        if self.mode == 0:
            dts = 0
            for segment in self.segments:
                num_frames = int(segment["duration"] * segment["fps"])
                frame_duration = 1.0 / segment["fps"]
                for i in range(int(num_frames)):
                    frame = {
                        "duration": frame_duration,
                        "dts": dts,
                        "bitrate": segment["bitrate"],
                        "codec": segment["codec"],
                        "fps": segment["fps"],
                        "resolution": segment["resolution"]
                    }
                    if "representation" in segment.keys():
                        frame.update({"representation": segment["representation"]})
                    # feed frame to MeasurementWindow
                    measurementwindow.add_frame(frame)
                    dts += frame_duration
            measurementwindow.stream_finished()

        # use frame info to infer frames and their DTS, add frame stats
        else:
            dts = 0
            for segment_index, segment in enumerate(self.segments):
                num_frames_assumed = int(segment["duration"] * segment["fps"])
                num_frames = len(segment["frames"])
                if num_frames != num_frames_assumed:
                    logger.warning("Segment specifies " + str(num_frames) + " frames but based on calculations, there should be " + str(num_frames_assumed))
                frame_duration = 1.0 / segment["fps"]
                for i in range(int(num_frames)):
                    frame = {
                        "duration": frame_duration,
                        "dts": dts,
                        "bitrate": segment["bitrate"],
                        "codec": segment["codec"],
                        "fps": segment["fps"],
                        "resolution": segment["resolution"],
                        "size": segment["frames"][i]["frameSize"],
                        "type": segment["frames"][i]["frameType"],
                    }
                    if "representation" in segment.keys():
                        frame.update({"representation": segment["representation"]})
                    if self.mode == 3:
                        qp_values = segment["frames"][i]["qpValues"]
                        if not qp_values:
                            raise P1203StandaloneError("No QP values for frame {i} of segment {segment_index}".format(**locals()))
                        frame["qpValues"] = qp_values
                    # feed frame to MeasurementWindow
                    measurementwindow.add_frame(frame)
                    dts += frame_duration
            measurementwindow.stream_finished()

        return {
            "video": {
                "streamId": self.stream_id,
                "mode": self.mode,
                "O22": self.o22,
            }
        }

    def __init__(self, segments, display_res="1920x1080", stream_id=None):
        """
        Initialize Pv model with input JSON data

        Arguments:
            segments {list} -- list of segments according to specification
            display_res {str} -- display resolution as "wxh" (default: "1920x1080")
            stream_id {str} -- stream ID (default: {None})
        """
        self.segments = segments
        self.display_res = display_res
        self.stream_id = stream_id
        self.o22 = []
        self.mode = None


if __name__ == '__main__':
    print("this is just a module")
