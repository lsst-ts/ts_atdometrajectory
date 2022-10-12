.. py:currentmodule:: lsst.ts.atdometrajectory

.. _lsst.ts.atdometrajectory.developer_guide:

###############
Developer Guide
###############

.. image:: https://img.shields.io/badge/Project Metadata-gray.svg
    :target: https://ts-xml.lsst.io/index.html#index-master-csc-table-atdometrajectory
.. image:: https://img.shields.io/badge/SAL\ Interface-gray.svg
    :target: https://ts-xml.lsst.io/sal_interfaces/ATDomeTrajectory.html
.. image:: https://img.shields.io/badge/GitHub-gray.svg
    :target: https://github.com/lsst-ts/ts_atdometrajectory
.. image:: https://img.shields.io/badge/Jira-gray.svg
    :target: https://jira.lsstcorp.org/issues/?jql=project%3DDM%20AND%20labels%3Dts_atdometrajectory

The ATDomeTrajectory CSC is implemented using `ts_salobj <https://ts-salobj.lsst.io/>`_.

.. _lsst.ts.atdometrajectory-api:

API
===

The primary classes are:

* `ATDomeTrajectory`: the CSC.
* `BaseAlgorithm`: base class for motion algorithms.
* `SimpleAlgorithm`: a simple motion algorithm.

.. automodapi:: lsst.ts.atdometrajectory
   :no-main-docstr:

.. _lsst.ts.atdometrajectory-build_and_test:

Build and Test
==============

This is a pure python package.
There is nothing to build except the documentation.

.. code-block:: bash

    make_idl_files.py ATDomeTrajectory
    setup -r .
    pytest -v  # to run tests
    package-docs clean; package-docs build  # to build the documentation
