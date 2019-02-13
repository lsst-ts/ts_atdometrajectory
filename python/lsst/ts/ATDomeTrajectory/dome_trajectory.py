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
import SALPY_PointingComponent


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

        pointing_index = 2  # for Aux Tel.
        # Note: if the DomeTrajectory CSC is ever made identical for Aux Tel
        # and Main Tel then use the same index for both the dome trajectory
        # CSC and the pointing component CSC
        self.pointing_remote = salobj.Remote(SALPY_PointingComponent, index=pointing_index,
                                             include=["currentTargetStatus"])
        dome_index = 1  # I'm not sure, but I know it's fixed
        self.dome_remote = salobj.Remote(SALPY_ATDome, index=dome_index, include=["position"])

        # Call this after constructing the remotes so the CSC is ready
        # to receive commands when summary state is output
        super().__init__(SALPY_ATDomeTrajectory, index=None, initial_state=initial_state,
                         initial_simulation_mode=initial_simulation_mode)
        self.pointing_remote.tel_currentTargetStatus.callback = self.update_current_target_status
        self.dome_remote.tel_position.callback = self.update_dome_position
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

    async def update_current_target_status(self, current_target):
        """Callback for currentTargetStatus from PointingComponent.

        This is triggered in any summary state, but only
        commands a new dome position if enabled.
        """
        target_azalt = AltAz(az=Angle(f"{current_target.demandAz} deg"),
                             alt=Angle(f"{current_target.demandEl} deg"))
        if self.target_azalt != target_azalt:
            self.target_azalt = target_azalt
            self.log.info(f"target_azalt=({self.target_azalt.az.deg}, {self.target_azalt.alt.deg})")
            await self.follow_target()

    async def update_dome_position(self, dome_position):
        """Callback for position from ATDome.

        This is triggered in any summary state, but only
        commands a new dome position if enabled.
        """
        dome_az = Angle(dome_position.azimuthPositionSet, u.deg)
        if self.dome_cmd_az != dome_az:
            self.dome_cmd_az = dome_az
            self.log.info(f"dome_cmd_az={self.dome_cmd_az.deg}")
            await self.follow_target()

    async def follow_target(self):
        """Send the dome to a new position, if appropriate.

        This has no effect unless the summary state is enabled
        and the target and dome azimuth are known.
        """
        if self.summary_state != salobj.State.ENABLED:
            return
        if None in (self.target_azalt, self.dome_cmd_az):
            return

        desired_dome_az = self.algorithm.desired_dome_az(dome_az=self.dome_cmd_az,
                                                         target_azalt=self.target_azalt)
        if desired_dome_az is not None:
            moveAzimuth_data = self.dome_remote.cmd_moveAzimuth.DataType()
            moveAzimuth_data.azimuth = desired_dome_az.deg
            await self.dome_remote.cmd_moveAzimuth.start(moveAzimuth_data, timeout=1)
