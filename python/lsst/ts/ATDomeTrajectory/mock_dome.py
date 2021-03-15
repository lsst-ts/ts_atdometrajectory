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

__all__ = ["MockDome"]

import asyncio
import math

from lsst.ts import salobj


class MockDome(salobj.BaseCsc):
    """A very limited fake ATDome CSC

    It receives the ``moveAzimuth`` command and outputs:

    * ``azimuthCommandedState`` event
    * ``position`` telemetry.

    It does not enforce motion limits.

    Parameters
    ----------
    initial_state : `salobj.State` or `int` (optional)
        The initial state of the CSC. This is provided for unit testing,
        as real CSCs should start up in `State.STANDBY`, the default.
    """

    valid_simulation_modes = [0]
    version = "mock"

    def __init__(self, initial_state):
        super().__init__(name="ATDome", index=None, initial_state=initial_state)
        self.curr_az = 0
        self.cmd_az = 0
        self.az_vel = 3  # deg/sec
        self.telemetry_interval = 0.2  # seconds
        self.move_azimuth_task = asyncio.Future()

    async def start(self):
        await super().start()
        self.evt_azimuthCommandedState.set_put(
            commandedState=1, azimuth=math.nan, force_output=True  # 1 = Unknown
        )

    async def close_tasks(self):
        self.move_azimuth_task.cancel()
        await super().close_tasks()

    def do_moveAzimuth(self, data):
        """Support the moveAzimuth command."""
        self.assert_enabled("moveAzimuth")
        self.cmd_az = data.azimuth
        self.evt_azimuthCommandedState.set_put(
            commandedState=2,  # 2 = GoToPosition
            azimuth=data.azimuth,
            force_output=True,
        )

    def report_summary_state(self):
        super().report_summary_state()
        if self.disabled_or_enabled:
            self.move_azimuth_task = asyncio.ensure_future(self.move_azimuth_loop())
        elif not self.move_azimuth_task.done():
            self.move_azimuth_task.cancel()

    async def move_azimuth_loop(self):
        """Move the dome to the specified azimuth."""
        try:
            max_az_corr = abs(self.az_vel * self.telemetry_interval)
            while True:
                if (
                    self.summary_state == salobj.State.ENABLED
                    and self.cmd_az != self.curr_az
                ):
                    az_err = salobj.angle_diff(self.cmd_az, self.curr_az).deg
                    abs_az_corr = min(abs(az_err), max_az_corr)
                    az_corr = abs_az_corr if az_err >= 0 else -abs_az_corr
                    self.curr_az += az_corr
                self.tel_position.set_put(azimuthPosition=self.curr_az)
                await asyncio.sleep(self.telemetry_interval)
        except asyncio.CancelledError:
            raise
        except Exception:
            self.log.exception("move_azimuth_loop failed")
            raise

    def do_moveShutterDropoutDoor(self, data):
        """This command is not supported."""
        raise salobj.ExpectedError("Not implemented")

    def do_closeShutter(self, data):
        """This command is not supported."""
        raise salobj.ExpectedError("Not implemented")

    def do_homeAzimuth(self, data):
        """This command is not supported."""
        raise salobj.ExpectedError("Not implemented")

    def do_stopMotion(self, data):
        """This command is not supported."""
        raise salobj.ExpectedError("Not implemented")

    def do_openShutter(self, data):
        """This command is not supported."""
        raise salobj.ExpectedError("Not implemented")

    def do_moveShutterMainDoor(self, data):
        """This command is not supported."""
        raise salobj.ExpectedError("Not implemented")
