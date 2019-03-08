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
import time
import unittest

from lsst.ts import salobj
from lsst.ts import ATDomeTrajectory
import SALPY_ATDome


class Harness:
    def __init__(self, initial_state):
        self.dome_index = 1  # match ts_ATDome
        self.csc = ATDomeTrajectory.FakeATDome(index=self.dome_index, initial_state=salobj.State.ENABLED)
        self.remote = salobj.Remote(SALPY_ATDome, index=self.dome_index)


class FakeDomeTestCase(unittest.TestCase):
    def setUp(self):
        salobj.test_utils.set_random_lsst_dds_domain()

    def test_move_azimuth(self):
        """Test issuing moveAzimuth commands to ATDomeCsc.
        """
        async def doit():
            harness = Harness(initial_state=salobj.State.ENABLED)
            self.assertEqual(harness.csc.summary_state, salobj.State.ENABLED)
            state = await harness.remote.evt_summaryState.next(flush=False, timeout=5)
            self.assertEqual(state.summaryState, salobj.State.ENABLED)

            position = await harness.remote.tel_position.next(flush=True, timeout=2)
            ATDomeTrajectory.assert_angles_almost_equal(position.azimuthPosition, 0)
            ATDomeTrajectory.assert_angles_almost_equal(position.azimuthPositionSet, 0)

            for az in (3, -1):
                predicted_duration = abs(az - position.azimuthPosition)/harness.csc.az_vel
                start_time = time.time()
                # be conservative about the end time
                predicted_end_time = start_time + predicted_duration
                safe_moving_end_time = predicted_end_time - harness.csc.telemetry_interval
                safe_done_end_time = predicted_end_time + harness.csc.telemetry_interval*2
                harness.remote.cmd_moveAzimuth.set(azimuth=az)
                await harness.remote.cmd_moveAzimuth.start(timeout=2)

                while True:
                    position = await harness.remote.tel_position.next(flush=True, timeout=2)
                    ATDomeTrajectory.assert_angles_almost_equal(position.azimuthPositionSet, az)
                    if time.time() < safe_moving_end_time:
                        with self.assertRaises(AssertionError):
                            ATDomeTrajectory.assert_angles_almost_equal(position.azimuthPosition, az)
                    elif time.time() > safe_done_end_time:
                        ATDomeTrajectory.assert_angles_almost_equal(position.azimuthPosition, az)
                        break
                    await asyncio.sleep(harness.csc.telemetry_interval)

        asyncio.get_event_loop().run_until_complete(doit())


if __name__ == "__main__":
    unittest.main()
