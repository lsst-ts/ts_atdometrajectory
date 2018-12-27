###################
ts_ATDomeTrajectory
###################

``ts_ATDomeTrajectory`` is a component of LSST Telescope and Site software.

``ts_ATDomeTrajectory`` implements the ``ts_ATDomeTrajectory`` CSC, which is responsible for
making the LSST auxiliary telescope dome follow the telescope.

The package is compatible with LSST DM's ``scons`` build system and ``eups`` package management system.
Assuming you have the basic LSST DM stack installed you can do the following, from within the package directory:

- ``setup -r .`` to setup the package and dependencies.
- ``scons`` to build the package (copy Python files from ``bin.src`` into ``bin`` after fixing the ``#!``) and run unit tests.
- ``scons install declare`` to install the package and declare it to eups.
- ``package-docs build`` to build the documentation.
  This requires ``documenteer``; see `building single package docs`_ for installation instructions.

.. _building single package docs: https://developer.lsst.io/stack/building-single-package-docs.html
