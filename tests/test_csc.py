# This file is part of ts_atdometrajectory.
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

import asyncio
import contextlib
import math
import os
import pathlib
import unittest

import pytest
import yaml
from lsst.ts import atdometrajectory, salobj, utils
from lsst.ts.idl.enums.ATDome import AzimuthCommandedState, ShutterDoorState
from lsst.ts.idl.enums.ATDomeTrajectory import TelescopeVignetted

NODATA_TIMEOUT = 0.5
STD_TIMEOUT = 5  # standard command timeout (sec)
LONG_TIMEOUT = 20  # time limit for starting a SAL component (sec)
TEST_CONFIG_DIR = pathlib.Path(__file__).parents[1].joinpath("tests", "data", "config")

RAD_PER_DEG = math.pi / 180


class ATDomeTrajectoryTestCase(
    salobj.BaseCscTestCase, unittest.IsolatedAsyncioTestCase
):
    @classmethod
    def setUpClass(cls):
        cls._randomize_topic_subname = True
    
    @contextlib.asynccontextmanager
    async def make_csc(
        self,
        initial_state,
        config_dir=TEST_CONFIG_DIR,
        override="",
        simulation_mode=0,
        log_level=None,
    ):
        async with super().make_csc(
            initial_state=initial_state,
            config_dir=config_dir,
            override=override,
            simulation_mode=simulation_mode,
            log_level=log_level,
        ), atdometrajectory.MockDome(
            initial_state=salobj.State.ENABLED
        ) as self.dome_csc, salobj.Remote(
            domain=self.dome_csc.domain, name="ATDome"
        ) as self.dome_remote, salobj.Controller(
            "ATMCS"
        ) as self.atmcs_controller:
            await self.atmcs_controller.evt_summaryState.set_write(
                summaryState=salobj.State.ENABLED
            )
            yield

    def basic_make_csc(self, initial_state, config_dir, simulation_mode, override):
        assert simulation_mode == 0
        return atdometrajectory.ATDomeTrajectory(
            initial_state=initial_state,
            config_dir=config_dir,
            override=override,
        )

    async def test_bin_script(self):
        """Test that run_atdometrajectory runs the CSC."""
        await self.check_bin_script(
            name="ATDomeTrajectory",
            index=None,
            exe_name="run_atdometrajectory",
        )

    async def test_standard_state_transitions(self):
        """Test standard CSC state transitions."""
        async with self.make_csc(initial_state=salobj.State.STANDBY):
            await self.check_standard_state_transitions(
                enabled_commands=("setFollowingMode",)
            )

    async def test_simple_follow(self):
        """Test that dome follows telescope using the "simple" algorithm."""
        async with self.make_csc(initial_state=salobj.State.ENABLED):
            await self.assert_next_sample(self.remote.evt_followingMode, enabled=False)
            await self.assert_next_sample(
                self.dome_remote.evt_azimuthCommandedState,
                commandedState=AzimuthCommandedState.UNKNOWN,
            )

            await self.remote.cmd_setFollowingMode.set_start(
                enable=True, timeout=STD_TIMEOUT
            )
            await self.assert_next_sample(self.remote.evt_followingMode, enabled=True)
            elevation = 40
            min_daz_to_move = self.csc.algorithm.max_delta_azimuth / math.cos(
                elevation * RAD_PER_DEG
            )
            for azimuth in (min_daz_to_move + 0.001, 180, -0.001):
                print(f"test elevation={elevation}, azimuth={azimuth}")
                await self.check_move(elevation=elevation, azimuth=azimuth)

            await self.check_null_moves(elevation=elevation)

            # Turn off following and make sure the dome does not follow
            # the telescope.
            await self.remote.cmd_setFollowingMode.set_start(
                enable=False, timeout=STD_TIMEOUT
            )
            await self.assert_next_sample(self.remote.evt_followingMode, enabled=False)
            # Pretend the telescope is pointing 180 deg away from the dome;
            # that is more than enough to trigger a dome move, if following.
            new_telescope_azimuth = self.dome_csc.cmd_az + 180
            await self.atmcs_controller.evt_target.set_write(
                elevation=elevation, azimuth=new_telescope_azimuth, force_output=True
            )
            await self.assert_dome_az(azimuth=None, move_expected=False)

    async def test_telescope_vignetted(self):
        async with self.make_csc(initial_state=salobj.State.ENABLED):
            angle_margin = 0.01
            await self.assert_next_sample(self.remote.evt_followingMode, enabled=False)
            azimuth_vignette_partial = self.csc.config.azimuth_vignette_partial
            azimuth_vignette_full = self.csc.config.azimuth_vignette_full
            dropout_door_vignette_partial = (
                self.csc.config.dropout_door_vignette_partial
            )
            dropout_door_vignette_full = self.csc.config.dropout_door_vignette_full

            await self.assert_next_sample(
                topic=self.remote.evt_telescopeVignetted,
                azimuth=TelescopeVignetted.UNKNOWN,
                shutter=TelescopeVignetted.UNKNOWN,
                vignetted=TelescopeVignetted.UNKNOWN,
            )

            assert self.dome_csc.curr_az == 0
            # Wait for ATDomeTrajectory to notice that both shutter doors
            # are fully open.
            while True:
                data = await self.assert_next_sample(
                    topic=self.remote.evt_telescopeVignetted,
                    azimuth=TelescopeVignetted.UNKNOWN,
                )
                if data.shutter == TelescopeVignetted.NO:
                    break
            await self.publish_telescope_actual_position(azimuth=0, elevation=0)
            await self.assert_next_sample(
                topic=self.remote.evt_telescopeVignetted,
                azimuth=TelescopeVignetted.NO,
                shutter=TelescopeVignetted.NO,
                vignetted=TelescopeVignetted.NO,
            )

            # Move the dome far enough negative to vignette partially
            dome_az = 0 - azimuth_vignette_partial - angle_margin
            await self.dome_remote.cmd_moveAzimuth.set_start(azimuth=dome_az)
            await self.assert_next_sample(
                topic=self.remote.evt_telescopeVignetted,
                azimuth=TelescopeVignetted.PARTIALLY,
                shutter=TelescopeVignetted.NO,
                vignetted=TelescopeVignetted.PARTIALLY,
            )

            # Change telescope azimuth far enough away on the other side
            # of zero to fully vignette
            await self.publish_telescope_actual_position(
                azimuth=dome_az + azimuth_vignette_full + angle_margin
            )
            await self.assert_next_sample(
                topic=self.remote.evt_telescopeVignetted,
                azimuth=TelescopeVignetted.FULLY,
                shutter=TelescopeVignetted.NO,
                vignetted=TelescopeVignetted.FULLY,
            )

            # Increase telescope elevation high enough to partial vignetting.
            # Rather than be fancy about the math, just use a plausible value.
            await self.publish_telescope_actual_position(elevation=45)
            await self.assert_next_sample(
                topic=self.remote.evt_telescopeVignetted,
                azimuth=TelescopeVignetted.PARTIALLY,
                shutter=TelescopeVignetted.NO,
                vignetted=TelescopeVignetted.PARTIALLY,
            )

            # Increase telescope elevation high enough to full vignetting.
            # Rather than be fancy about the math, just use a plausible value.
            await self.publish_telescope_actual_position(elevation=90)
            await self.assert_next_sample(
                topic=self.remote.evt_telescopeVignetted,
                azimuth=TelescopeVignetted.NO,
                shutter=TelescopeVignetted.NO,
                vignetted=TelescopeVignetted.NO,
            )

            # Slew to azimuth = dome_az (so we don't have to worry about
            # vignetting due to azimuth), then test shutter door state
            # at various elevations, starting with 90.
            await self.publish_telescope_actual_position(azimuth=dome_az)

            await self.dome_csc.evt_dropoutDoorState.set_write(
                state=ShutterDoorState.CLOSING
            )
            await self.assert_next_sample(
                topic=self.remote.evt_telescopeVignetted,
                azimuth=TelescopeVignetted.NO,
                shutter=TelescopeVignetted.UNKNOWN,
                vignetted=TelescopeVignetted.UNKNOWN,
            )
            await self.dome_csc.evt_dropoutDoorState.set_write(
                state=ShutterDoorState.CLOSED
            )
            await self.assert_next_sample(
                topic=self.remote.evt_telescopeVignetted,
                azimuth=TelescopeVignetted.NO,
                shutter=TelescopeVignetted.NO,
                vignetted=TelescopeVignetted.NO,
            )
            await self.dome_csc.evt_mainDoorState.set_write(
                state=ShutterDoorState.CLOSING
            )
            await self.assert_next_sample(
                topic=self.remote.evt_telescopeVignetted,
                azimuth=TelescopeVignetted.NO,
                shutter=TelescopeVignetted.UNKNOWN,
                vignetted=TelescopeVignetted.UNKNOWN,
            )
            await self.dome_csc.evt_mainDoorState.set_write(
                state=ShutterDoorState.CLOSED
            )
            await self.assert_next_sample(
                topic=self.remote.evt_telescopeVignetted,
                azimuth=TelescopeVignetted.NO,
                shutter=TelescopeVignetted.FULLY,
                vignetted=TelescopeVignetted.FULLY,
            )
            await self.dome_csc.evt_mainDoorState.set_write(
                state=ShutterDoorState.OPENED
            )
            await self.assert_next_sample(
                topic=self.remote.evt_telescopeVignetted,
                azimuth=TelescopeVignetted.NO,
                shutter=TelescopeVignetted.NO,
                vignetted=TelescopeVignetted.NO,
            )

            # With only the dropout door closed, try lower elevations
            # for partial and full vignetting.
            await self.publish_telescope_actual_position(
                elevation=dropout_door_vignette_partial - angle_margin
            )
            await self.assert_next_sample(
                topic=self.remote.evt_telescopeVignetted,
                azimuth=TelescopeVignetted.NO,
                shutter=TelescopeVignetted.PARTIALLY,
                vignetted=TelescopeVignetted.PARTIALLY,
            )
            await self.publish_telescope_actual_position(
                elevation=dropout_door_vignette_full - angle_margin
            )
            await self.assert_next_sample(
                topic=self.remote.evt_telescopeVignetted,
                azimuth=TelescopeVignetted.NO,
                shutter=TelescopeVignetted.FULLY,
                vignetted=TelescopeVignetted.FULLY,
            )

            await self.dome_csc.evt_dropoutDoorState.set_write(
                state=ShutterDoorState.OPENED
            )
            await self.assert_next_sample(
                topic=self.remote.evt_telescopeVignetted,
                azimuth=TelescopeVignetted.NO,
                shutter=TelescopeVignetted.NO,
                vignetted=TelescopeVignetted.NO,
            )

            last_vignetted = TelescopeVignetted.NO
            for dome_summary_state, telescope_summary_state in zip(
                salobj.State, salobj.State
            ):
                with self.subTest(
                    dome_summary_state=dome_summary_state,
                    telescope_summary_state=telescope_summary_state,
                ):
                    # This is a bit skanky, because the mock dome CSC should
                    # report its own summary state. But the CSC cannot tell
                    # this is happening, and it has no reason to report
                    # a new summary state itself. So it works fine.
                    await self.dome_csc.evt_summaryState.set_write(
                        summaryState=dome_summary_state
                    )
                    await self.atmcs_controller.evt_summaryState.set_write(
                        summaryState=telescope_summary_state
                    )
                    if dome_summary_state in {
                        salobj.State.DISABLED,
                        salobj.State.ENABLED,
                    } and telescope_summary_state in {
                        salobj.State.DISABLED,
                        salobj.State.ENABLED,
                    }:
                        desired_vignetted = TelescopeVignetted.NO
                    else:
                        desired_vignetted = TelescopeVignetted.UNKNOWN

                    if desired_vignetted != last_vignetted:
                        await self.assert_next_sample(
                            topic=self.remote.evt_telescopeVignetted,
                            azimuth=desired_vignetted,
                            shutter=desired_vignetted,
                            vignetted=desired_vignetted,
                        )
                        last_vignetted = desired_vignetted

    async def publish_telescope_actual_position(self, azimuth=None, elevation=None):
        """Publish ATMCS actual position.

        Publish mount_AzEl_Encoders with azimuthCalculatedAngle and/or
        elevationCalculatedAngle changed as specified.
        If the new value is not None then the field is set to an array of 0s,
        except the final value, which is as specified.
        This is done in order to test the fact that ATDomeTrajectory
        only reads the final array element of these two fields.

        Parameters
        ----------
        azimuth : `float` | `None`
            Telescope actual azimuth (deg).
            If None, do not change the current value.
        elevation : `float` | `None`
            Telescope actual elevation (deg)
            If None, do not change the current value.
        """
        kwargs = dict()
        for value, fieldname in (
            (azimuth, "azimuthCalculatedAngle"),
            (elevation, "elevationCalculatedAngle"),
        ):
            if value is None:
                continue
            arr_len = len(
                getattr(self.atmcs_controller.tel_mount_AzEl_Encoders.data, fieldname)
            )
            arr = [0] * (arr_len - 1) + [value]
            kwargs[fieldname] = arr
        await self.atmcs_controller.tel_mount_AzEl_Encoders.set_write(**kwargs)

    async def test_default_config_dir(self):
        async with self.make_csc(initial_state=salobj.State.STANDBY, config_dir=None):
            await self.assert_next_sample(
                self.remote.evt_softwareVersions,
                cscVersion=atdometrajectory.__version__,
                subsystemVersions="",
            )

            desired_config_pkg_name = "ts_config_attcs"
            desired_config_env_name = desired_config_pkg_name.upper() + "_DIR"
            desired_config_pkg_dir = os.environ[desired_config_env_name]
            desired_config_dir = (
                pathlib.Path(desired_config_pkg_dir) / "ATDomeTrajectory/v4"
            )
            assert self.csc.get_config_pkg() == desired_config_pkg_name
            assert self.csc.config_dir == desired_config_dir
            await self.csc.do_exitControl(data=None)
            await asyncio.wait_for(self.csc.done_task, timeout=5)

    async def test_configuration(self):
        async with self.make_csc(initial_state=salobj.State.STANDBY):
            await self.assert_next_summary_state(salobj.State.STANDBY)

            for bad_config_name in (
                "no_such_file.yaml",
                "invalid_no_such_algorithm.yaml",
                "invalid_malformed.yaml",
                "invalid_bad_max_daz.yaml",
            ):
                with self.subTest(bad_config_name=bad_config_name):
                    with salobj.assertRaisesAckError():
                        await self.remote.cmd_start.set_start(
                            configurationOverride=bad_config_name, timeout=STD_TIMEOUT
                        )

            await self.remote.cmd_start.set_start(
                configurationOverride="valid.yaml", timeout=STD_TIMEOUT
            )

            settings = await self.assert_next_sample(
                self.remote.evt_algorithm, algorithmName="simple"
            )
            # max_delta_azimuth=7.1 is hard coded in the yaml file
            assert yaml.safe_load(settings.algorithmConfig) == dict(
                max_delta_azimuth=7.1
            )

    async def assert_dome_az(self, azimuth, move_expected):
        """Check the ATDome and ATDomeController commanded azimuth.


        Parameters
        ----------
        expected_azimuth : `float`
            Expected new azimuth position (deg);
            ignored if ``move_expected`` false.
        move_expected : `bool`
            Is a move expected?

        Notes
        -----
        If ``move_expected`` then read the next ``azimuthCommandedState``
        ATDome event.
        Otherwise try to read the next event and expect it to time out.
        """
        if move_expected:
            az_cmd_state = await self.assert_next_sample(
                self.dome_remote.evt_azimuthCommandedState,
                commandedState=AzimuthCommandedState.GOTOPOSITION,
            )
            utils.assert_angles_almost_equal(az_cmd_state.azimuth, azimuth)
        else:
            with pytest.raises(asyncio.TimeoutError):
                await self.dome_remote.evt_azimuthCommandedState.next(
                    flush=False, timeout=NODATA_TIMEOUT
                )

    def assert_telescope_target(self, elevation, azimuth):
        utils.assert_angles_almost_equal(
            self.csc.telescope_target.azimuth.position, azimuth
        )
        utils.assert_angles_almost_equal(
            self.csc.telescope_target.elevation.position, elevation
        )

    async def check_move(self, elevation, azimuth):
        """Set telescope target azimuth and check that the dome goes there.

        Then check that the dome does not move for small changes
        to the telescope target about that point.

        Parameters
        ----------
        elevation : `float`
            Desired altitude for telescope (deg)
        azimuth : `float`
            Desired azimuth for telescope and dome (deg)

        Raises
        ------
        ValueError :
            If the change in dome azimuth <= configured max dome azimuth error
            (since that will result in no dome motion, which will mess up
            the test).
        """
        max_delta_azimuth = self.csc.algorithm.max_delta_azimuth
        scaled_delta_azimuth = (azimuth - self.dome_csc.cmd_az) * math.cos(
            elevation * RAD_PER_DEG
        )
        if abs(scaled_delta_azimuth) <= max_delta_azimuth:
            raise ValueError(
                f"scaled_delta_azimuth={scaled_delta_azimuth} "
                f"must be > max_delta_azimuth={max_delta_azimuth}"
            )

        await self.atmcs_controller.evt_target.set_write(
            elevation=elevation, azimuth=azimuth, force_output=True
        )
        await self.assert_dome_az(azimuth, move_expected=True)
        self.assert_telescope_target(elevation=elevation, azimuth=azimuth)
        await asyncio.wait_for(self.wait_dome_move(azimuth), timeout=LONG_TIMEOUT)
        await self.check_null_moves(elevation)

    async def wait_dome_move(self, azimuth):
        """Wait for an ATDome azimuth move to finish.

        Parameters
        ----------
        azimuth : `float`
            Target azimuth for telescope and dome (deg)
        """
        while True:
            curr_pos = await self.dome_remote.tel_position.next(
                flush=True, timeout=STD_TIMEOUT
            )
            if utils.angle_diff(curr_pos.azimuthPosition, azimuth).deg < 0.1:
                break

    async def check_null_moves(self, elevation):
        """Check that small telescope moves do not trigger dome motion.

        Parameters
        ----------
        elevation : `float`
            Target altitude for telescope (deg)
        """
        azimuth = self.dome_csc.cmd_az
        max_delta_azimuth = self.csc.algorithm.max_delta_azimuth
        no_move_daz_deg = (max_delta_azimuth - 0.0001) * math.cos(
            elevation * RAD_PER_DEG
        )
        for target_azimuth in (
            azimuth - no_move_daz_deg,
            azimuth + no_move_daz_deg,
            azimuth,
        ):
            await self.atmcs_controller.evt_target.set_write(
                elevation=elevation, azimuth=target_azimuth, force_output=True
            )
            await self.assert_dome_az(azimuth, move_expected=False)
            self.assert_telescope_target(elevation=elevation, azimuth=target_azimuth)
