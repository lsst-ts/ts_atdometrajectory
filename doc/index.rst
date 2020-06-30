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

To run `ATDomeTrajectory` type ``runATDomeTrajectory.py``

Enable `ATDomeTrajectory` to have it command ``ATDome`` azimuth to follow the telescope.
Disable `ATDomeTrajectory` to prevent it from sending any more commands to ``ATDome``; this will not halt existing dome motion.

.. _lsst.ts.ATDomeTrajectory-contributing:

Contributing
============

``lsst.ts.ATDomeTrajectory`` is developed at https://github.com/lsst-ts/ts_ATDomeTrajectory.
You can find Jira issues for this module using `labels=ts_ATDomeTrajectory <https://jira.lsstcorp.org/issues/?jql=project%20%3D%20DM%20AND%20labels%20%20%3D%20ts_ATDomeTrajectory>`_.

.. _lsst.ts.ATDomeTrajectory-pyapi:

Python API reference
====================

.. automodapi:: lsst.ts.ATDomeTrajectory
   :no-main-docstr:

Version History
===============

.. toctree::
    version_history
    :maxdepth: 1
