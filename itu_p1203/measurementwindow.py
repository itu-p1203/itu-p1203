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

from . import log
from .utils import get_chunk_hash

logger = log.setup_custom_logger("itu_p1203")


class MeasurementWindow:
    """
    Implements a sliding measurement window that can only hold a certain amount
    of frames depending on the summed up duration of each individual frame
    """

    def __init__(self):
        self.max_size = 20
        self._frames = []  # actual measurement window
        self._removed_frames = []  # removed old frames
        self._last_score_output_at = 0
        self._acc_frame_dur = (
            0  # accumulated frame duration inside the measurement window
        )
        self._acc_pvs_dur = 0  # current accumulated time at end of measurement window, for the entire PVS
        self._frames_added_cnt = 0
        self._half_window_size = int(self.max_size / 2)  # half of the window

    def set_score_callback(self, callback):
        """
        Sets the function that should be called on a model whenever a score
        needs to be calculated.

        The callback must take two arguments:
        - {float} output sample timestamp
        - {list} list of frames to calculate scores on
        """
        if not callable(callback):
            raise SystemExit(
                "Callback passed to set_score_callback is not a callable function"
            )
        self._score_callback = callback

    def _should_calculate_score(self):
        """
        Depending on the current status, should a score be output? This is called with every frame
        added to the measurement window.
        """
        # Beginning of filling the measurement window: When we reach 11 seconds, we can output the score for t=1
        if (
            self._last_score_output_at == 0
            and round(self._acc_pvs_dur, 5) < self._half_window_size + 1
        ):
            return False

        # Otherwise, we can start outputting scores, starting with t=1 using the window [0, 11]
        if self._acc_pvs_dur - self._half_window_size >= self._last_score_output_at + 1:
            next_score_output_at = self._last_score_output_at + 1
            if self._score_callback:
                logger.debug("Boundaries: " + str(self.get_boundaries()))
                self._score_callback(next_score_output_at, self._frames)
            self._last_score_output_at = next_score_output_at
            return True

        return False

    def add_frame(self, frame):
        """
        Adds a frame to the measurement window, removing older frames
        if necessary

        frame: dict with keys "duration" and "dts"
        """
        if not frame["duration"]:
            raise SystemExit("Frame added to measurement window had no duration")

        if self._acc_frame_dur + frame["duration"] > self.max_size:
            removed_frame = self._frames.pop(0)
            self._removed_frames.append(removed_frame)
            self._acc_frame_dur -= removed_frame["duration"]

        # pre-calculate chunk hashes
        frame["representation"] = (
            get_chunk_hash(frame, "audio")
            if "fps" not in frame
            else get_chunk_hash(frame, "video")
        )

        self._frames.append(frame)
        self._acc_frame_dur += frame["duration"]
        self._acc_pvs_dur += frame["duration"]

        # if a score should be calculated, tell the model that it should take
        # the frames and calculate the score.
        self._should_calculate_score()

    def stream_finished(self):
        """
        This should be called when the stream is finished, flushing the
        measurement window and eventually outputting the last score.
        """
        # Final score is only for full seconds, i.e. if total duration is
        # 180.23, then last score will be at 180.
        final_sample_timestamp = math.floor(self._acc_pvs_dur)

        # Minor bugfix: if in mode 0, rounding up would be better, do this instead.
        # This can happen if frames only sum up to 0.9999999 and not the next second.
        if self._acc_pvs_dur - final_sample_timestamp > 0.99:
            final_sample_timestamp = math.ceil(self._acc_pvs_dur)

        # The window is aat [160.23, 180.23] now
        # Next output timestamp is 171
        output_sample_timestamp = self._last_score_output_at + 1

        while output_sample_timestamp <= final_sample_timestamp:
            # Remove frames from the beginning of the window [160.23, 180.23]
            # until it fulfills condition [t-10, 180.23], i.e. [161, 180.23]
            removed_duration = 0
            while (
                round(self._frames[0]["dts"], 5)
                < output_sample_timestamp - self._half_window_size
            ):
                # print round(self._frames[0]["dts"], 5), output_sample_timestamp - self._half_window_size
                removed_frame = self._frames.pop(0)
                removed_duration += removed_frame["duration"]
                self._removed_frames.append(removed_frame)
                self._acc_frame_dur -= removed_frame["duration"]

            if self._score_callback:
                self._score_callback(output_sample_timestamp, self._frames)

            # output next score at 172, and so on
            output_sample_timestamp += 1
        return

    def get_frames(self):
        """
        Returns all frames within the measurement window.
        """
        return self._frames

    def length(self):
        """
        Returns the accumulated frame duration of the window
        """
        return self._acc_frame_dur

    def get_boundaries(self):
        """
        Return the DTS as [a, b] where a and b are the first and last frames
        """
        return (self._frames[0]["dts"], self._frames[-1]["dts"])

    def print_content(self):
        """
        Pretty-print the content of the measurement window for debugging
        """
        print("\t".join(["IDX", "TYPE", "SIZE", "PTS", "DTS", "DUR", "ACC"]))
        acc = 0

        for index, frame in enumerate(self._frames, start=1):
            if "type" in frame.keys() and frame["type"] is not None:
                f_type = frame["type"]
            else:
                f_type = "None"

            if "size" in frame.keys() and frame["size"] is not None:
                size = frame["size"]
            else:
                size = "None"

            if "pts" in frame.keys() and frame["pts"] != None:
                pts = str(format(round(frame["pts"], 4), ".4f"))
            else:
                pts = "None"

            if frame["dts"] != None:
                dts = str(format(round(frame["dts"], 4), ".4f"))
            else:
                dts = "None"

            duration = str(format(round(frame["duration"], 4), ".4f"))
            acc += frame["duration"]

            print(
                "\t".join(
                    [
                        str(index),
                        str(f_type),
                        str(size),
                        str(pts),
                        str(dts),
                        str(duration),
                        str(format(round(acc, 4), ".4f")),
                    ]
                )
            )
