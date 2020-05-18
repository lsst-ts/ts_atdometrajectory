.. py:currentmodule:: lsst.ts.ATDomeTrajectory

.. _lsst.ts.ATDomeTrajectory:

########################
lsst.ts.ATDomeTrajectory
########################

ts_ATDomeTrajectory contains the `ATDomeTrajectory` CSC and support code,
including a simple `FakeATDome` CSC for unit testing.

.. _lsst.ts.ATDomeTrajectory-using:

Using lsst.ts.ATDomeTrajectory
==============================

You can setup and build this package using eups and sconsUtils.
After setting up the package you can build it and run unit tests by typing ``scons``.
Building it constructs a version.py file and runs unit tests.

To run the `ATDomeTrajectory` CSC type ``runATDomeTrajectory.py``

.. _lsst.ts.ATDomeTrajectory-contributing:

Contributing
============

``lsst.ts.ATDomeTrajectory`` is developed at https://github.com/lsst-ts/ts_ATDomeTrajectory.
You can find Jira issues for this module using `labels=ts_ATDomeTrajectory <https://jira.lsstcorp.org/issues/?jql=project%20%3D%20DM%20AND%20labels%20%20%3D%20ts_ATDomeTrajectory>`_.

.. If there are topics related to developing this module (rather than using it), link to this from a toctree placed here.

.. .. toctree::
..    :maxdepth: 1

.. _lsst.ts.ATDomeTrajectory-pyapi:

Python API reference
====================

.. automodapi:: lsst.ts.ATDomeTrajectory
   :no-main-docstr:
   :no-inheritance-diagram:
.. automodapi:: lsst.ts.ATDomeTrajectory.algorithms
   :no-main-docstr:
   :no-inheritance-diagram:

Version History
===============

.. toctree::
    version_history
    :maxdepth: 1
