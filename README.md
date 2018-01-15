# ITU-T Rec. P.1203 Standalone Implementation

This evaluation software implements the following standards:

- ITU-T Rec. P.1203: Parametric bitstream-based quality assessment of progressive download and adaptive audiovisual streaming services over reliable transport
- ITU-T Rec. P.1203.1: Parametric bitstream-based quality assessment of progressive download and adaptive audiovisual streaming services over reliable transport - Video quality estimation module
- ITU-T Rec. P.1203.2: Parametric bitstream-based quality assessment of progressive download and adaptive audiovisual streaming services over reliable transport - Audio quality estimation module
- ITU-T Rec. P.1203.3: Parametric bitstream-based quality assessment of progressive download and adaptive audiovisual streaming services over reliable transport - Quality integration module

## General Description

The software takes the following input:

* One or more audiovisual files (segments), or
* A JSON-formatted input specification

Based on the input, it calculates per-second audio and video quality scores and an overall audiovisual integrated quality score according to the P.1203 standards. The following codecs are supported:

* Audio: AAC-LC, HE-AAC, MP2, AC3
* Video: H.264

When specifying the input, the software automatically decides which "mode" will be used for evaluation:

* Mode 0 (metadata only); bitrate, framerate, and resolution
* Mode 1 (frame header data only): all of mode 0 plus frame types and sizes
* Mode 2 (bitstream data, 2%): all of mode 1 plus 2% of the QP values of all frames
* Mode 3 (bitstream data, 2%): all of mode 1 plus QP values of all frames

The higher the mode, the higher the accuracy of the prediction.

## Requirements

* Python 3, ffprobe/ffmpeg and pip3
* For running locally without pip: `pip3 install numpy scipy pandas`
* For development (for code analysis and improving): `pip3 install pylint`

For installation under Windows please follow the guide in [windows/README.md](windows/README.md).

## Installation via `pip3`

From this directory, run:

    pip3 install .

Then you will get a `p1203-standalone` executable on your system.

## CLI Usage

```
itu_p1203 [-h] [-m {0,1,2,3}] [--debug] [--only-pa] [--only-pv]
          [--print-intermediate] [--cpu-count CPU_COUNT] [--version]
          input [input ...]

P.1203 standalone reference implementation

positional arguments:
  input                 input report JSON file(s) or video file(s), format see README

optional arguments:
  -h, --help            show this help message and exit
  -m {0,1,2,3}, --mode {0,1,2,3}
                        mode to run for extraction in case video files are
                        loaded (default: 1)
  --debug               some debug output (default: False)
  --only-pa             just print Pa O.21 values (default: False)
  --only-pv             just print Pv O.22 values (default: False)
  --print-intermediate  print intermediate O.21/O.22 values (default: False)
  --cpu-count CPU_COUNT thread/CPU count (default: 8)
  --version             show program's version number and exit
```

The program will output a valid JSON report with the following structure:

```
{
  "path/to/first/input/file": {
    "O21": [
      # per-second audio quality scores (only if --print-intermediate was used)
    ],
    "O22": [
      # per-second video quality scores (only if --print-intermediate was used)
    ]
    "O23": 5.0,     # stalling quality
    "O34": [
      # per-second audiovisual quality scores
    ],
    "O35": 4.63,    # audiovisual quality score
    "O46": 4.92,    # overall quality score
    "mode": 0,      # used mode, either 0, 1, or 3
    "streamId": 42  # currently unused
  },
  "path/to/second/input/file": {
    ...
  }, ...
}
```

## Usage Examples

These examples assume direct usage from the source folder. If you installed the tool via `pip` you can just call `itu-p1203` with the needed options.

```
python3 -m itu_p1203 examples/mode0.json
```

Should output:

```json
{
 "examples/mode0.json": {
  "O23": 5.0,
  "O34": [5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0],
  "O35": 5.0,
  "O46": 4.9209299083625,
  "mode": 0,
  "streamId": 42
 }
}
```

You can run video and audio-only evaluation, too:

```bash
python3 -m itu_p1203 examples/mode1.json --only-pv
```

```json
{
 "examples/mode1.json": {
  "video": {
   "O22": [3.6388673743323765, 3.6388673743323765, 3.6388673743323765, 3.6388673743323765, 3.6388673743323765, 3.9788927218578936, 3.9788927218578936, 3.9788927218578936, 3.9788927218578936, 3.9788927218578936, 4.391663023866462, 4.391663023866462, 4.391663023866462, 4.391663023866462, 4.391663023866462, 4.404242168691321, 4.404242168691321, 4.404242168691321, 4.404242168691321],
   "mode": 1,
   "streamId": 42
  }
 }
}
```

You can run it on video files directly:

```
python3 -m itu_p1203 segment-1.mp4 segment-2.mp4 --mode 1
```

## JSON Input Format

The input JSON file (see files in `examples`) must have at least the following data:

```
{
"I13":                # video input information
    "streamId": 42,   # unique identifier for the stream
    "segments": [
      # list of video segments, see below
    ]
}
```

The following keys and data are optional:

```
"IGen": {                         # Generic input information
    "displaySize": "1920x1080"    # display resolution in pixels, given as `<width>x<height>`
    "device": "pc"                # pc or mobile, default: "pc"
    "viewingDistance":            # not used
  }
"I11": {              # Audio input information
    "streamId": 42    # unique identifier for the stream
    "segments": [
      # list of audio segments, see below
    ]
  }
"I23": {              # Stalling input information
    "streamId": 42    # unique identifier for the stream
    "stalling": [
      # pair of `[start timestamp, duration]` for each stalling event
      # where the start timestamp is measured in media time
    ]
  }
}
```

Note:

- All timestamps are in media time
- All timestamps are given as seconds (with optional fractional seconds)

As an alternative to giving segment information, the input can also be a list of O.21 (audio) and O.22 (video) quality scores, e.g. from other calculations. See `examples/existing_O21_O22.json` for an example.

### JSON Audio Input Format

For audio, `segments` contains a list of audio segments to be analyzed. Each segment is defined by the following dictionary:

```
{
  "codec": "aaclc",   # audio codec, any of [mp2, ac3, aaclc, heaac]
  "start": 0.0,       # start timestamp
  "duration": 5.0,    # duration
  "bitrate": 192.0    # bitrate in kBit/s
}
```

### JSON Video Input Format

For video, `segments` contains a list of video segments to be analyzed. Each segment is defined by the following dictionary, depending on the mode:

```
{
  "codec": "h264",       # only h264 supported in standard
  "start": 0.0,          # start timestamp in s
  "duration": 5.0,       # duration in s
  "res": "1920x1080",    # resolution as "widthxheight", e.g. "1920x1080"
  "bitrate": 5000,       # bitrate in kBit/s
  "fps": 24,             # framerate
  "frames": [
    # optional list of frames
    # when present, will enable modes 1, 2 or 3
  ]
}
```

The list of frames contains every frame in the sequence, in decoding order. The object contents depend on the mode, and the software figures out automatically which mode to calculate:

```
{
  "frameType": "I",     # I or Non-I
  "frameSize": 18102,   # in Bytes
  "qpValues": [
    # optional list of QP values in frame, one per macroblock
    # when present, will enable mode 3
  ]
}
```

## Advanced: Input Generation with `ffprobe`

If you have `ffprobe` installed, you can generate the required input file from one or more video segments by using the `itu_p1203/extractor.py` script. For example:

```bash
python3 -m itu_p1203.extractor -m 1 /path/to/segment1.mp4 /path/to/segment2.mp4 > mode1.json
```

This is what the `itu_p1203` script does in the background if you call it with a video file as argument.

For extracting Mode 3 values, you need the [`ffmpeg-debug-qp`](https://github.com/slhck/ffmpeg-debug-qp) executable installed. Note that this is experimental and may not work with all input video files, hence cannot be used to validate an existing implementation.

See `itu_p1203/extractor.py -h` for more info.

## API Usage

You can use the classes contained in this module to programmatically call the model in your test application. For example:

```python
from itu_p1203.itu_p1203 import P1203Standalone
P1203Standalone(input_json).calculate_complete()

from itu_p1203.p1203Pa import P1203Pa
P1203Pa(segments).calculate()

from itu_p1203.p1203Pq import P1203Pq
P1203Pq(audio_scores, video_scores).calculate()
```

For more, see the example usage in `itu_p1203/__main__.py`.

## Acknowledgement

If you use this software in your research, you must:

1. Include the link to this repository
2. Cite the following publication:

        @inproceedings{Raake2017,
        address = {Erfurt},
        author = {Raake, Alexander and Garcia, Marie-Neige and Robitza, Werner and List, Peter and Göring, Steve and Feiten, Bernhard},
        booktitle = {2017 Ninth International Conference on Quality of Multimedia Experience (QoMEX)},
        doi = {10.1109/QoMEX.2017.7965631},
        isbn = {978-1-5386-4024-1},
        month = {May},
        publisher = {IEEE},
        title = {{A bitstream-based, scalable video-quality model for HTTP adaptive streaming: ITU-T P.1203.1}},
        url = {http://ieeexplore.ieee.org/document/7965631/},
        year = {2017}
        }

Development of this software has been partly funded by the European Union’s Horizon 2020 research and innovation programme under the Marie Skłodowska-Curie grant agreement No 643072, Project [QoE-Net](http://www.qoenet-itn.eu/).

## License

Copyright 2017 Deutsche Telekom AG, Technische Universität Berlin, Technische Universität Ilmenau, LM Ericsson

Permission is hereby granted, free of charge, to use the software for non-commercial research purposes.

Any other use of the software, including commercial use, merging, publishing, distributing, sublicensing, and/or selling copies of the Software, is forbidden.

For a commercial license, you must contact the respective rights holders of the standards ITU-T Rec. P.1203, ITU-T Rec. P.1203.1, ITU-T Rec. P.1203.2, and ITU-T Rec. P.1203.3. See https://www.itu.int/en/ITU-T/ipr/Pages/default.aspx for more information.

NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY THIS LICENSE. THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

## Authors

Main developers:

* Steve Göring, Technische Universität Ilmenau
* Werner Robitza, Deutsche Telekom AG

Contributors:

* Marie-Neige Garcia, Technische Universität Berlin
* Alexander Raake, Technische Universität Ilmenau
* Marcel Schmalzl, Technische Universität Ilmenau
* Peter List, Deutsche Telekom AG
* Bernhard Feiten, Deutsche Telekom AG
* Ulf Wüstenhagen, Deutsche Telekom AG
* Jörgen Gustafsson, LM Ericsson
* Gunnar Heikkilä, LM Ericsson
* David Lindegren, LM Ericsson
* Junaid Shaikh, LM Ericsson