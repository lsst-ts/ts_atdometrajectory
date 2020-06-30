# This file is part of ts_ATDomeTrajectory.
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

import asyncio
import math
import os
import pathlib
import unittest

import asynctest
import yaml

from lsst.ts import salobj
from lsst.ts import ATDomeTrajectory
from lsst.ts.idl.enums import ATDome

NODATA_TIMEOUT = 0.5
STD_TIMEOUT = 5  # standard command timeout (sec)
LONG_TIMEOUT = 20  # time limit for starting a SAL component (sec)
TEST_CONFIG_DIR = pathlib.Path(__file__).parents[1].joinpath("tests", "data", "config")

RAD_PER_DEG = math.pi / 180


class ATDomeTrajectoryTestCase(salobj.BaseCscTestCase, asynctest.TestCase):
    def setUp(self):
        self.dome_csc = None
        self.dome_remote = None
        self.atmcs_controller = None

    async def tearDown(self):
        for item_to_close in (self.dome_csc, self.dome_remote, self.atmcs_controller):
            if item_to_close is not None:
                await item_to_close.close()

    def basic_make_csc(self, initial_state, config_dir, simulation_mode):
        self.dome_csc = ATDomeTrajectory.FakeATDome(initial_state=salobj.State.ENABLED)
        self.dome_remote = salobj.Remote(domain=self.dome_csc.domain, name="ATDome")
        self.atmcs_controller = salobj.Controller("ATMCS")
        return ATDomeTrajectory.ATDomeTrajectory(
            initial_state=initial_state,
            config_dir=config_dir,
            simulation_mode=simulation_mode,
        )

    async def test_bin_script(self):
        """Test that run_atdometrajectory.py runs the CSC.
        """
        await self.check_bin_script(
            name="ATDomeTrajectory", index=None, exe_name="run_atdometrajectory.py",
        )

    async def test_standard_state_transitions(self):
        """Test standard CSC state transitions.
        """
        async with self.make_csc(initial_state=salobj.State.STANDBY):
            await self.check_standard_state_transitions(enabled_commands=())

    async def test_simple_follow(self):
        """Test that dome follows telescope using the "simple" algorithm.
        """
        async with self.make_csc(initial_state=salobj.State.ENABLED):

            await self.assert_next_sample(
                self.dome_remote.evt_azimuthCommandedState,
                commandedState=ATDome.AzimuthCommandedState.UNKNOWN,
            )
            elevation = 40
            min_daz_to_move = self.csc.algorithm.max_delta_azimuth / math.cos(
                elevation * RAD_PER_DEG
            )
            for azimuth in (min_daz_to_move + 0.001, 180, -0.001):
                print(f"test elevation={elevation}, azimuth={azimuth}")
                await self.check_move(elevation=elevation, azimuth=azimuth)

            await self.check_null_moves(elevation=elevation)

    async def test_default_config_dir(self):
        async with self.make_csc(initial_state=salobj.State.STANDBY):
            desired_config_pkg_name = "ts_config_attcs"
            desired_config_env_name = desired_config_pkg_name.upper() + "_DIR"
            desird_config_pkg_dir = os.environ[desired_config_env_name]
            desired_config_dir = (
                pathlib.Path(desird_config_pkg_dir) / "ATDomeTrajectory/v1"
            )
            self.assertEqual(self.csc.get_config_pkg(), desired_config_pkg_name)
            self.assertEqual(self.csc.config_dir, desired_config_dir)
            await self.csc.do_exitControl(data=None)
            await asyncio.wait_for(self.csc.done_task, timeout=5)

    async def test_configuration(self):
        async with self.make_csc(
            initial_state=salobj.State.STANDBY, config_dir=TEST_CONFIG_DIR
        ):
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
                            settingsToApply=bad_config_name, timeout=STD_TIMEOUT
                        )

            await self.remote.cmd_start.set_start(
                settingsToApply="valid.yaml", timeout=STD_TIMEOUT
            )

            settings = await self.assert_next_sample(
                self.remote.evt_algorithm, algorithmName="simple"
            )
            # max_delta_azimuth=7.1 is hard coded in the yaml file
            self.assertEqual(
                yaml.safe_load(settings.algorithmConfig), dict(max_delta_azimuth=7.1)
            )

    async def assert_dome_az(self, azimuth, move_expected):
        """Check the ATDome and ATDomeController commanded azimuth.
        """
        if move_expected:
            az_cmd_state = await self.assert_next_sample(
                self.dome_remote.evt_azimuthCommandedState,
                commandedState=ATDome.AzimuthCommandedState.GOTOPOSITION,
            )
            salobj.assertAnglesAlmostEqual(az_cmd_state.azimuth, azimuth)
        else:
            with self.assertRaises(asyncio.TimeoutError):
                await self.dome_remote.evt_azimuthCommandedState.next(
                    flush=False, timeout=NODATA_TIMEOUT
                )

    def assert_telescope_target(self, elevation, azimuth):
        salobj.assertAnglesAlmostEqual(
            self.csc.telescope_target.azimuth.position, azimuth
        )
        salobj.assertAnglesAlmostEqual(
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

        self.atmcs_controller.evt_target.set_put(
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
            if salobj.angle_diff(curr_pos.azimuthPosition, azimuth).deg < 0.1:
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
            self.atmcs_controller.evt_target.set_put(
                elevation=elevation, azimuth=target_azimuth, force_output=True
            )
            await self.assert_dome_az(azimuth, move_expected=False)
            self.assert_telescope_target(elevation=elevation, azimuth=target_azimuth)


if __name__ == "__main__":
    unittest.main()
