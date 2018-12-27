.. py:currentmodule:: lsst.ts.ATDomeTrajectory

.. _lsst.ts.ATDomeTrajectory:

########################
lsst.ts.ATDomeTrajectory
########################

ts_ATDomeTrajectory contains the `ATDomeTrajectoryCsc` and suport code,
including a simple `FakeATDomeCsc`.

.. .. _lsst.ts.ATDomeTrajectory-using:

Using lsst.ts.ATDomeTrajectory
==============================

ts_ATDomeTrajectory requires the following SALPY libraries:

* SALPY_ATDome
* SALPY_ATDomeTrajectory
* SALPY_PointingComponent

You can setup and build this package using eups and sconsUtils.
After setting up the package you can build it and run unit tests by typing ``scons``.
Building it merely copies ``bin.src/runATDomeTrajectory.py`` into ``bin/`` after tweaking the ``#!`` line.


To run the `ATDomeTrajectoryCsc` type ``runATDomeTrajectory.py``

.. .. toctree::
..    :maxdepth: 1

.. _lsst.ts.ATDomeTrajectory-contributing:

Contributing
============

``lsst.ts.ATDomeTrajectory`` is developed at https://github.com/lsst-ts/ts_ATDomeTrajectory.

.. If there are topics related to developing this module (rather than using it), link to this from a toctree placed here.

.. .. toctree::
..    :maxdepth: 1

.. _lsst.ts.ATDomeTrajectory-pyapi:

Python API reference
====================

.. automodapi:: lsst.ts.ATDomeTrajectory
   :no-main-docstr:
   :no-inheritance-diagram:
