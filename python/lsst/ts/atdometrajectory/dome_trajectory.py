#
# Developed for Vera C. Rubin Observatory Telescope and Site Systems.
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

__all__ = ["ATDomeTrajectory", "run_atdometrajectory"]

import asyncio
import math

import yaml
from lsst.ts import salobj, simactuators, utils
from lsst.ts.xml.enums.ATDome import AzimuthCommandedState, ShutterDoorState
from lsst.ts.xml.enums.ATDomeTrajectory import TelescopeVignetted

from . import __version__
from .base_algorithm import AlgorithmRegistry
from .config_schema import CONFIG_SCHEMA
from .elevation_azimuth import ElevationAzimuth

# Timeout for commands that should be executed quickly.
STD_TIMEOUT = 5

# Time (sec) between polling for vignetting.
VIGNETTING_MONITOR_INTERVAL = 0.1


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
    override : `str`, optional
        Configuration override to apply if ``initial_state`` is
        `State.DISABLED` or `State.ENABLED`.
    """

    valid_simulation_modes = [0]
    version = __version__

    def __init__(
        self,
        config_dir=None,
        initial_state=salobj.base_csc.State.STANDBY,
        override="",
    ):
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
        self.move_dome_azimuth_task = utils.make_done_future()

        # Next telescope target, eventually from the scheduler;
        # an ElevationAzimuth; None before the next target is seen;
        self.next_telescope_target = None

        super().__init__(
            name="ATDomeTrajectory",
            config_schema=CONFIG_SCHEMA,
            config_dir=config_dir,
            index=None,
            initial_state=initial_state,
            override=override,
            simulation_mode=0,
        )

        self.atmcs_remote = salobj.Remote(
            domain=self.domain,
            name="ATMCS",
            include=["mount_AzEl_Encoders", "summaryState", "target"],
        )
        self.dome_remote = salobj.Remote(
            domain=self.domain,
            name="ATDome",
            include=[
                "azimuthCommandedState",
                "dropoutDoorState",
                "mainDoorState",
                "position",
                "summaryState",
            ],
        )

        self.atmcs_remote.evt_target.callback = self.atmcs_target_callback
        self.dome_remote.evt_azimuthCommandedState.callback = (
            self.atdome_commanded_azimuth_state_callback
        )
        self.report_vignetted_task = utils.make_done_future()
        self.distance_to_dome_at_horizon = None

    @staticmethod
    def get_config_pkg():
        return "ts_config_attcs"

    @property
    def following_enabled(self):
        """Is following enabled?

        False if the CSC is not in the ENABLED state
        or if following is not enabled.
        """
        if self.summary_state != salobj.State.ENABLED:
            return False
        return self.evt_followingMode.data.enabled

    async def configure(self, config):
        """Configure this CSC and output the ``algorithm`` event.

        Parameters
        ----------
        config : `types.SimpleNamespace`
            Configuration, as described by `CONFIG_SCHEMA`
        """
        algorithm_name = config.algorithm_name
        if algorithm_name not in AlgorithmRegistry:
            raise salobj.ExpectedError(f"Unknown algorithm {algorithm_name}")
        algorithm_config = getattr(config, config.algorithm_name)
        self.algorithm = AlgorithmRegistry[config.algorithm_name](**algorithm_config)
        self.config = config
        await self.evt_algorithm.set_write(
            algorithmName=config.algorithm_name,
            algorithmConfig=yaml.dump(algorithm_config),
        )
        self.distance_to_dome_at_horizon = self.compute_distance_to_dome(0)

    async def close_tasks(self):
        self.move_dome_azimuth_task.cancel()
        self.report_vignetted_task.cancel()
        try:
            await self.report_vignetted_task
        except asyncio.CancelledError:
            # Ignore because deliberately cancelled.
            pass
        await self.evt_telescopeVignetted.set_write(
            vignetted=TelescopeVignetted.UNKNOWN,
            azimuth=TelescopeVignetted.UNKNOWN,
            shutter=TelescopeVignetted.UNKNOWN,
        )
        await super().close_tasks()

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

    def compute_distance_to_dome(self, elevation):
        """Compute distance (mm) from telescope center to inner edge of dome
        slit.

        Parameters
        ----------
        elevation : `float`
          Telescope elevation (deg).

        Returns
        -------
        distance_to_dome : `float`
            Distance to dome at the specified telewscope elevation (mm).
        """
        # The equations break down at the zenith, but we can get close enough
        # by stopping just short of it.
        elevation = min(elevation, 89.999)

        # Use the standard triangle equations:
        #
        # c = a * sin(C) / sin(A)
        # B = arcsin(b/a sin(A))
        # C = 180 - A - B
        #
        # Where the triangle has these quantities:
        #
        # * angle_a: elevation + 90
        # * side_a: dome inner radius
        # * side_b: telescope height offset
        # * side_c: distance from telescope center to dome (value to compute)
        side_a = self.config.dome_inner_radius
        side_b = self.config.telescope_height_offset
        angle_a_rad = math.radians(elevation + 90)
        angle_b_rad = math.asin(side_b / side_a * math.sin(angle_a_rad))
        angle_c_rad = math.pi - angle_b_rad - angle_a_rad
        return side_a * math.sin(angle_c_rad) / math.sin(angle_a_rad)

    def compute_vignetted_by_azimuth(
        self, *, dome_azimuth, telescope_azimuth, telescope_elevation
    ):
        """Compute the ``azimuth`` field of the telescopeVignetted event.

        Parameters
        ----------
        dome_azimuth : `float` | None
            Dome current azimuth (deg); None if unknown.
        telescope_azimuth : `float` | None
            Telescope current azimuth (deg); None if unknown.
        telescope_elevation : `float` | None
            Telescope current elevation (deg); None if unknown.

        Returns
        -------
        azimuth : `TelescopeVignetted`
            Telescope vignetted by azimuth mismatch between telescope and dome.
        """
        if (
            dome_azimuth is None
            or telescope_azimuth is None
            or telescope_elevation is None
        ):
            return TelescopeVignetted.UNKNOWN

        abs_azimuth_difference = abs(
            utils.angle_diff(dome_azimuth, telescope_azimuth).deg
        )
        distance_to_dome = self.compute_distance_to_dome(telescope_elevation)
        scaled_abs_azimuth_difference = (
            abs_azimuth_difference
            * math.cos(math.radians(telescope_elevation))
            * self.distance_to_dome_at_horizon
            / distance_to_dome
        )
        if scaled_abs_azimuth_difference < self.config.azimuth_vignette_partial:
            return TelescopeVignetted.NO
        elif scaled_abs_azimuth_difference < self.config.azimuth_vignette_full:
            return TelescopeVignetted.PARTIALLY
        return TelescopeVignetted.FULLY

    def compute_vignetted_by_shutter(
        self, *, dome_dropout_door_state, dome_main_door_state, telescope_elevation
    ):
        """Compute the ``shutter`` field of the telescopeVignetted event.

        Parameters
        ----------
        dome_dropout_door_state : `ShutterDoorState` | None
            Dome dropout door state; None if unknown.
        dome_main_door_state : `ShutterDoorState` | None
            Dome main door state; None if unknown.
        telescope_elevation : `float` | None
            Telescope current elevation (deg); None if unknown.

        Returns
        -------
        shutter : `TelescopeVignetted`
            Telescope vignetted by shutter.
        """
        if dome_dropout_door_state is None or dome_main_door_state is None:
            return TelescopeVignetted.UNKNOWN
        elif (
            dome_dropout_door_state == ShutterDoorState.OPENED
            and dome_main_door_state == ShutterDoorState.OPENED
        ):
            return TelescopeVignetted.NO
        elif (
            dome_dropout_door_state == ShutterDoorState.CLOSED
            and dome_main_door_state == ShutterDoorState.CLOSED
        ):
            return TelescopeVignetted.FULLY
        elif (
            dome_dropout_door_state == ShutterDoorState.CLOSED
            and dome_main_door_state == ShutterDoorState.OPENED
        ):
            # The dropout door is closed and the main door is opened,
            # so vignetting depends on telescope elevation.
            if telescope_elevation is None:
                return TelescopeVignetted.UNKNOWN
            elif telescope_elevation > self.config.dropout_door_vignette_partial:
                return TelescopeVignetted.NO
            elif telescope_elevation > self.config.dropout_door_vignette_full:
                return TelescopeVignetted.PARTIALLY
            return TelescopeVignetted.FULLY
        return TelescopeVignetted.UNKNOWN

    def compute_vignetted_by_any(self, *, azimuth, shutter):
        """Compute the ``vignetted`` field of the telescopeVignetted event."""
        if (
            azimuth == TelescopeVignetted.UNKNOWN
            or shutter == TelescopeVignetted.UNKNOWN
        ):
            return TelescopeVignetted.UNKNOWN
        elif azimuth == TelescopeVignetted.NO and shutter == TelescopeVignetted.NO:
            return TelescopeVignetted.NO
        elif azimuth == TelescopeVignetted.FULLY or shutter == TelescopeVignetted.FULLY:
            return TelescopeVignetted.FULLY
        return TelescopeVignetted.PARTIALLY

    async def do_setFollowingMode(self, data):
        """Handle the setFollowingMode command."""
        self.assert_enabled()
        if data.enable:
            # Report following enabled and trigger an update
            await self.evt_followingMode.set_write(enabled=True)
            await self.follow_target()
        else:
            await self.evt_followingMode.set_write(enabled=False)
            self.move_dome_azimuth_task.cancel()

    async def follow_target(self):
        """Send the dome to a new position, if appropriate.

        This has no effect unless the summary state is enabled,
        the CSC and remotes have fully started,
        and the target azimuth is known.
        """
        if not self.following_enabled:
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
                self.move_dome_azimuth_task = asyncio.create_task(
                    self.move_dome_azimuth(desired_dome_azimuth)
                )

    def get_dome_azimuth(self):
        """Get current dome azimuth (deg), or None if unavailable."""
        dome_position = self.dome_remote.tel_position.get()
        if dome_position is None:
            return None
        return dome_position.azimuthPosition

    def get_dome_dropout_door_state(self):
        """Get current dome dropout door state, or None if unavailable."""
        dome_dropout_door_state = self.dome_remote.evt_dropoutDoorState.get()
        if dome_dropout_door_state is None:
            return None
        return dome_dropout_door_state.state

    def get_dome_main_door_state(self):
        """Get current dome main door state, or None if unavailable."""
        dome_main_door_state = self.dome_remote.evt_mainDoorState.get()
        if dome_main_door_state is None:
            return None
        return dome_main_door_state.state

    def get_dome_summary_state(self):
        """Get ATDome summary state, or None if unavailable."""
        dome_state = self.dome_remote.evt_summaryState.get()
        if dome_state is None:
            return None
        return dome_state.summaryState

    def get_telescope_azimuth_elevation(self):
        """Get current azimuth and elevation of the telescope (deg).

        Return (None, None) if unavailable.
        """
        telescope_encoders = self.atmcs_remote.tel_mount_AzEl_Encoders.get()
        if telescope_encoders is None:
            return (None, None)
        return (
            telescope_encoders.azimuthCalculatedAngle[-1],
            telescope_encoders.elevationCalculatedAngle[-1],
        )

    def get_telescope_summary_state(self):
        """Get ATMCS summary state, or None if unavailable."""
        telescope_state = self.atmcs_remote.evt_summaryState.get()
        if telescope_state is None:
            return None
        return telescope_state.summaryState

    async def handle_summary_state(self):
        if not self.summary_state == salobj.State.ENABLED:
            self.move_dome_azimuth_task.cancel()
            self.report_vignetted_task.cancel()
            try:
                await self.report_vignetted_task
            except asyncio.CancelledError:
                # Ignore because deliberately cancelled.
                pass
            await self.evt_followingMode.set_write(enabled=False)
        if self.disabled_or_enabled:
            if self.report_vignetted_task.done():
                self.report_vignetted_task = asyncio.create_task(
                    self.report_vignetted_loop()
                )
        else:
            self.report_vignetted_task.cancel()
            try:
                await self.report_vignetted_task
            except asyncio.CancelledError:
                # Ignore because deliberately cancelled.
                pass
            await self.evt_telescopeVignetted.set_write(
                vignetted=TelescopeVignetted.UNKNOWN,
                azimuth=TelescopeVignetted.UNKNOWN,
                shutter=TelescopeVignetted.UNKNOWN,
            )

    async def report_vignetted_loop(self):
        """Poll ATMCS and ATDome topics to report telescopeVignetted event."""
        self.log.info("report_vignetted_loop begins")
        ok_states = frozenset((salobj.State.DISABLED, salobj.State.ENABLED))
        try:
            while True:
                dome_state = self.get_dome_summary_state()
                telescope_state = self.get_telescope_summary_state()
                if dome_state not in ok_states or telescope_state not in ok_states:
                    azimuth = TelescopeVignetted.UNKNOWN
                    shutter = TelescopeVignetted.UNKNOWN
                else:
                    (
                        telescope_azimuth,
                        telescope_elevation,
                    ) = self.get_telescope_azimuth_elevation()
                    dome_azimuth = self.get_dome_azimuth()
                    dome_dropout_door_state = self.get_dome_dropout_door_state()
                    dome_main_door_state = self.get_dome_main_door_state()
                    azimuth = self.compute_vignetted_by_azimuth(
                        dome_azimuth=dome_azimuth,
                        telescope_azimuth=telescope_azimuth,
                        telescope_elevation=telescope_elevation,
                    )
                    shutter = self.compute_vignetted_by_shutter(
                        dome_dropout_door_state=dome_dropout_door_state,
                        dome_main_door_state=dome_main_door_state,
                        telescope_elevation=telescope_elevation,
                    )
                vignetted = self.compute_vignetted_by_any(
                    azimuth=azimuth, shutter=shutter
                )
                await self.evt_telescopeVignetted.set_write(
                    vignetted=vignetted, azimuth=azimuth, shutter=shutter
                )
                await asyncio.sleep(VIGNETTING_MONITOR_INTERVAL)
        except asyncio.CancelledError:
            self.log.info("report_vignetted_loop ends")
        except Exception as e:
            self.log.exception(f"report_vignetted_loop failed: {e!r}")
        await self.evt_telescopeVignetted.set_write(
            vignetted=TelescopeVignetted.UNKNOWN,
            azimuth=TelescopeVignetted.UNKNOWN,
            shutter=TelescopeVignetted.UNKNOWN,
        )

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

    async def start(self):
        await super().start()
        await self.dome_remote.start_task
        await self.evt_telescopeVignetted.set_write(
            vignetted=TelescopeVignetted.UNKNOWN,
            azimuth=TelescopeVignetted.UNKNOWN,
            shutter=TelescopeVignetted.UNKNOWN,
        )


def run_atdometrajectory():
    """Run the ATDomeTrajectory CSC."""
    asyncio.run(ATDomeTrajectory.amain(index=None))
