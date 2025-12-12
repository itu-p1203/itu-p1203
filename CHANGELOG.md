## [1.11.0] - 2025-12-12

### 🚀 Features

- Use video-parser instead of ffmpeg-debug-qp if available

### ⚙️ Miscellaneous Tasks

- Remove gitchangelog files, move to git-cliff
- Migrate to uv, update README

### ⚙️ Other

- Bump version to 1.11.0
## [1.10.0] - 2024-09-20

### ⚙️ Other

- Update dependencies and python requirements
- Bump version to 1.10.0.
## [1.9.6] - 2023-10-31

### 🐛 Bug Fixes

- Fix mos_from_r function

This better handles values exceeding the allowable input range [0, 100]

### ⚙️ Other

- Explain direct installation
- Bump version to 1.9.6.
## [1.9.5] - 2023-07-01

### ⚙️ Other

- Add fix for incorrect FPS values increasing computation time
- Bump version to 1.9.5.
## [1.9.4] - 2023-04-26

### ⚙️ Other

- Update extractor.py
- Bump version to 1.9.4.
## [1.9.3] - 2023-02-28

### ⚙️ Other

- Add fast-mode parameter
- Add test fixture
- Support .ts files, fixes #33
- Bump version to 1.9.3.
## [1.9.2] - 2023-02-23

### ⚙️ Other

- Allow overriding displaySize per segment for fast mode
- Bump version to 1.9.2.
## [1.9.1] - 2023-01-10

### 🐛 Bug Fixes

- Fix author string

### ⚙️ Other

- Bump version to 1.9.1.
## [1.9.0] - 2023-01-10

### 🐛 Bug Fixes

- Fix imports
- Fix includes and remove manifest.in

### ⚙️ Other

- Improve docstrings
- Change .warn to .warning (deprecated)
- Fixed small typo in README.md
- Update __main__.py
- Bump requirement to python 3.8
- Add setup.cfg
- Export requirements on release
- Remove executable flag on some files
- Format with black and isort
- Add blame ignore file
- Add minor type annotation
- Update packages
- Bump version to 1.9.0.
## [1.8.3] - 2022-06-24

### ⚙️ Other

- Add mode to specify displaySize per segment
- Bump version to 1.8.3.
## [1.8.2] - 2022-06-24

### ⚙️ Other

- Rename logger
- Implement an internal fast mode for per-segment computation
- Bump version to 1.8.2.
## [1.8.1] - 2022-02-28

### ⚙️ Other

- Update Python dependency versions
- Bump version to 1.8.1.
## [1.8.0] - 2021-07-26

### ⚙️ Other

- Add example for running extractor for mode 3
- Improve extractor function

uses code from parse_qp_output.py in ffmpeg-debug-qp to improve resilience
- Implement P.1203.3 Amendment 1 Appendix 2
- Update readme
- Bump version to 1.8.0.
## [1.7.2] - 2021-05-04

### ⚙️ Other

- Speed improvements

dont know why but under linux it just works with a separate command for the plot

speedup changes, precache representation names, and further use only first frame in a measurement window for calculation of audio scores

some speedup in the chunk part

update unittests

minor cleanup
- Further speedup for chunk_hash
- Remove unneded dependencies
- Cleanup profile graph
- Add further profiling for long sequences
- Bump version to 1.7.2.
## [1.7.1] - 2021-04-30

### 🐛 Bug Fixes

- Fix usage of lru_cache() method
- Fix profiling script

### ⚙️ Other

- Enable auto-push on release
- Remove old changes file
- Add console script to pyproject.toml
- Error handling improvements
- Solved issue #26
- Simplify release script
- Update packages
- Update python requirement
- Bump version to 1.7.1.
## [1.7.0] - 2020-09-22

### ⚙️ Other

- Remove static functions and access to static constants
- Add extraction of all parameters
- Add poetry env
- Freeze numpy/scipy/pandas versions
- Update release script
- Bump version to 1.7.0.
## [1.6.2] - 2020-04-27

### 🐛 Bug Fixes

- Fix python multiprocessing under macOS, fixes #16

### ⚙️ Other

- Add a test for Pq model part
- Extract methods in pq part, thus such methods can be overloaded later
- Version bump to 1.6.2
## [1.6.1] - 2020-04-24

### ⚙️ Other

- Add amendment 1 for p.1203.3
- Version bump to 1.6.1
## [1.6.0] - 2020-04-24

### ⚙️ Other

- Add vscode to gitignore
- Add linearization from Eq. 30 of P.1203.3
- Version bump to 1.6.0
## [1.5.2] - 2020-04-10

### 🐛 Bug Fixes

- Fix unit test precision

### ⚙️ Other

- Version bump to 1.5.2
## [1.5.1] - 2020-04-10

### ⚙️ Other

- Add fuzzy test comparator
- Allow overriding Pq coefficients from class constructor
- Version bump to 1.5.1
## [1.5.0] - 2020-03-16

### ⚙️ Other

- Python 3.7 and 3.8
- Add missing handheld/mobile conversion
- Remove python 3.8 compatibility, see #16
- Version bump to 1.5.0
## [1.4.1] - 2020-01-27

### ⚙️ Other

- Do not prune stalling events if there is no audio
- Version bump to 1.4.1
## [1.4.0] - 2019-11-28

### 🐛 Bug Fixes

- Fix codec name in examples, add new one-line example
- Fix package imports, avoid relative imports

### ⚡ Performance

- Performance improvements, do not use hash function

### ⚙️ Other

- Update test script to check for exact values
- Add profiling test description
- Version bump to 1.4.0
## [1.3.3] - 2019-11-22

### ⚙️ Other

- Handle empty stalling values
- Version bump to 1.3.3
## [1.3.2] - 2019-09-12

### 🐛 Bug Fixes

- Fix rounding errors in measurement window, fixes #15

This applies a small check at the end of the measurement window.
If it is .9999, then it will be rounded up instead of down.

### ⚙️ Other

- Version bump to 1.3.2
## [1.3.1] - 2019-07-18

### ⚙️ Other

- Added missing comma
- Merge pull request #14 from jeromepasvantis/bugfix-extractor-cmdarg

Bugfix in Extractor: Missing Comma in Cmdline args
- Version bump to 1.3.1
## [1.3.0] - 2019-07-08

### ⚙️ Other

- Allow reading from STDIN

Make it possible to supply "-" as input filename, which will make the program
read from STDIN instead of an actual file.
- Version bump to 1.3.0
## [1.2.8] - 2019-04-23

### ⚙️ Other

- Update notice about error in P.1203.3 standard
- Update helper script to use existing qp values, if calculated
- Add support for .gz files for QP values
- Add warning if multiple segments are used with one qp logfile
- Allow calculating average QP as shortcut in extractor
- Add Windows compatibility

This adds compatibility for Windows by using portable file size commands
as well as list-based subprocess calls.
This requires Python 3.5 or higher.
Windows-specific instructions have been removed due to size and maintenance
burden. Current versions of Python are recommended instead.
- Version bump to 1.2.8
## [1.2.7] - 2019-01-28

### ⚙️ Other

- Round during segment continuity check

additionally print info on what type of segment is being checked
- Version bump to 1.2.7
## [1.2.6] - 2019-01-18

### 🐛 Bug Fixes

- Fix position of warning message

### ⚙️ Other

- Exclude zero-duration stalling events
- Version bump to 1.2.6
## [1.2.5] - 2019-01-18

### ⚙️ Other

- Restrict position of stalling events to inside media range
- Version bump to 1.2.5
## [1.2.4] - 2018-09-10

### ⚙️ Other

- Change how the overall result of P1203Standalone is handled, this increases extensibiliy of the Pq model
- Version bump to 1.2.4
## [1.2.3] - 2018-07-16

### 🐛 Bug Fixes

- Fix debug print function

### ⚙️ Other

- Missing dict specifier in readme input example
- Typo in resolution for input
- Missing commas on Readme json
- Merge pull request #6 from pedosb/master

Corrects invalid JSON in readme examples
- Add missing return statement, fixes #7
- Version bump to 1.2.3
## [1.2.2] - 2018-06-21

### 🐛 Bug Fixes

- Fix citation key

### ⚙️ Other

- Change affiliation
- Clarify error in standard
- Clarify acknowledgement terms
- Ask user to accept terms before running
- Version bump to 1.2.2
## [1.2.1] - 2018-06-20

### ⚙️ Other

- Add disclaimer in README
- Minor readme improvements
- Minor bug in detecting stalling
- Version bump to 1.2.1
## [1.2.0] - 2018-06-20

### 🐛 Bug Fixes

- Fix coefficient for exponential function
- Fix detection of initial buffering for RF model

### ⚙️ Other

- Version bump to 1.2.0
## [1.1.15] - 2018-06-20

### 🐛 Bug Fixes

- Fix setup script

### ⚙️ Other

- Warn if the first stalling event is not starting at 0
- Version bump to 1.1.15
## [1.1.14] - 2018-05-25

### ⚙️ Other

- Add auto release script
- Version bump to 1.1.14
## [1.1.13] - 2018-05-25

### 🐛 Bug Fixes

- Fix handling of single digit qp values

### ⚙️ Other

- Merge pull request #4 from derbroti/master

fix handling of single digit qp values
- Bump version
## [1.1.12] - 2018-05-23

### ⚙️ Other

- Add a comment of media in json description
- Do not import module for installation, fixes #2
- Bump version
## [1.1.11] - 2018-05-03

### 🐛 Bug Fixes

- Fix error in method documentation
- Fix handling of setup version

### ⚙️ Other

- Initial commit
- Remove debugging print
- Bump version
- Update references
- Minor README improvements
- Allow quiet running
- Bump version
