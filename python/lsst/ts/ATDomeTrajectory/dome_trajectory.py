#
# Developed for the LSST Telescope and Site Systems.
# This product includes software developed by the LSST Project
# (https://www.lsst.org).
# See the COPYRIGHT file at the top-level directory of this distribution
# for details of code ownership.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

__all__ = ["ATDomeTrajectory"]

import asyncio
import pathlib

import yaml

from lsst.ts import salobj
from lsst.ts import simactuators
from lsst.ts.idl.enums.ATDome import AzimuthCommandedState
from . import __version__
from .elevation_azimuth import ElevationAzimuth
from .base_algorithm import AlgorithmRegistry

# Timeout for commands that should be executed quickly
STD_TIMEOUT = 5


class ATDomeTrajectory(salobj.ConfigurableCsc):
    """ATDomeTrajectory CSC

    ATDomeTrajectory commands the dome to follow the telescope,
    using an algorithm you specify in the configuration file.
    It supports no commands beyond the standard commands.

    Parameters
    ----------
    config_dir : `str` (optional)
        Directory of configuration files, or None for the standard
        configuration directory (obtained from `get_default_config_dir`).
        This is provided for unit testing.
    initial_state : `salobj.State` (optional)
        The initial state of the CSC. Typically one of:
        - State.ENABLED if you want the CSC immediately usable.
        - State.STANDBY if you want full emulation of a CSC.
    simulation_mode : `int` (optional)
        Simulation mode. This is provided for unit testing,
        as real CSCs should start up not simulating, the default.
    """

    valid_simulation_modes = [0]
    version = __version__

    def __init__(self, config_dir=None, initial_state=salobj.base_csc.State.STANDBY):
        schema_path = (
            pathlib.Path(__file__)
            .parents[4]
            .joinpath("schema", "ATDomeTrajectory.yaml")
        )
        super().__init__(
            name="ATDomeTrajectory",
            schema_path=schema_path,
            config_dir=config_dir,
            index=None,
            initial_state=initial_state,
            simulation_mode=0,
        )

        # Commanded dome azimuth (deg), from the ATDome azimuthCommandedState
        # event; None before the event is seen.
        self.dome_target_azimuth = None

        # Telescope target, from the ATMCS target event;
        # an ElevationAzimuth; None before a target is seen.
        self.telescope_target = None

        # Task that starts dome azimuth motion
        # and waits for the motionState and target events
        # that indicate the motion has started.
        # While running that axis will not be commanded.
        # This avoids the problem of new telescope target events
        # causing unwanted motion when the dome has been commanded
        # but has not yet had a chance to report the fact.
        self.move_dome_azimuth_task = salobj.make_done_future()

        # Task that is set to (moved_elevation, moved_azimuth)
        # whenever the follow_target method runs.
        self.follow_task = asyncio.Future()

        # Next telescope target, eventually from the scheduler;
        # an ElevationAzimuth; None before the next target is seen;
        self.next_telescope_target = None

        self.atmcs_remote = salobj.Remote(
            domain=self.domain, name="ATMCS", include=["target"]
        )
        self.dome_remote = salobj.Remote(
            domain=self.domain, name="ATDome", include=["azimuthCommandedState"]
        )

        self.atmcs_remote.evt_target.callback = self.atmcs_target_callback
        self.dome_remote.evt_azimuthCommandedState.callback = (
            self.atdome_commanded_azimuth_state_callback
        )

    @staticmethod
    def get_config_pkg():
        return "ts_config_attcs"

    async def configure(self, config):
        """Configure this CSC and output the ``algorithm`` event.

        Parameters
        ----------
        config : `types.SimpleNamespace`
            Configuration, as described by ``schema/ATDomeTrajectory.yaml``
        """
        self.algorithm = AlgorithmRegistry[config.algorithm_name](
            **config.algorithm_config
        )
        self.evt_algorithm.set_put(
            algorithmName=config.algorithm_name,
            algorithmConfig=yaml.dump(config.algorithm_config),
        )

    async def atmcs_target_callback(self, target):
        """Callback for ATMCS target event.

        This is triggered in any summary state, but only
        commands a new dome position if enabled.
        """
        telescope_target = ElevationAzimuth(
            elevation=simactuators.path.PathSegment(
                position=target.elevation,
                velocity=target.elevationVelocity,
                tai=target.taiTime,
            ),
            azimuth=simactuators.path.PathSegment(
                position=target.azimuth,
                velocity=target.azimuthVelocity,
                tai=target.taiTime,
            ),
        )
        self.telescope_target = telescope_target
        await self.follow_target()

    async def atdome_commanded_azimuth_state_callback(self, state):
        """Callback for the ATDome commandedAzimuthState event.

        This is triggered in any summary state, but only
        commands a new dome position if enabled.
        """
        if state.commandedState != AzimuthCommandedState.GOTOPOSITION:
            self.dome_target_azimuth = None
            self.log.info("dome_target_azimuth=nan")
        else:
            self.dome_target_azimuth = state.azimuth
            self.log.info(f"dome_target_azimuth={self.dome_target_azimuth}")
        await self.follow_target()

    async def follow_target(self):
        """Send the dome to a new position, if appropriate.

        This has no effect unless the summary state is enabled,
        the CSC and remotes have fully started,
        and the target azimuth is known.
        """
        if self.summary_state != salobj.State.ENABLED:
            return
        if not self.start_task.done():
            return
        if self.telescope_target is None:
            return
        if self.move_dome_azimuth_task.done():
            desired_dome_azimuth = self.algorithm.desired_dome_azimuth(
                dome_target_azimuth=self.dome_target_azimuth,
                telescope_target=self.telescope_target,
            )
            if desired_dome_azimuth is not None:
                moved_azimuth = True
                self.move_dome_azimuth_task = asyncio.create_task(
                    self.move_dome_azimuth(desired_dome_azimuth)
                )

        if not self.follow_task.done():
            self.follow_task.set_result(moved_azimuth)

    async def handle_summary_state(self):
        if not self.summary_state == salobj.State.ENABLED:
            self.move_dome_azimuth_task.cancel()
            self.follow_task.cancel()

    def make_follow_task(self):
        """Make and return a task that is set when the follow method runs.

        The result of the task is (moved_elevation, moved_azimuth).
        This method is intended for unit tests.
        """
        self.follow_task = asyncio.Future()
        return self.follow_task

    async def move_dome_azimuth(self, desired_dome_azimuth):
        """Start moving the dome in azimuth.

        Parameters
        ----------
        desired_dome_azimuth : `lsst.ts.simactuators.path.PathSegment`
            Desired dome azimuth.
        """
        await self.dome_remote.cmd_moveAzimuth.set_start(
            azimuth=desired_dome_azimuth, timeout=STD_TIMEOUT
        )
