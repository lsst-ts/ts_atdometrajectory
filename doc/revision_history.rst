.. py:currentmodule:: lsst.ts.ATDomeTrajectory

.. _lsst.ts.ATDomeTrajectory.revision_history:

####################################
ts_ATDomeTrajectory Revision History
####################################

v0.8.2
======
In `algorithms.SimpleAlgorithm` scale daz by cos(el) so the dome is less likely to move unnecessarily.

Add this revision history.

Make the package usable from source, without running scons. Thus move bin.src/run_atdometrajectory.py to bin/run_atdometrajectory.py and make the presence of version.py optional.

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

