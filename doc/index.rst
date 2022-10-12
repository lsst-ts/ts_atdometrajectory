.. py:currentmodule:: lsst.ts.atdometrajectory

.. _lsst.ts.atdometrajectory:

########################
lsst.ts.atdometrajectory
########################

.. image:: https://img.shields.io/badge/Project Metadata-gray.svg
    :target: https://ts-xml.lsst.io/index.html#index-master-csc-table-atdometrajectory
.. image:: https://img.shields.io/badge/SAL\ Interface-gray.svg
    :target: https://ts-xml.lsst.io/sal_interfaces/ATDomeTrajectory.html
.. image:: https://img.shields.io/badge/GitHub-gray.svg
    :target: https://github.com/lsst-ts/ts_atdometrajectory
.. image:: https://img.shields.io/badge/Jira-gray.svg
    :target: https://jira.lsstcorp.org/issues/?jql=project%3DDM%20AND%20labels%3Dts_atdometrajectory

Overview
========

ATDomeTrajectory moves the Vera C. Rubin Auxiliary Telescope dome to follow the telescope.
It does this by reading telescope position from the `ATMCS CSC`_ (or `ATMCSSimulator CSC`_ if simulating the ATMCS) and issuing commands to the `ATDome CSC`_.

Unlike most observatory enclosures, we plan to slowly rotate the dome during exposures, in order to minimize the time required to move to the next target.
ATDomeTrajectory supports multiple algorithms for determining how to move the dome, though at present only one simple algorithm is available.

.. _ATDome CSC: https://ts-atdome.lsst.io
.. _ATMCS CSC: https://ts-atmcs.lsst.io
.. _ATMCSSimulator CSC: https://ts-atmcssimulator.lsst.io

.. _lsst.ts.atdometrajectory-user_guide:

User Guide
==========

Start the ATDomeTrajectory CSC as follows:

.. prompt:: bash

    run_atdometrajectory

Stop the CSC by sending it to the OFFLINE state.

To make the dome follow the telescope: issue the ATDomeTrajectory
`setEnabledMode <https://ts-xml.lsst.io/sal_interfaces/ATDomeTrajectory.html#setenabledmode>`_ command
with ``enabled=True``.

To move the dome to a specified azimuth that is different from the telescope's azimuth:

* Stop the dome from following: issue the ATDomeTrajectory `setEnabledMode command`_ with ``enabled=False``.
* Move the dome: issue the ATDome `moveAzimuth command`_ with ``azimuth=desired_azimuth``.

ATDomeTrajectory can support multiple algorithms for making the dome follow the telescope;
but at the time of this writing, there is only one.
The algorithm is specified and configured in :ref:`configuration <lsst.ts.atdometrajectory-configuration>`.

Simulation
----------

ATDomeTrajectory can be fully exercised without hardware by running the `ATMCSSimulator CSC`_ and running `ATDome CSC`_ in simulation mode.
ATDomeTrajectory does not have a simulation mode of its own.

.. _setEnabledMode command: https://ts-xml.lsst.io/sal_interfaces/ATDomeTrajectory.html#setenabledmode
.. _moveAzimuth command: https://ts-xml.lsst.io/sal_interfaces/ATDome.html#moveazimuth

.. _lsst.ts.atdometrajectory-configuration:

Configuration
-------------

Configuration is defined by `CONFIG_SCHEMA <https://github.com/lsst-ts/ts_atdometrajectory/blob/main/python/lsst/ts/atdometrajectory/config_schema.py>`_.
Configuration primarily consists of specifying the control algorithm and its associated parameters.

Available algorithms:

* `SimpleAlgorithm`

Configuration files live in `ts_config_attcs/ATDomeTrajectory <https://github.com/lsst-ts/ts_config_attcs/tree/develop/ATDomeTrajectory>`_.

Here is a sample configuration file that specifies all fields::

    # We strongly suggest that you specify the algorithm name
    # if you override any of the algorithm's default configuration.
    # That way your configuration file will continue to work
    # even if the default algorithm changes.
    algorithm_name: "simple"
    algorithm_config:
      # This value is abitrary and merely for illustration.
      # It can be omitted, and the default is reasonable.
      max_delta_azimuth: 3.5

Developer Guide
===============

.. toctree::
    developer_guide
    :maxdepth: 1

Version History
===============

.. toctree::
    version_history
    :maxdepth: 1
