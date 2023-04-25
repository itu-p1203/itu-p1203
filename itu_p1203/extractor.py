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

import argparse
import gzip
import json
import os
import re
import subprocess
import sys
import tempfile
from collections import OrderedDict
from fractions import Fraction

from . import utils


def average(x):
    if not isinstance(x, list):
        print_stderr("Cannot use average() on non-list!")
        sys.exit(1)
    if not x:
        return []
    return sum(x) / len(x)


def print_stderr(msg):
    print("EXTRACTOR: {}".format(msg), file=sys.stderr)


def run_command(cmd, dry_run=False, verbose=False):
    """
    Run a command directly
    """
    if dry_run or verbose:
        print_stderr("[cmd] " + " ".join(cmd))
        if dry_run:
            return

    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()

    if process.returncode == 0:
        return stdout.decode("utf-8"), stderr.decode("utf-8")
    else:
        print_stderr("[error] running command: {}".format(" ".join(cmd)))
        print_stderr(stderr.decode("utf-8"))
        sys.exit(1)


class Extractor(object):
    """
    Video extractor class based on ffmpeg/ffprobe
    """

    def __init__(self, input_files, mode, qp_logfile=None, use_average=False):
        """
        Initialize a new extractor

        Arguments:
            - input_files {list} -- files to analyze
            - mode {int} -- 0, 1, 2, or 3
        """
        self.input_files = input_files
        if mode not in [0, 1, 2, 3]:
            raise SystemExit("Wrong mode passed")
        self.mode = mode
        self.report = {}

        if len(input_files) > 1 and qp_logfile:
            print_stderr("QP Logfile only supported for one segment!")
            sys.exit(1)

        self.qp_logfile = qp_logfile
        self.use_average = use_average

    def extract(self):
        """
        Run the extraction and return the report as object
        """
        # lists that hold segment information for video, audio
        segment_list_video = []
        segment_list_audio = []

        # iterate over all files and extract info, append it to the lists
        current_timestamp = 0
        for segment in self.input_files:
            if not os.path.isfile(segment):
                print_stderr("Input file " + str(segment) + " does not exist")
                sys.exit(1)

            # extract the lines from this one segment
            (
                segment_info_video,
                segment_info_audio,
                duration,
            ) = Extractor.get_segment_info_lines(
                segment,
                mode=self.mode,
                timestamp=current_timestamp,
                qp_logfile=self.qp_logfile,
                use_average=self.use_average,
            )
            segment_list_video.append(segment_info_video)
            if segment_info_audio:
                segment_list_audio.append(segment_info_audio)

            # increase pointer to start timestamp
            current_timestamp += duration

        report = {
            "IGen": {
                "displaySize": "1920x1080",
                "device": "pc",
                "viewingDistance": "150cm",
            },
            "I11": {"streamId": 42, "segments": segment_list_audio},
            "I13": {"streamId": 42, "segments": segment_list_video},
            "I23": {"streamId": 42, "stalling": []},
        }
        self.report = report
        return report

    @staticmethod
    def get_tempfilename():
        """
        Return a temporary filename
        """
        tmp = tempfile.NamedTemporaryFile(delete=False)
        tmp.close()
        return tmp.name

    @staticmethod
    # https://stackoverflow.com/q/41525690
    def _file_line_gen(filename):
        if filename.endswith(".gz"):
            open_fn = gzip.open
        else:
            open_fn = open

        with open_fn(filename, "rb") as f:
            for line in f:
                yield line

    @staticmethod
    def _parse_qp_data(logfile, use_average=False):
        """
        Efficient parsing of the data, yields per-frame data.
        """
        frame_index = -1
        first_frame_found = False
        has_current_frame_data = False

        frame_type = None
        frame_size = None
        frame_qp_values = []

        for line in Extractor._file_line_gen(logfile):
            line = line.decode("utf-8").strip()
            # skip all non-relevant lines
            if (
                "[h264" not in line
                and "[mpeg2video" not in line
                and "pkt_size" not in line
            ):
                continue

            # skip irrelevant other lines
            if (
                "nal_unit_type" in line
                or "Reinit context" in line
                or "Skipping" in line
            ):
                continue

            # start a new frame
            if "New frame" in line:
                if has_current_frame_data:
                    # yield the current frame
                    frame_data = {"frameType": frame_type, "frameSize": frame_size}

                    if use_average:
                        frame_data["qpValues"] = [average(frame_qp_values)]
                    else:
                        frame_data["qpValues"] = frame_qp_values

                    yield frame_data

                frame_type = line[-1]
                if frame_type not in ["I", "P", "B"]:
                    print_stderr(
                        "Wrong frame type parsed: "
                        + str(frame_type)
                        + "\n Offending LINE : "
                        + line
                    )
                    continue

                first_frame_found = True

                frame_index += 1
                # initialize empty for the moment
                frame_qp_values = []
                frame_size = 0
                has_current_frame_data = True
                continue

            if not first_frame_found:
                # continue parsing
                continue

            if ("[h264" in line or "[mpeg2video" in line) and "pkt_size" not in line:
                if (
                    set(line.split("] ")[1]) - set(" 0123456789PAiIdDgGS><X+-|?=")
                    != set()
                ):
                    # this line contains something that is not a qp value
                    continue

                # Now we have a line with qp values.
                # Strip the first part off the string, e.g.
                #   [h264 @ 0x7f9fb4806e00] 25i  26i  25i  30i  25I  25i  25i  25i  28i  26i  25I  26i  28i  32i  25i  25I  25i  25i  28i  26i
                # becomes:
                #   25i  26i  25i  30i  25I  25i  25i  25i  28i  26i  25I  26i  28i  32i  25i  25I  25i  25i  28i  26i
                #   [h264 @ 0x7fadf2008000] 1111111111111111111111111111111111111111
                # OR
                # becomes:
                #   1111111111111111111111111111111111111111
                # Note:
                # Single digit qp values are padded with a leading space e.g.:
                # [h264 @ 0x7fadf2008000]  1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1
                raw_values = re.sub(r"\[[\w\s@]+\]\s", "", line)
                # remove the leading space in case of single digit qp values
                line_qp_values = [
                    int(raw_values[i : i + 2].lstrip())
                    for i in range(0, len(raw_values), 2)
                ]
                frame_qp_values.extend(line_qp_values)
                continue
            if "pkt_size" in line:
                frame_size = int(re.findall(r"\d+", line[line.rfind("pkt_size") :])[0])

        # yield last frame
        if has_current_frame_data:
            frame_data = {"frameType": frame_type, "frameSize": frame_size}

            if use_average:
                frame_data["qpValues"] = [average(frame_qp_values)]
            else:
                frame_data["qpValues"] = frame_qp_values
            yield frame_data

    @staticmethod
    def parse_qp_data(logfile, use_average=False):
        """
        Parse data from the QP logfile that ffmpeg-debug-qp generates.
        Returns a list of frame information.
        """
        return list(Extractor._parse_qp_data(logfile, use_average))

    @staticmethod
    def get_video_frame_info_ffmpeg_debug_qp(
        segment, qp_logfile=None, use_average=False
    ):
        """
        Obtain the video frame info using the ffmpeg-debug-qp script.

        Return keys:
            - `frame_type`: `I`, `P`, `B`
            - `size`: Size of the packet in bytes (including SPS, PPS for first frame, and AUD units for subsequent frames)
            - `qpValues`: List of QP values
        """
        if qp_logfile:
            if os.path.isfile(qp_logfile):
                return Extractor.parse_qp_data(qp_logfile, use_average)
            else:
                print_stderr(
                    "Logfile "
                    + str(qp_logfile)
                    + " not found! Falling back to ffmpeg-debug-qp parsing."
                )

        # try to get from source distribution
        ffmpeg_debug_script = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__), "..", "ffmpeg-debug-qp", "ffmpeg_debug_qp"
            )
        )

        if not os.path.isfile(ffmpeg_debug_script):

            # else, try to get from PATH
            ffmpeg_debug_script = utils.which("ffmpeg_debug_qp")

            if not ffmpeg_debug_script:
                print_stderr(
                    "Cannot find ffmpeg_debug_qp, neither in the subfolder 'ffmpeg-debug-qp', nor in your $PATH. "
                    + "Please install from https://github.com/slhck/ffmpeg-debug-qp"
                )
                sys.exit(1)

        tmp_file_debug_output = Extractor.get_tempfilename()

        # Extract QP values from ffmpeg
        extract_cmd = [ffmpeg_debug_script, segment]
        print_stderr("Running command to extract QPs ...")
        print_stderr(extract_cmd)

        try:
            with open(tmp_file_debug_output, "wb") as out_f:
                subprocess.run(extract_cmd, stderr=out_f)
        except Exception as e:
            print_stderr("Error running ffmpeg_debug_qp: " + str(e))
            sys.exit(1)

        try:
            data = Extractor.parse_qp_data(tmp_file_debug_output, use_average)
        except Exception as e:
            raise e
        finally:
            os.remove(tmp_file_debug_output)

        return data

    @staticmethod
    def get_video_frame_info_ffprobe(segment, info_type="packet"):
        """
        Return a list of OrderedDicts with video frame info, in decoding or presentation order
        info_type: "packet" or "frame", if packet: decoding order, if frame: presentation order

        Return keys:
            - `frame_type`: `I` or `Non-I` (for decoding order) or `I`, `P`, `B` (for presentation order)
            - `dts`: DTS of the frame (only for decoding order)
            - `pts`: PTS of the frame
            - `size`: Size of the packet in bytes (including SPS, PPS for first frame, and AUD units for subsequent frames)
            - `duration`: Duration of the frame in `s.msec`
        """
        if info_type == "packet":
            cmd = [
                "ffprobe",
                "-loglevel",
                "error",
                "-select_streams",
                "v",
                "-show_packets",
                "-show_entries",
                "packet=pts_time,dts_time,duration_time,size,flags",
                "-of",
                "json",
                segment,
            ]
        elif info_type == "frame":
            cmd = [
                "ffprobe",
                "-loglevel",
                "error",
                "-select_streams",
                "v",
                "-show_frames",
                "-show_entries",
                "frame=pkt_pts_time,pkt_dts_time,pkt_duration_time,pkt_size,pict_type",
                "-of",
                "json",
                segment,
            ]
        else:
            print_stderr("wrong info type, can be 'packet' or 'frame'")
            sys.exit(1)

        stdout, _ = run_command(cmd)
        info = json.loads(stdout)[info_type + "s"]

        # Assemble info into OrderedDict
        if info_type == "packet":
            ret = []
            for packet_info in info:
                frame_type = "I" if packet_info["flags"] == "K_" else "Non-I"
                if "dts_time" in packet_info:
                    dts = packet_info["dts_time"]
                else:
                    dts = "NaN"
                ret.append(
                    OrderedDict(
                        [
                            ("frame_type", frame_type),
                            ("dts", dts),
                            ("size", packet_info["size"]),
                            ("duration", packet_info["duration_time"]),
                        ]
                    )
                )
        elif info_type == "frame":
            ret = []
            for frame_info in info:
                if "pts_time" in frame_info:
                    pts = frame_info["pts_time"]
                else:
                    pts = "NaN"
                ret.append(
                    OrderedDict(
                        [
                            ("frame_type", frame_info["pict_type"]),
                            ("pts", pts),
                            ("size", frame_info["pkt_size"]),
                            ("duration", frame_info["pkt_duration_time"]),
                        ]
                    )
                )
        else:
            # cannot happen
            pass
        return ret

    @staticmethod
    def get_format_info(segment):
        """
        Get info about the segment, as shown by ffprobe "-show_format"

        Returns a dict, with the keys:
        - `nb_streams`
        - `nb_programs`
        - `format_name`
        - `format_long_name`
        - `start_time`
        - `duration`
        - `size`
        - `bit_rate`
        - `probe_score`
        """
        cmd = ["ffprobe", "-loglevel", "error", "-show_format", "-of", "json", segment]
        stdout, _ = run_command(cmd)
        info = json.loads(stdout)["format"]

        # conversions
        info["nb_streams"] = int(info["nb_streams"])
        info["nb_programs"] = int(info["nb_programs"])
        info["duration"] = float(info["duration"])
        info["size"] = int(info["size"])
        try:
            info["bit_rate"] = int(info["bit_rate"])
        except KeyError:
            info["bit_rate"] = 0

        return info

    @staticmethod
    def get_segment_info(segment):
        """
        Get info about the segment, as shown by ffprobe "-show_streams"

        Returns an OrderedDict, with the keys:
        - `segment_filename`: Basename of the segment file
        - `file_size`: Size of the file in bytes
        - `video_duration`: Duration of the video in `s.msec`
        - `video_frame_rate`: Framerate in Hz
        - `video_bitrate`: Bitrate of the video stream in kBit/s
        - `video_width`: Width in pixels
        - `video_height`: Height in pixels
        - `video_codec`: Video codec (`h264`, `hevc`, `vp9`)
        - `audio_duration`: Duration of the audio in `s.msec`
        - `audio_sample_rate`: Audio sample rate in Hz
        - `audio_codec`: Audio codec name (`aac`)
        - `audio_bitrate`: Bitrate of the video stream in kBit/s
        """
        segment_size = os.path.getsize(segment)

        cmd = [
            "ffprobe",
            "-loglevel",
            "error",
            "-show_streams",
            "-show_format",
            "-of",
            "json",
            segment,
        ]
        stdout, _ = run_command(cmd)
        info = json.loads(stdout)

        has_video = False
        has_audio = False
        for stream_info in info["streams"]:
            if stream_info["codec_type"] == "video":
                video_info = stream_info
                has_video = True
            elif stream_info["codec_type"] == "audio":
                audio_info = stream_info
                has_audio = True

        if not has_video:
            print("[warn] No video stream found in segment", file=sys.stderr)
        ret = OrderedDict()
        if has_video:
            if "duration" in video_info:
                video_duration = float(video_info["duration"])
            elif "tags" in video_info and "DURATION" in video_info["tags"]:
                duration_str = video_info["tags"]["DURATION"]
                hms, msec = duration_str.split(".")
                total_dur = sum(
                    int(x) * 60**i for i, x in enumerate(reversed(hms.split(":")))
                )
                video_duration = total_dur + float("0." + msec)
            elif "duration" in info["format"]:
                print_stderr(
                    "Warning: could not extract video duration from stream info, use format entry "
                    + str(segment)
                )
                video_duration = float(info["format"]["duration"])
            else:
                video_duration = None
                print_stderr(
                    "Warning: could not extract video duration from " + str(segment)
                )

            if "bit_rate" in video_info:
                video_bitrate = round(float(video_info["bit_rate"]) / 1024.0, 2)
            else:
                # fall back to calculating from accumulated frame duration
                stream_size = Extractor.get_stream_size(segment)
                video_bitrate = round((stream_size * 8 / 1024.0) / video_duration, 2)

            ret.update(
                OrderedDict(
                    [
                        ("segment_filename", segment),
                        ("file_size", segment_size),
                        ("video_duration", video_duration),
                        (
                            "video_frame_rate",
                            float(Fraction(video_info["r_frame_rate"])),
                        ),
                        ("video_bitrate", video_bitrate),
                        ("video_width", video_info["width"]),
                        ("video_height", video_info["height"]),
                        ("video_codec", video_info["codec_name"]),
                    ]
                )
            )

        if has_audio:
            if "duration" in audio_info:
                audio_duration = float(audio_info["duration"])
            elif "tags" in audio_info and "DURATION" in audio_info["tags"]:
                duration_str = audio_info["tags"]["DURATION"]
                hms, msec = duration_str.split(".")
                total_dur = sum(
                    int(x) * 60**i for i, x in enumerate(reversed(hms.split(":")))
                )
                audio_duration = total_dur + float("0." + msec)
            elif "duration" in info["format"]:
                print_stderr(
                    "Warning: could not extract audio duration from stream info, use format entry "
                    + str(segment)
                )
                audio_duration = float(info["format"]["duration"])
            else:
                audio_duration = None
                print_stderr(
                    "Warning: could not extract audio duration from " + str(segment)
                )

            if "bit_rate" in audio_info:
                audio_bitrate = round(float(audio_info["bit_rate"]) / 1024.0, 2)
            else:
                # fall back to calculating from accumulated frame duration
                stream_size = Extractor.get_stream_size(segment, stream_type="audio")
                audio_bitrate = round((stream_size * 8 / 1024.0) / audio_duration, 2)

            ret.update(
                OrderedDict(
                    [
                        ("audio_duration", audio_duration),
                        ("audio_sample_rate", audio_info["sample_rate"]),
                        ("audio_codec", audio_info["codec_name"]),
                        ("audio_bitrate", audio_bitrate),
                    ]
                )
            )

        return ret

    @staticmethod
    def get_stream_size(segment, stream_type="video"):
        """
        Return the video stream size in Bytes, as determined by summing up the individual
        frame sizes.

        stream_type: either "video" or "audio"
        """
        switch = "v" if stream_type == "video" else "a"
        cmd = [
            "ffprobe",
            "-loglevel",
            "error",
            "-select_streams",
            switch,
            "-show_entries",
            "packet=size",
            "-of",
            "compact=p=0:nk=1",
            segment,
        ]
        stdout, _ = run_command(cmd)
        size = 0
        for l in stdout.split("\n"):
            if l == "":
                continue
            if "|" in l:
                size += int(l.split("|")[0])
            else:
                size += int(l)
        return size

    @staticmethod
    def get_segment_info_lines(
        segment, mode=0, timestamp=0, qp_logfile=None, use_average=False
    ):
        """
        Return (list, list, duration), where each list contains the info for the
        video or audio part of the passed segment, and the duration of the segment.
        This should be used in the JSON report under "segments".

        mode: 0 or 1
        timestamp: start timestamp for the segments
        qp_logfile: Existing QP debug log file generated by ffmpeg-debug-qp
        use_average: Use average QP (saving memory/space for generated report)
        """
        segment_info = Extractor.get_segment_info(segment)
        format_info = Extractor.get_format_info(segment)
        video_segment_info_json = {}
        audio_segment_info_json = {}

        if "video_codec" in segment_info:
            video_segment_info_json = {
                "codec": segment_info["video_codec"],
                "start": timestamp,
                # use format duration to align both video and audio
                "duration": format_info["duration"],
                "resolution": str(segment_info["video_width"])
                + "x"
                + str(segment_info["video_height"]),
                "bitrate": segment_info["video_bitrate"],
                "fps": segment_info["video_frame_rate"],
            }

        if "audio_bitrate" in segment_info:
            audio_segment_info_json = {
                "codec": segment_info["audio_codec"],
                "start": timestamp,
                # use format duration to align both video and audio
                "duration": format_info["duration"],
                "bitrate": segment_info["audio_bitrate"],
            }

        if mode == 1:
            frame_info = Extractor.get_video_frame_info_ffprobe(segment)
            frame_stats_json = []
            for frame in frame_info:
                frame_stats_json.append(
                    {
                        "frameType": frame["frame_type"],
                        "frameSize": frame["size"],
                    }
                )
            video_segment_info_json["frames"] = frame_stats_json

        if mode in [2, 3]:
            frame_stats = Extractor.get_video_frame_info_ffmpeg_debug_qp(
                segment, qp_logfile, use_average
            )
            video_segment_info_json["frames"] = frame_stats

        return (
            video_segment_info_json,
            audio_segment_info_json,
            format_info["duration"],
        )


def main(_):
    """
    Extract needed report for P.1203 using segment files as input
    """
    sys.path.append(os.path.dirname(__file__))

    # argument parsing
    parser = argparse.ArgumentParser(
        description="Extract values of a video for building the JSON report file for P.1203 standalone",
        epilog="2018",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "-m",
        "--mode",
        default=0,
        type=int,
        choices=[0, 1, 2, 3],
        help="build report for this specified mode",
    )
    parser.add_argument(
        "-q",
        "--qp-logfile",
        type=str,
        help="existing logfile generated by ffmpeg_debug_qp",
    )
    parser.add_argument(
        "-a",
        "--use-average",
        action="store_true",
        help="use average QP (saving memory/space)",
    )
    parser.add_argument("input", type=str, help="Input video file(s)", nargs="*")

    argsdict = vars(parser.parse_args())

    # sequential list of input files
    segment_files = argsdict["input"]
    if not segment_files:
        print_stderr("Need at least one input file")
        sys.exit(1)

    report = Extractor(
        segment_files, argsdict["mode"], argsdict["qp_logfile"], argsdict["use_average"]
    ).extract()

    print(json.dumps(report, sort_keys=True, indent=4))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
