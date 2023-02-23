# Changelog


## v1.9.2 (2023-02-23)

* Allow overriding displaySize per segment for fast mode.


## v1.9.1 (2023-01-10)

* Fix author string.


## v1.9.0 (2023-01-10)

* Update packages.

* Add minor type annotation.

* Add blame ignore file.

* Format with black and isort.

* Remove executable flag on some files.

* Fix includes and remove manifest.in.

* Export requirements on release.

* Add setup.cfg.

* Fix imports.

* Bump requirement to python 3.8.

* Update __main__.py.

* Fixed small typo in README.md.

* Change .warn to .warning (deprecated)

* Improve docstrings.


## v1.8.3 (2022-06-24)

* Add mode to specify displaySize per segment.


## v1.8.2 (2022-06-24)

* Implement an internal fast mode for per-segment computation.

* Rename logger.


## v1.8.1 (2022-02-28)

* Update Python dependency versions.


## v1.8.0 (2021-07-26)

* Update readme.

* Implement P.1203.3 Amendment 1 Appendix 2.

* Improve extractor function.

  uses code from parse_qp_output.py in ffmpeg-debug-qp to improve resilience

* Add example for running extractor for mode 3.


## v1.7.2 (2021-05-04)

* Add further profiling for long sequences.

* Cleanup profile graph.

* Remove unneded dependencies.

* Further speedup for chunk_hash.

* Speed improvements.

  dont know why but under linux it just works with a separate command for the plot

  speedup changes, precache representation names, and further use only first frame in a measurement window for calculation of audio scores

  some speedup in the chunk part

  update unittests

  minor cleanup


## v1.7.1 (2021-04-30)

* Update python requirement.

* Update packages.

* Fix profiling script.

* Simplify release script.

* Fix usage of lru_cache() method.

* Solved issue #26.

* Error handling improvements.

* Add console script to pyproject.toml.

* Remove old changes file.

* Enable auto-push on release.


## v1.7.0 (2020-09-22)

* Update release script.

* Freeze numpy/scipy/pandas versions.

* Add poetry env.

* Add extraction of all parameters.

* Remove static functions and access to static constants.


## v1.6.2 (2020-04-27)

* Version bump to 1.6.2.

* Extract methods in pq part, thus such methods can be overloaded later.

* Add a test for Pq model part.

* Fix python multiprocessing under macOS, fixes #16.


## v1.6.1 (2020-04-24)

* Version bump to 1.6.1.

* Add amendment 1 for p.1203.3.


## v1.6.0 (2020-04-24)

* Version bump to 1.6.0.

* Add linearization from Eq. 30 of P.1203.3.

* Add vscode to gitignore.


## v1.5.2 (2020-04-10)

* Version bump to 1.5.2.

* Fix unit test precision.


## v1.5.1 (2020-04-10)

* Version bump to 1.5.1.

* Allow overriding Pq coefficients from class constructor.

* Add fuzzy test comparator.


## v1.5.0 (2020-03-16)

* Version bump to 1.5.0.

* Remove python 3.8 compatibility, see #16.

* Add missing handheld/mobile conversion.

* Python 3.7 and 3.8.


## v1.4.1 (2020-01-27)

* Version bump to 1.4.1.

* Do not prune stalling events if there is no audio.


## v1.4.0 (2019-11-28)

* Version bump to 1.4.0.

* Add profiling test description.

* Update test script to check for exact values.

* Performance improvements, do not use hash function.

* Fix package imports, avoid relative imports.

* Fix codec name in examples, add new one-line example.


## v1.3.3 (2019-11-22)

* Version bump to 1.3.3.

* Handle empty stalling values.


## v1.3.2 (2019-09-12)

* Version bump to 1.3.2.

* Fix rounding errors in measurement window, fixes #15.

  This applies a small check at the end of the measurement window.
  If it is .9999, then it will be rounded up instead of down.


## v1.3.1 (2019-07-18)

* Version bump to 1.3.1.

* Merge pull request #14 from jeromepasvantis/bugfix-extractor-cmdarg.

  Bugfix in Extractor: Missing Comma in Cmdline args

* Added missing comma.


## v1.3.0 (2019-07-08)

* Version bump to 1.3.0.

* Allow reading from STDIN.

  Make it possible to supply "-" as input filename, which will make the program
  read from STDIN instead of an actual file.


## v1.2.8 (2019-04-23)

* Version bump to 1.2.8.

* Add Windows compatibility.

  This adds compatibility for Windows by using portable file size commands
  as well as list-based subprocess calls.
  This requires Python 3.5 or higher.
  Windows-specific instructions have been removed due to size and maintenance
  burden. Current versions of Python are recommended instead.

* Allow calculating average QP as shortcut in extractor.

* Add warning if multiple segments are used with one qp logfile.

* Add support for .gz files for QP values.

* Update helper script to use existing qp values, if calculated.

* Update notice about error in P.1203.3 standard.


## v1.2.7 (2019-01-28)

* Version bump to 1.2.7.

* Round during segment continuity check.

  additionally print info on what type of segment is being checked


## v1.2.6 (2019-01-18)

* Version bump to 1.2.6.

* Exclude zero-duration stalling events.

* Fix position of warning message.


## v1.2.5 (2019-01-18)

* Version bump to 1.2.5.

* Restrict position of stalling events to inside media range.


## v1.2.4 (2018-09-10)

* Version bump to 1.2.4.

* Change how the overall result of P1203Standalone is handled, this increases extensibiliy of the Pq model.


## v1.2.3 (2018-07-16)

* Version bump to 1.2.3.

* Add missing return statement, fixes #7.

* Fix debug print function.

* Merge pull request #6 from pedosb/master.

  Corrects invalid JSON in readme examples

* Missing commas on Readme json.

* Typo in resolution for input.

* Missing dict specifier in readme input example.


## v1.2.2 (2018-06-21)

* Version bump to 1.2.2.

* Ask user to accept terms before running.

* Clarify acknowledgement terms.

* Clarify error in standard.

* Change affiliation.

* Fix citation key.


## v1.2.1 (2018-06-20)

* Version bump to 1.2.1.

* Minor bug in detecting stalling.

* Minor readme improvements.

* Add disclaimer in README.


## v1.2.0 (2018-06-20)

* Version bump to 1.2.0.

* Fix detection of initial buffering for RF model.

* Fix coefficient for exponential function.


## v1.1.15 (2018-06-20)

* Version bump to 1.1.15.

* Warn if the first stalling event is not starting at 0.

* Fix setup script.


## v1.1.14 (2018-05-25)

* Version bump to 1.1.14.

* Add auto release script.


## v1.1.13 (2018-05-25)

* Bump version.

* Merge pull request #4 from derbroti/master.

  fix handling of single digit qp values

* Fix handling of single digit qp values.


## v1.1.12 (2018-05-23)

* Bump version.

* Do not import module for installation, fixes #2.

* Add a comment of media in json description.


## v1.1.11 (2018-05-03)

* Fix handling of setup version.

* Bump version.

* Allow quiet running.

* Minor README improvements.

* Update references.

* Bump version.

* Remove debugging print.

* Fix error in method documentation.

* Initial commit.


