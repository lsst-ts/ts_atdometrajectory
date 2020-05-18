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

import pathlib

from astropy.coordinates import Angle, AltAz
import astropy.units as u
import yaml

from lsst.ts import salobj
from .algorithms import AlgorithmRegistry


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

    Notes
    -----
    **Simulation Modes**

    Supported simulation modes:

    * 0: regular operation
    * 1: simulation mode: start a mock ATDome controller and talk to it
      using SAL.
    """

    def __init__(
        self,
        config_dir=None,
        initial_state=salobj.base_csc.State.STANDBY,
        simulation_mode=0,
    ):
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
            simulation_mode=simulation_mode,
        )

        self.dome_cmd_az = None
        """Commanded dome azimuth, as read from telemetry.

        An astropy.coordinates.Angle, or None before the first read.
        """

        self.target_azalt = None
        """Telescope target azimuth, as read from telemetry.

        An astropy.coordinates.Angle, or None before the first read.
        """

        self.atmcs_remote = salobj.Remote(
            domain=self.domain, name="ATMCS", include=["target"]
        )
        self.dome_remote = salobj.Remote(
            domain=self.domain, name="ATDome", include=["azimuthCommandedState"]
        )

        self.atmcs_remote.evt_target.callback = self.update_target
        self.dome_remote.evt_azimuthCommandedState.callback = (
            self.commanded_azimuth_state_callback
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

    async def update_target(self, target):
        """Callback for ATMCS target event.

        This is triggered in any summary state, but only
        commands a new dome position if enabled.
        """
        target_azalt = AltAz(
            az=Angle(target.azimuth, u.deg), alt=Angle(target.elevation, u.deg)
        )
        if self.target_azalt is None or self.target_azalt != target_azalt:
            self.target_azalt = target_azalt
            self.log.info(
                f"target_azalt=({self.target_azalt.az.deg}, {self.target_azalt.alt.deg})"
            )
            await self.follow_target()

    async def commanded_azimuth_state_callback(self, state):
        """Callback for the ATDome commandedAzimuthState event.

        This is triggered in any summary state, but only
        commands a new dome position if enabled.
        """
        if state.commandedState != 2:  # 1 is GoToPosition
            self.dome_cmd_az = None
            self.log.info("dome_cmd_az=nan")
        else:
            self.dome_cmd_az = Angle(state.azimuth, u.deg)
            self.log.info(f"dome_cmd_az={self.dome_cmd_az.deg}")
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
        if self.target_azalt is None:
            return
        if self.dome_cmd_az is None:
            desired_dome_az = self.target_azalt.az
        else:
            desired_dome_az = self.algorithm.desired_dome_az(
                dome_az=self.dome_cmd_az, target_azalt=self.target_azalt
            )
        if desired_dome_az is not None:
            self.dome_remote.cmd_moveAzimuth.set(azimuth=desired_dome_az.deg)
            await self.dome_remote.cmd_moveAzimuth.start(timeout=1)
