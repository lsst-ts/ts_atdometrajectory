.. py:currentmodule:: lsst.ts.ATDomeTrajectory

.. _lsst.ts.ATDomeTrajectory.revision_history:

####################################
ts_ATDomeTrajectory Revision History
####################################

v1.1.0
======
Update for SAL 4.

Other changes:

* Modernize the code.
* Fix a race condition in a unit test.

Requirements:

* ts_salobj 5
* ts_idl 0.4
* IDL files for ATDome, ATDomeTrajectory and ATMCS
* ts_xml 4.1
* ts_ATDome 0.8

v1.0.0
======
Update for ATDome no longer having a SAL index.

Requirements:

* ts_salobj 4.3
* ts_idl
* IDL files for ATDome, ATDomeTrajectory and ATMCS
* ts_xml 4.1
* ts_ATDome 0.7

v0.9.0
======
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
======
Add a dependency on ts_config_attcs to the ups table file.

v0.8.0
======
Use OpenSplice dds instead of SALPY libraries.

Requirements:

* ts_salobj 4.3
* ts_idl
* The following IDL files:

  * ATDomeTrajectory
  * ATDome
  * ATMCS

v0.7.0
======
Make `ATDomeTrajectory.configure` async for ts_salobj 3.12.

Requirements:

ts_xml 3.9
ts_sal 3.9
ts_salobj 3.12

v0.6.0
======
Standardize configuration of `ATDomeTrajectory` by making it a subclass of `salobj.ConfigurableCsc`.

Requirements:

* ts_xml v3.9
* ts_sal v3.8.41 or later, preferably v3.9
* ts_salobj v3.11

v0.5.0
======
Update for ts_ATDome v0.4.0.

Requirements:

* ATDome v0.4.0
* ts_sal v3.8.41
* ts_salobj v3.9

