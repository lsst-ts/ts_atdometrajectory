.. py:currentmodule:: lsst.ts.atdometrajectory

.. _lsst.ts.atdometrajectory.version_history:

###############
Version History
###############

v1.10.1
-------

* `CONFIG_SCHEMA`: update to v4.
  Rename x_vignetted_min to x_vignetted_partial and x_vignetted_max to x_vignetted_full.
  This enhances clarity and matches MTDomeTrajectory, where "min" and "max" did not work for all vignetting parameters.
* `ATDomeTrajectory`: fix a misfeature in the compute_vignetted_by_azimuth method: it was checking the ATMCS mount_AzEl_Encoders telemetry unnecessarily.
* Unit tests: remove ``if __name__ == "__main__"`` blocks, so tests must be run with pytest.
* Use ts_pre_commit_config.
* Remove scons support.

Requirements:

* ts_salobj 7.2
* ts_idl 2
* ts_utils 1
* IDL files for ATDome, ATDomeTrajectory and ATMCS built from ts_xml 16

v1.10.0
-------

* `ATDomeTrajectory`: publish the ``telescopeVignetted`` event.
  This requires ts_xml 16 and adds items to the config schema version, bumping it to version v3.
* ``Jenkinsfile`` CI: do not run as root.
* pre-commit: update black to 23.1.0 and pre-commit-hooks to v4.4.0 and add isort.

Requirements:

* ts_salobj 7.2
* ts_idl 2
* ts_utils 1
* IDL files for ATDome, ATDomeTrajectory and ATMCS built from ts_xml 16

v1.9.0
------

* `MockDome`: use allow_missing_callbacks to simplify the code.
  This requires ts_salobj 7.2.
* ``Jenkinsfile`` CI: change HOME to WHOME (except in the cleanup section).
* Rename package from ts_ATDomeTrajectory to ts_atdometrajectory.

Requirements:

* ts_salobj 7.2
* ts_idl 2
* ts_utils 1
* IDL files for ATDome, ATDomeTrajectory and ATMCS built from ts_xml 11

v1.8.0
------

* Rename command-line scripts to remove ".py" suffix.
* Add ``Jenkinsfile`` for continuous integration.
* Build with pyproject.toml.

Requirements:

* ts_salobj 7
* ts_idl 2
* ts_utils 1
* IDL files for ATDome, ATDomeTrajectory and ATMCS built from ts_xml 11

v1.7.0
------

* Update for ts_salobj v7, which is required.
  This also requires ts_xml 11.
* Use ts_utils and pytest-black.

Requirements:

* ts_salobj 7
* ts_idl 2
* ts_utils 1
* IDL files for ATDome, ATDomeTrajectory and ATMCS built from ts_xml 11

v1.6.0
------

* Support the ``setFollowingMode`` command.
  This requires ts_xml 9.
* `ATDomeTrajectory`: wait for the dome remote to start at startup,
  to avoid the CSC trying to command the dome before the remote is ready.
* Rename `MockATDome` to `MockDome` for uniformity with ts_MTDomeTrajectory.
* ``test_csc.py``: eliminate several race conditions in ``make_csc``
   by waiting for the extra remotes and controllers to start.
* Change the CSC configuration schema to allow configuring all algorithms at once.
  This supports a planned change to how configuration files are read.
* Eliminate use of the abandoned ``asynctest`` package; use `unittest.IsolatedAsyncioTestCase` instead.
* Delete obsolete ``.travis.yml`` file.
* Format the code with black 20.8b1.
* Use pre-commit instead of a custom pre-commit hook; see the README.md for instructions.
* Modernize conda/meta.yaml.

Requirements:

* ts_salobj 6.3
* ts_idl 2
* IDL files for ATDome, ATDomeTrajectory and ATMCS built from ts_xml 9

v1.5.1
------

* Fix handling of a missing ``version.py`` file.
* Modernize ``Jenkinsfile.conda``.

Requirements:

* ts_salobj 6.3
* ts_idl 2
* IDL files for ATDome, ATDomeTrajectory and ATMCS built from ts_xml 4.1


v1.5.0
------

* Store the CSC configuration schema in code.
  This requires ts_salobj 6.3.
* `MockDome`: set the ``version`` class attribute.

Requirements:

* ts_salobj 6.3
* ts_idl 2
* IDL files for ATDome, ATDomeTrajectory and ATMCS built from ts_xml 4.1

v1.4.7
------

* Modernize doc/conf.py for documenteer 0.6.

Requirements:

* ts_salobj 5.11 or 6
* ts_idl 1.0
* IDL files for ATDome, ATDomeTrajectory and ATMCS built from ts_xml 4.1

v1.4.6
------

* `ATDomeTrajectory`: add ``version`` class attribute, which is used to set the ``cscVersion`` field of the ``softwareVersions`` event.

Requirements:

* ts_salobj 5.11 or 6
* ts_idl 1.0
* IDL files for ATDome, ATDomeTrajectory and ATMCS built from ts_xml 4.1

v1.4.5
------

* Improve `MockATDome` shutdown.
* Improve reliability of a unit test of `MockATDome`.

Requirements:

* ts_salobj 5.11 or 6
* ts_idl 1.0
* IDL files for ATDome, ATDomeTrajectory and ATMCS built from ts_xml 4.1

v1.4.4
------

* Modernize the documentation.
* Rename ``FakeATDome`` to `MockATDome`.

Requirements:

* ts_salobj 5.11 or 6
* ts_idl 1.0
* IDL files for ATDome, ATDomeTrajectory and ATMCS built from ts_xml 4.1

v1.4.3
------

* Pin version of black in meta.yaml.

Requirements:

* ts_salobj 5.11 or 6
* ts_idl 1.0
* IDL files for ATDome, ATDomeTrajectory and ATMCS built from ts_xml 4.1

v1.4.2
------

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

* Added missing ts_simactuators to the list of dependencies.

Requirements:

* ts_salobj 5.11
* ts_idl 1.0
* IDL files for ATDome, ATDomeTrajectory and ATMCS built from ts_xml 4.1

v1.4.0
------

* Add next target support to the algorithms (but not the CSC, yet).
* Modernize the code and make it more like MTDomeTrajectory.

Requirements:

* ts_salobj 5.11
* ts_idl 1.0
* IDL files for ATDome, ATDomeTrajectory and ATMCS built from ts_xml 4.1

v1.3.4
------

* Add black to conda test dependencies

Requirements:

* ts_salobj 5.11
* ts_idl 1.0
* IDL files for ATDome, ATDomeTrajectory and ATMCS built from ts_xml 4.1

v1.3.3
------

* Add ``tests/test_black.py`` to verify that files are formatted with black.
  This requires ts_salobj 5.11 or later.
* Modernized the test of the bin script, which also made it compatible with salobj 5.12.
* Fix f strings with no {}.
* Update ``.travis.yml`` to remove ``sudo: false`` to github travis checks pass once again.

v1.3.2
------

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
