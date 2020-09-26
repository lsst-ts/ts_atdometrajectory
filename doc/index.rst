.. py:currentmodule:: lsst.ts.ATDomeTrajectory

.. _lsst.ts.ATDomeTrajectory:

########################
lsst.ts.ATDomeTrajectory
########################

.. image:: https://img.shields.io/badge/Project Metadata-gray.svg
    :target: https://ts-xml.lsst.io/index.html#index-master-csc-table-atdometrajectory
.. image:: https://img.shields.io/badge/SAL\ Interface-gray.svg
    :target: https://ts-xml.lsst.io/sal_interfaces/ATDomeTrajectory.html
.. image:: https://img.shields.io/badge/GitHub-gray.svg
    :target: https://github.com/lsst-ts/ts_ATDomeTrajectory
.. image:: https://img.shields.io/badge/Jira-gray.svg
    :target: https://jira.lsstcorp.org/issues/?jql=labels+%3D+ts_ATDomeTrajectory

Overview
========

ATDomeTrajectory moves the Vera C. Rubin Auxiliary Telescope dome to follow the telescope.
It does this by reading telescope position from the `ATMCS CSC`_ (or `ATMCSSimulator CSC`_ if simulating the ATMCS) and issuing commands to the `ATDome CSC`_.

Unlike most observatory enclosures, we plan to slowly rotate the dome during exposures, in order to minimize the time required to move to the next target.
ATDomeTrajectory supports multiple algorithms for determining how to move the dome, though at present only one simple algorithm is available.

.. _ATDome CSC: https://ts-atdome.lsst.io
.. _ATMCS CSC: https://ts-atmcs.lsst.io
.. _ATMCSSimulator CSC: https://ts-atmcssimulator.lsst.io

.. _lsst.ts.ATDomeTrajectory-user_guide:

User Guide
==========

Start the ATDomeTrajectory CSC as follows:

.. prompt:: bash

    run_atdometrajectory.py

Stop the CSC by sending it to the OFFLINE state.

To make dome track the telescope send the ATDomeTrajectory CSC to the ENABLED state.

To stop the dome from tracking the telescope (e.g. if you want to send the dome to some specific position) send the ATDomeTrajectory CSC to the DISABLED state (or any state other than ENABLED).

ATDomeTrajectory supports multiple algorithms for moving the dome.
The algorithm is specified in the :ref:`configuration <lsst.ts.ATDomeTrajectory-configuration>`.

ATDomeTrajectory can be fully exercised without hardware by running the `ATMCSSimulator CSC`_ and running `ATDome CSC`_ in simulation mode.
Thus ATDomeTrajectory does not need or have a simulation mode of its own.

.. _lsst.ts.ATDomeTrajectory-configuration:

Configuration
-------------

Configuration is defined by `this schema <https://github.com/lsst-ts/ts_ATDomeTrajectory/blob/develop/schema/ATDomeTrajectory.yaml>`_.
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
