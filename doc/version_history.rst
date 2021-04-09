.. py:currentmodule:: lsst.ts.ATDomeTrajectory

.. _lsst.ts.ATDomeTrajectory.version_history:

###############
Version History
###############

v1.7.0
------

Changes:

* Change the CSC configuration schema to allow configuring all algorithms at once.
  This supports a planned change to how configuration files are read.

Requirements:

* ts_salobj 6.3
* ts_idl 2
* IDL files for ATDome, ATDomeTrajectory and ATMCS built from ts_xml 8.1

v1.6.0
------

Changes:

* Support the ``setFollowingMode`` command.
  This requires ts_xml 8.1.
* `ATDomeTrajectory`: wait for the dome remote to start at startup,
  to avoid the CSC trying to command the dome before the remote is ready.
* Rename `MockATDome` to `MockDome` for uniformity with ts_MTDomeTrajectory.
* ``test_csc.py``: eliminate several race conditions in ``make_csc``
   by waiting for the extra remotes and controllers to start.
* Eliminate use of the abandoned ``asynctest`` package; use `unittest.IsolatedAsyncioTestCase` instead.
* Delete obsolete ``.travis.yml`` file.
* Format the code with black 20.8b1.
* Use pre-commit instead of a custom pre-commit hook; see the README.md for instructions.
* Modernize conda/meta.yaml.

Requirements:

* ts_salobj 6.3
* ts_idl 2
* IDL files for ATDome, ATDomeTrajectory and ATMCS built from ts_xml 8.1

v1.5.1
------

Changes:

* Fix handling of a missing ``version.py`` file.
* Modernize ``Jenkinsfile.conda``.

Requirements:

* ts_salobj 6.3
* ts_idl 2
* IDL files for ATDome, ATDomeTrajectory and ATMCS built from ts_xml 4.1


v1.5.0
------

Changes:

* Store the CSC configuration schema in code.
  This requires ts_salobj 6.3.
* `MockDome`: set the ``version`` class attribute.

Requirements:

* ts_salobj 6.3
* ts_idl 2
* IDL files for ATDome, ATDomeTrajectory and ATMCS built from ts_xml 4.1

v1.4.7
------

Changes:

* Modernize doc/conf.py for documenteer 0.6.

Requirements:

* ts_salobj 5.11 or 6
* ts_idl 1.0
* IDL files for ATDome, ATDomeTrajectory and ATMCS built from ts_xml 4.1

v1.4.6
------

Changes:

* `ATDomeTrajectory`: add ``version`` class attribute, which is used to set the ``cscVersion`` field of the ``softwareVersions`` event.

Requirements:

* ts_salobj 5.11 or 6
* ts_idl 1.0
* IDL files for ATDome, ATDomeTrajectory and ATMCS built from ts_xml 4.1

v1.4.5
------

Changes:

* Improve `MockATDome` shutdown.
* Improve reliability of a unit test of `MockATDome`.

Requirements:

* ts_salobj 5.11 or 6
* ts_idl 1.0
* IDL files for ATDome, ATDomeTrajectory and ATMCS built from ts_xml 4.1

v1.4.4
------

Changes:

* Modernize the documentation.
* Rename ``FakeATDome`` to `MockATDome`.

Requirements:

* ts_salobj 5.11 or 6
* ts_idl 1.0
* IDL files for ATDome, ATDomeTrajectory and ATMCS built from ts_xml 4.1

v1.4.3
------

Changes:

* Pin version of black in meta.yaml.

Requirements:

* ts_salobj 5.11 or 6
* ts_idl 1.0
* IDL files for ATDome, ATDomeTrajectory and ATMCS built from ts_xml 4.1

v1.4.2
------

Changes:

* Remove the ``simulation_mode`` constructor argument from `ATDomeTrajectory`
  and updated associated documentation.
  The CSC does not support simulation.
* Improved the ``black`` pre-commit hook.

Requirements:

* ts_salobj 5.11 or 6
* ts_idl 1.0
* IDL files for ATDome, ATDomeTrajectory and ATMCS built from ts_xml 4.1

v1.4.1
------

Changes:

* Added missing ts_simactuators to the list of dependencies.

Requirements:

* ts_salobj 5.11
* ts_idl 1.0
* IDL files for ATDome, ATDomeTrajectory and ATMCS built from ts_xml 4.1

v1.4.0
------

Changes:

* Add next target support to the algorithms (but not the CSC, yet).
* Modernize the code and make it more like MTDomeTrajectory.

Requirements:

* ts_salobj 5.11
* ts_idl 1.0
* IDL files for ATDome, ATDomeTrajectory and ATMCS built from ts_xml 4.1

v1.3.4
------

Changes:

* Add black to conda test dependencies

Requirements:

* ts_salobj 5.11
* ts_idl 1.0
* IDL files for ATDome, ATDomeTrajectory and ATMCS built from ts_xml 4.1

v1.3.3
------

Changes:

* Add ``tests/test_black.py`` to verify that files are formatted with black.
  This requires ts_salobj 5.11 or later.
* Modernized the test of the bin script, which also made it compatible with salobj 5.12.
* Fix f strings with no {}.
* Update ``.travis.yml`` to remove ``sudo: false`` to github travis checks pass once again.

v1.3.2
------

Changes:

* Fix the ``Contributing`` entry in ``index.rst``.

Requirements:

* ts_salobj 5.11
* ts_idl 1.0
* IDL files for ATDome, ATDomeTrajectory and ATMCS built from ts_xml 4.1

v1.3.1
------

Add conda build support.

Requirements:

* ts_salobj 5.4
* ts_idl 1.0
* IDL files for ATDome, ATDomeTrajectory and ATMCS built from ts_xml 4.1


v1.3.0
------

* Update CSC unit tests to use `lsst.ts.salobj.BaseCscTestCase`.
  Thus we now require ts_salobj 5.4.
* Code formatted by ``black``, with a pre-commit hook to enforce this. See the README file for configuration instructions.

Requirements:

* ts_salobj 5.4
* ts_idl 1.0
* IDL files for ATDome, ATDomeTrajectory and ATMCS built from ts_xml 4.1


v1.2.0
------

Update for ts_salobj 5.2: rename initial_simulation_mode to simulation_mode.

Requirements:

* ts_salobj 5.2
* ts_idl 0.4
* IDL files for ATDome, ATDomeTrajectory and ATMCS built from ts_xml 4.1

v1.1.0
------
Update for SAL 4.

Other changes:

* Modernize the code.
* Fix a race condition in a unit test.

Requirements:

* ts_salobj 5
* ts_idl 0.4
* IDL files for ATDome, ATDomeTrajectory and ATMCS built from ts_xml 4.1

v1.0.0
------
Update for ATDome no longer having a SAL index.

Requirements:

* ts_salobj 4.3
* ts_idl
* IDL files for ATDome, ATDomeTrajectory and ATMCS built from ts_xml 4.1

v0.9.0
------
In `algorithms.SimpleAlgorithm` scale daz by cos(el) so the dome is less likely to move unnecessarily.

Other changes:

* Add this revision history.
* Make the package usable from source, without running scons.
  Thus move bin.src/run_atdometrajectory.py to bin/run_atdometrajectory.py and make the presence of version.py optional.

Requirements:

* ts_salobj 4.3
* ts_idl
* IDL files for ATDome, ATDomeTrajectory and ATMCS

v0.8.1
------
Add a dependency on ts_config_attcs to the ups table file.

v0.8.0
------
Use OpenSplice dds instead of SALPY libraries.

Requirements:

* ts_salobj 4.3
* ts_idl
* The following IDL files:

  * ATDomeTrajectory
  * ATDome
  * ATMCS

v0.7.0
------
Make `ATDomeTrajectory.configure` async for ts_salobj 3.12.

Requirements:

ts_xml 3.9
ts_sal 3.9
ts_salobj 3.12

v0.6.0
------
Standardize configuration of `ATDomeTrajectory` by making it a subclass of `salobj.ConfigurableCsc`.

Requirements:

* ts_xml v3.9
* ts_sal v3.8.41 or later, preferably v3.9
* ts_salobj v3.11

v0.5.0
------
Update for ts_ATDome v0.4.0.

Requirements:

* ATDome v0.4.0
* ts_sal v3.8.41
* ts_salobj v3.9
