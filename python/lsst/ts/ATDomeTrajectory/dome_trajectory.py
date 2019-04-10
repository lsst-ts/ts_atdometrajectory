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

import SALPY_ATDomeTrajectory
import SALPY_ATDome
import SALPY_ATMCS


class ATDomeTrajectory(salobj.BaseCsc):
    """ATDomeTrajectory CSC

    ATDomeTrajectory commands the dome to follow the telescope,
    using an algorithm you specify in the configuration file.
    It supports no commands beyond the standard commands.

    Parameters
    ----------
    initial_state : `salobj.State` (optional)
        The initial state of the CSC. Typically one of:
        - State.ENABLED if you want the CSC immediately usable.
        - State.STANDBY if you want full emulation of a CSC.
    initial_simulation_mode : `int` (optional)
        Initial simulation mode. This is provided for unit testing,
        as real CSCs should start up not simulating, the default.

    Notes
    -----
    **Simulation Modes**

    Supported simulation modes:

    * 0: regular operation
    * 1: simulation mode: start a mock ATDome controller and talk to it
      using SAL.
    """
    def __init__(self, initial_state=salobj.base_csc.State.STANDBY, initial_simulation_mode=0):
        self.dome_cmd_az = None
        """Commanded dome azimuth, as read from telemetry.

        An astropy.coordinates.Angle, or None before the first read.
        """
        self.target_azalt = None
        """Telescope target azimuth, as read from telemetry.

        An astropy.coordinates.Angle, or None before the first read.
        """
        self.atmcs_remote = salobj.Remote(SALPY_ATMCS, include=["target"])
        dome_index = 1  # match ts_ATDome
        self.dome_remote = salobj.Remote(SALPY_ATDome, index=dome_index, include=["azimuthCommandedState"])

        # Call this after constructing the remotes so the CSC is ready
        # to receive commands when summary state is output
        super().__init__(SALPY_ATDomeTrajectory, index=None, initial_state=initial_state,
                         initial_simulation_mode=initial_simulation_mode)
        self.atmcs_remote.evt_target.callback = self.update_target
        self.dome_remote.evt_azimuthCommandedState.callback = self.commanded_azimuth_state_callback
        self.config()

    @property
    def config_dir(self):
        """Return the path to the directory that holds configuration files.
        """
        return pathlib.Path(__file__).parents[4].joinpath("config")

    def config(self, algorithm_name="simple", algorithm_config=None):
        """Configure this CSC and output the ``settingsApplied`` event.

        Parameters
        ----------
        algorithm_name : `str`
            Name of algorithm to use for following the telescope.
            The provided name must be an entry in `AlgorithmRegistry`.
        algorithm_config : `dict` of (`str`, ``any_safe_type``)
            Configuration for the algorithm; see the algorithm for details.
            ``any_safe_type`` means any type that can be returned by
            ``yaml.safe_load``.
        """
        if algorithm_config is None:
            algorithm_config = dict()
        self.algorithm = AlgorithmRegistry[algorithm_name](**algorithm_config)
        self.evt_settingsApplied.set_put(
            algorithmName=algorithm_name,
            algorithmConfig=yaml.dump(algorithm_config),
        )

    def begin_start(self, id_data):
        """Deal with configuration.

        This will be moved to BaseCsc at some point.
        """
        config_file_name = id_data.data.settingsToApply
        if config_file_name:
            config_path = self.config_dir.joinpath(config_file_name)
            if not config_path.is_file():
                raise salobj.ExpectedError(f"Cannot find config file {config_path!s}")
            with open(config_path, "r") as config_file:
                config_data = yaml.safe_load(config_file)
        else:
            config_data = dict()
        self.config(**config_data)

    async def update_target(self, target):
        """Callback for ATMCS target event.

        This is triggered in any summary state, but only
        commands a new dome position if enabled.
        """
        target_azalt = AltAz(az=Angle(target.azimuth, u.deg), alt=Angle(target.elevation, u.deg))
        if self.target_azalt is None or self.target_azalt != target_azalt:
            self.target_azalt = target_azalt
            self.log.info(f"target_azalt=({self.target_azalt.az.deg}, {self.target_azalt.alt.deg})")
            await self.follow_target()

    async def commanded_azimuth_state_callback(self, state):
        """Callback for the ATDome commandedAzimuthState event.

        This is triggered in any summary state, but only
        commands a new dome position if enabled.
        """
        if state.commandedState != SALPY_ATDome.ATDome_shared_AzimuthCommandedState_GoToPosition:
            self.dome_cmd_az = None
            self.log.info(f"dome_cmd_az=nan")
        else:
            self.dome_cmd_az = Angle(state.azimuth, u.deg)
            self.log.info(f"dome_cmd_az={self.dome_cmd_az.deg}")
        await self.follow_target()

    async def follow_target(self):
        """Send the dome to a new position, if appropriate.

        This has no effect unless the summary state is enabled
        and the target and dome azimuth are known.
        """
        if self.summary_state != salobj.State.ENABLED:
            return
        if self.target_azalt is None:
            return
        if self.dome_cmd_az is None:
            desired_dome_az = self.target_azalt.az
        else:
            desired_dome_az = self.algorithm.desired_dome_az(dome_az=self.dome_cmd_az,
                                                             target_azalt=self.target_azalt)
        if desired_dome_az is not None:
            self.dome_remote.cmd_moveAzimuth.set(azimuth=desired_dome_az.deg)
            await self.dome_remote.cmd_moveAzimuth.start(timeout=1)
