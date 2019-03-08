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
import unittest

import yaml

from lsst.ts import salobj
from lsst.ts import ATDomeTrajectory
import SALPY_ATDomeTrajectory
import SALPY_ATDome
import SALPY_ATMCS

STD_TIMEOUT = 2  # standard command timeout (sec);


class Harness:
    def __init__(self, initial_state):
        self.dome_index = 1  # match ts_ATDome
        self.dome_csc = ATDomeTrajectory.FakeATDome(index=self.dome_index, initial_state=salobj.State.ENABLED)
        self.dome_remote = salobj.Remote(SALPY_ATDome, index=self.dome_index)
        self.atmcs_controller = salobj.Controller(SALPY_ATMCS)
        self.csc = ATDomeTrajectory.ATDomeTrajectory(initial_state=initial_state)
        self.remote = salobj.Remote(SALPY_ATDomeTrajectory, index=None)


class ATDomeTrajectoryTestCase(unittest.TestCase):
    def setUp(self):
        salobj.test_utils.set_random_lsst_dds_domain()

    def test_main(self):
        async def doit():
            """Test that runATDomeTrajectory.py runs the CSC.
            """
            process = await asyncio.create_subprocess_exec("runATDomeTrajectory.py")
            try:
                remote = salobj.Remote(SALPY_ATDomeTrajectory, index=None)
                summaryState_data = await remote.evt_summaryState.next(flush=False, timeout=20)
                self.assertEqual(summaryState_data.summaryState, salobj.State.STANDBY)
                self.assertIsNone(process.returncode)

                remote.cmd_start.set(settingsToApply="default.yaml")
                await remote.cmd_start.start(timeout=STD_TIMEOUT)
                summaryState_data = await remote.evt_summaryState.next(flush=False, timeout=STD_TIMEOUT)
                self.assertEqual(summaryState_data.summaryState, salobj.State.DISABLED)
                self.assertIsNone(process.returncode)

                await remote.cmd_standby.start(timeout=STD_TIMEOUT)
                summaryState_data = await remote.evt_summaryState.next(flush=False, timeout=STD_TIMEOUT)
                self.assertEqual(summaryState_data.summaryState, salobj.State.STANDBY)

                await remote.cmd_exitControl.start(timeout=STD_TIMEOUT)
                summaryState_data = await remote.evt_summaryState.next(flush=False, timeout=STD_TIMEOUT)
                self.assertEqual(summaryState_data.summaryState, salobj.State.OFFLINE)

                await asyncio.wait_for(process.wait(), 2)
            except Exception:
                if process.returncode is None:
                    process.terminate()
                raise

        asyncio.get_event_loop().run_until_complete(doit())

    def test_standard_state_transitions(self):
        """Test standard CSC state transitions.
        """
        async def doit():
            harness = Harness(initial_state=salobj.State.STANDBY)
            self.assertEqual(harness.csc.summary_state, salobj.State.STANDBY)
            state = await harness.remote.evt_summaryState.next(flush=False, timeout=STD_TIMEOUT)
            self.assertEqual(state.summaryState, salobj.State.STANDBY)
            self.assertIsNone(harness.csc.dome_cmd_az)

            # send start; new state is DISABLED
            harness.remote.cmd_start.set(settingsToApply="default.yaml")
            await harness.remote.cmd_start.start(timeout=STD_TIMEOUT)
            self.assertEqual(harness.csc.summary_state, salobj.State.DISABLED)
            state = await harness.remote.evt_summaryState.next(flush=False, timeout=STD_TIMEOUT)
            self.assertEqual(state.summaryState, salobj.State.DISABLED)

            # send enable; new state is ENABLED
            await harness.remote.cmd_enable.start(timeout=STD_TIMEOUT)
            self.assertEqual(harness.csc.summary_state, salobj.State.ENABLED)
            state = await harness.remote.evt_summaryState.next(flush=False, timeout=STD_TIMEOUT)
            self.assertEqual(state.summaryState, salobj.State.ENABLED)

            # if the dome indices  don't match then other tests will fail
            self.assertEqual(harness.csc.dome_remote.salinfo.index, harness.dome_index)

            # send disable; new state is DISABLED
            await harness.remote.cmd_disable.start(timeout=STD_TIMEOUT)
            self.assertEqual(harness.csc.summary_state, salobj.State.DISABLED)
            state = await harness.remote.evt_summaryState.next(flush=False, timeout=STD_TIMEOUT)
            self.assertEqual(state.summaryState, salobj.State.DISABLED)

            # send standby; new state is STANDBY
            await harness.remote.cmd_standby.start(timeout=STD_TIMEOUT)
            self.assertEqual(harness.csc.summary_state, salobj.State.STANDBY)
            state = await harness.remote.evt_summaryState.next(flush=False, timeout=STD_TIMEOUT)
            self.assertEqual(state.summaryState, salobj.State.STANDBY)

            # send exitControl; new state is OFFLINE
            await harness.remote.cmd_exitControl.start(timeout=STD_TIMEOUT)
            self.assertEqual(harness.csc.summary_state, salobj.State.OFFLINE)
            state = await harness.remote.evt_summaryState.next(flush=False, timeout=STD_TIMEOUT)
            self.assertEqual(state.summaryState, salobj.State.OFFLINE)

            await asyncio.wait_for(harness.csc.done_task, 2)

        asyncio.get_event_loop().run_until_complete(doit())

    def test_simple_follow(self):
        """Test that dome follows telescope using the "simple" algorithm.
        """
        async def doit():
            harness = Harness(initial_state=salobj.State.ENABLED)
            self.assertEqual(harness.csc.summary_state, salobj.State.ENABLED)
            state = await harness.remote.evt_summaryState.next(flush=False, timeout=STD_TIMEOUT)
            self.assertEqual(state.summaryState, salobj.State.ENABLED)

            await self.check_null_moves(harness, alt_deg=0)

            max_daz_deg = harness.csc.algorithm.max_daz.deg
            for az_deg in (max_daz_deg + 0.001, 180, -0.001):
                with self.subTest(az_deg=az_deg):
                    await self.check_move(harness, az_deg, alt_deg=0)

        asyncio.get_event_loop().run_until_complete(doit())

    def test_configuration(self):
        async def doit():
            harness = Harness(initial_state=salobj.State.STANDBY)
            self.assertEqual(harness.csc.summary_state, salobj.State.STANDBY)
            state = await harness.remote.evt_summaryState.next(flush=False, timeout=STD_TIMEOUT)
            self.assertEqual(state.summaryState, salobj.State.STANDBY)
            settings = await harness.remote.evt_settingsApplied.next(flush=False, timeout=STD_TIMEOUT)
            self.assertEqual(settings.algorithmName, "simple")
            self.assertEqual(yaml.safe_load(settings.algorithmConfig), dict())

            # missing config file
            harness.remote.cmd_start.set(settingsToApply="no_such_file.yaml")
            with salobj.test_utils.assertRaisesAckError():
                await harness.remote.cmd_start.start(timeout=STD_TIMEOUT)

            # invalid configuration
            harness.remote.cmd_start.set(settingsToApply="invalid_no_such_algorithm.yaml")
            with salobj.test_utils.assertRaisesAckError():
                await harness.remote.cmd_start.start(timeout=STD_TIMEOUT)

            # invalid configuration
            harness.remote.cmd_start.set(settingsToApply="invalid_malformed.yaml")
            with salobj.test_utils.assertRaisesAckError():
                await harness.remote.cmd_start.start(timeout=STD_TIMEOUT)

            harness.remote.cmd_start.set(settingsToApply="default.yaml")
            await harness.remote.cmd_start.start(timeout=STD_TIMEOUT)
            self.assertEqual(harness.csc.summary_state, salobj.State.DISABLED)
            state = await harness.remote.evt_summaryState.next(flush=False, timeout=STD_TIMEOUT)
            self.assertEqual(state.summaryState, salobj.State.DISABLED)
            settings = await harness.remote.evt_settingsApplied.next(flush=False, timeout=STD_TIMEOUT)
            self.assertEqual(settings.algorithmName, "simple")
            self.assertEqual(yaml.safe_load(settings.algorithmConfig), dict(max_daz=5))

        asyncio.get_event_loop().run_until_complete(doit())

    async def assert_dome_az(self, harness, expected_az):
        """Check the ATDome and ATDomeController commanded azimuth.
        """
        dome_position = await harness.dome_remote.tel_position.next(flush=False, timeout=STD_TIMEOUT)
        ATDomeTrajectory.assert_angles_almost_equal(dome_position.azimuthPositionSet, expected_az)
        # wait for the second telemetry in order to make sure
        # ATDomeTrajectory has time to process the first one
        dome_position = await harness.dome_remote.tel_position.next(flush=False, timeout=STD_TIMEOUT)
        ATDomeTrajectory.assert_angles_almost_equal(dome_position.azimuthPositionSet, expected_az)
        ATDomeTrajectory.assert_angles_almost_equal(harness.csc.dome_cmd_az, expected_az)

    def assert_telescope_azalt(self, harness, expected_az, expected_alt):
        ATDomeTrajectory.assert_angles_almost_equal(harness.csc.target_azalt.az, expected_az)
        ATDomeTrajectory.assert_angles_almost_equal(harness.csc.target_azalt.alt, expected_alt)

    async def check_move(self, harness, az_deg, alt_deg):
        """Set telescope target azimuth and check that the dome goes there.

        Then check that the dome does not move for small changes
        to the telescope target about that point.

        Parameters
        ----------
        az_deg : `float`
            Desired azimuth for telescope and dome (deg)
        alt_deg : `float`
            Desired altitude for telescope (deg)

        Raises
        ------
        ValueError :
            If the change in dome azimuth <= configured max dome azimuth error
            (since that will result in no dome motion, which will mess up
            the test).
        """
        max_daz_deg = harness.csc.algorithm.max_daz.deg
        daz_dome_deg = az_deg - harness.dome_csc.cmd_az.deg
        if abs(daz_dome_deg) <= max_daz_deg:
            raise ValueError(f"daz_dome_deg={daz_dome_deg} must be > max_daz_deg={max_daz_deg}")

        self.set_target_azalt(harness, az_deg, alt_deg)
        await self.assert_dome_az(harness, az_deg)
        self.assert_telescope_azalt(harness, az_deg, alt_deg)
        await self.check_null_moves(harness, alt_deg)

    async def check_null_moves(self, harness, alt_deg):
        az_deg = harness.dome_csc.cmd_az.deg
        max_daz_deg = harness.csc.algorithm.max_daz.deg
        no_move_daz_deg = max_daz_deg - 0.0001
        for target_az_deg in (az_deg - no_move_daz_deg, az_deg + no_move_daz_deg, az_deg):
            self.set_target_azalt(harness, target_az_deg, alt_deg)
            await self.assert_dome_az(harness, az_deg)
            self.assert_telescope_azalt(harness, target_az_deg, alt_deg)

    def set_target_azalt(self, harness, az_deg, alt_deg):
        harness.atmcs_controller.evt_target.set_put(elevation=alt_deg, azimuth=az_deg, force_output=True)


if __name__ == "__main__":
    unittest.main()
