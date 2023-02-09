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
import time
import unittest

import pytest

from lsst.ts import atdometrajectory
from lsst.ts import salobj
from lsst.ts import utils
from lsst.ts.idl.enums.ATDome import AzimuthCommandedState, ShutterDoorState

STD_TIMEOUT = 5  # standard command timeout (sec)


class MockDomeTestCase(salobj.BaseCscTestCase, unittest.IsolatedAsyncioTestCase):
    def basic_make_csc(self, initial_state, config_dir, simulation_mode):
        return atdometrajectory.MockDome(initial_state=initial_state)

    async def test_move_azimuth(self):
        """Test issuing moveAzimuth commands to ATDome."""
        async with self.make_csc(initial_state=salobj.State.ENABLED):
            await self.assert_next_summary_state(salobj.State.ENABLED)

            await self.assert_next_sample(
                topic=self.remote.evt_azimuthCommandedState,
                commandedState=AzimuthCommandedState.UNKNOWN,
            )
            await self.assert_next_sample(
                topic=self.remote.evt_dropoutDoorState, state=ShutterDoorState.OPENED
            )
            await self.assert_next_sample(
                topic=self.remote.evt_mainDoorState, state=ShutterDoorState.OPENED
            )

            position = await self.remote.tel_position.next(
                flush=True, timeout=STD_TIMEOUT
            )
            utils.assert_angles_almost_equal(position.azimuthPosition, 0)

            for az in (3, -1):
                predicted_duration = (
                    abs(az - position.azimuthPosition) / self.csc.az_vel
                )
                start_time = time.time()
                # be conservative about the end time
                predicted_end_time = start_time + predicted_duration
                safe_done_end_time = (
                    predicted_end_time + self.csc.telemetry_interval * 2
                )
                await self.remote.cmd_moveAzimuth.set_start(
                    azimuth=az, timeout=STD_TIMEOUT
                )

                az_cmd_state = await self.assert_next_sample(
                    self.remote.evt_azimuthCommandedState,
                    commandedState=AzimuthCommandedState.GOTOPOSITION,
                )
                utils.assert_angles_almost_equal(az_cmd_state.azimuth, az)

                isfirst = True
                while True:
                    position = await self.remote.tel_position.next(
                        flush=True, timeout=STD_TIMEOUT
                    )
                    if isfirst:
                        isfirst = False
                        with pytest.raises(AssertionError):
                            utils.assert_angles_almost_equal(
                                position.azimuthPosition, az
                            )
                    elif time.time() > safe_done_end_time:
                        utils.assert_angles_almost_equal(position.azimuthPosition, az)
                        break
                    await asyncio.sleep(self.csc.telemetry_interval)


if __name__ == "__main__":
    unittest.main()
