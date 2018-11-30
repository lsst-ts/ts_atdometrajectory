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
import contextlib
import unittest
from lsst.ts import salobj
from lsst.ts.salobj.base import AckError
from lsst.ts.ATDomeTrajectory.ATDomeTrajectoryCSC import ATDomeTrajectoryCsc as theCsc
import SALPY_ATDomeTrajectory
import SALPY_ATDome
from random import randint

@contextlib.contextmanager
def assertRaisesAckError(ack=None, error=None):
    """Assert that code raises a salobj.AckError
    Parameters
    ----------
    ack : `int` (optional)
        Ack code, typically a SAL__CMD_<x> constant.
        If None then the ack code is not checked.
    error : `int`
        Error code. If None then the error value is not checked.
    """
    try:
        yield
        raise AssertionError("AckError not raised")
    except AckError as e:
        if ack is not None and e.ack.ack != ack:
            raise AssertionError(f"ack.ack={e.ack.ack} instead of {ack}")
        if error is not None and e.ack.error != error:
            raise AssertionError(f"ack.error={e.ack.error} instead of {error}")


class Harness:

    index = 0

    def __init__(self, initial_state):
        self.csc = theCsc(self.index, initial_state=initial_state)
        self.remote = salobj.Remote(SALPY_ATDomeTrajectory, self.index)
        self.atdome_controller = salobj.Controller(SALPY_ATDome, self.index)

class CommunicateTestCase(unittest.TestCase):
    @unittest.skip('reason')
    def test_heartbeat(self):
        """Wait for 2 hearbeat and validate timing
        """

        async def doit():
            harness = Harness(initial_state=salobj.State.ENABLED)
            start_time = time.time()
            await harness.remote.evt_heartbeat.next(timeout=2)
            await harness.remote.evt_heartbeat.next(timeout=2)
            duration = time.time() - start_time
            self.assertLess(abs(duration - 2), 1.5)  # not clear what this limit should be
        asyncio.get_event_loop().run_until_complete(doit())

    @unittest.skip('reason')
    def test_main(self):
        async def doit():
            """Test if the CSC executable runs
            """
            process = await asyncio.create_subprocess_exec("runATDomeTrajectoryCSC.py", str(self.index))
            try:
                remote = salobj.Remote(self.cscName, self.index)
                summaryState_data = await remote.evt_summaryState.next(flush=False, timeout=10)
                self.assertEqual(summaryState_data.summaryState, salobj.State.STANDBY)

                id_ack = await remote.cmd_exitControl.start(remote.cmd_exitControl.DataType(), timeout=2)
                self.assertEqual(id_ack.ack.ack, remote.salinfo.lib.SAL__CMD_COMPLETE)
                summaryState_data = await remote.evt_summaryState.next(flush=False, timeout=10)
                self.assertEqual(summaryState_data.summaryState, salobj.State.OFFLINE)

                await asyncio.wait_for(process.wait(), 2)
            except Exception:
                if process.returncode is None:
                    process.terminate()
                raise

        asyncio.get_event_loop().run_until_complete(doit())

    @unittest.skip('reason')
    def test_standard_state_transitions(self):
        """Test standard CSC state transitions.
        """
        async def doit():
            harness = Harness(initial_state=salobj.State.STANDBY)
            commands = ("start", "enable", "disable", "exitControl", "standby")
            self.assertEqual(harness.csc.summary_state, salobj.State.STANDBY)

            for bad_command in commands:
                if bad_command in ("start", "exitControl"):
                    continue  # valid command in STANDBY state
                with self.subTest(bad_command=bad_command):
                    cmd_attr = getattr(harness.remote, f"cmd_{bad_command}")
                    with assertRaisesAckError(
                            ack=harness.remote.salinfo.lib.SAL__CMD_FAILED):
                        await cmd_attr.start(cmd_attr.DataType())

            # send start; new state is DISABLED
            cmd_attr = getattr(harness.remote, f"cmd_start")
            state_coro = harness.remote.evt_summaryState.next(flush=True, timeout=10)
            id_ack = await cmd_attr.start(cmd_attr.DataType())
            state = await state_coro
            self.assertEqual(id_ack.ack.ack, harness.remote.salinfo.lib.SAL__CMD_COMPLETE)
            self.assertEqual(id_ack.ack.error, 0)
            self.assertEqual(harness.csc.summary_state, salobj.State.DISABLED)
            self.assertEqual(state.summaryState, salobj.State.DISABLED)

            for bad_command in commands:
                if bad_command in ("standby", "enable"):
                    continue  # valid command in DISABLED state
                with self.subTest(bad_command=bad_command):
                    cmd_attr = getattr(harness.remote, f"cmd_{bad_command}")
                    with assertRaisesAckError(
                            ack=harness.remote.salinfo.lib.SAL__CMD_FAILED):
                        await cmd_attr.start(cmd_attr.DataType())

            # send enable; new state is ENABLED
            cmd_attr = getattr(harness.remote, f"cmd_enable")
            state_coro = harness.remote.evt_summaryState.next(flush=False, timeout=10)
            id_ack = await cmd_attr.start(cmd_attr.DataType(), timeout=10)
            state = await state_coro
            self.assertEqual(id_ack.ack.ack, harness.remote.salinfo.lib.SAL__CMD_COMPLETE)
            self.assertEqual(id_ack.ack.error, 0)
            self.assertEqual(harness.csc.summary_state, salobj.State.ENABLED)
            self.assertEqual(state.summaryState, salobj.State.ENABLED)

            for bad_command in commands:
                if bad_command in ("disable"):
                    continue  # valid command in DISABLED state
                with self.subTest(bad_command=bad_command):
                    cmd_attr = getattr(harness.remote, f"cmd_{bad_command}")
                    with assertRaisesAckError(
                            ack=harness.remote.salinfo.lib.SAL__CMD_FAILED):
                        await cmd_attr.start(cmd_attr.DataType())

            # send disable; new state is DISABLED
            cmd_attr = getattr(harness.remote, f"cmd_disable")
            state_coro = harness.remote.evt_summaryState.next(flush=False, timeout=10)
            # this CMD may take some time to complete
            id_ack = await cmd_attr.start(cmd_attr.DataType(), timeout=30.)
            self.assertEqual(id_ack.ack.ack, harness.remote.salinfo.lib.SAL__CMD_COMPLETE)
            self.assertEqual(id_ack.ack.error, 0)
            self.assertEqual(harness.csc.summary_state, salobj.State.DISABLED)

            # send standby; new state is STANDBY
            cmd_attr = getattr(harness.remote, f"cmd_standby")
            state_coro = harness.remote.evt_summaryState.next(flush=False, timeout=10)
            id_ack = await cmd_attr.start(cmd_attr.DataType())
            state = await state_coro
            self.assertEqual(id_ack.ack.ack, harness.remote.salinfo.lib.SAL__CMD_COMPLETE)
            self.assertEqual(id_ack.ack.error, 0)
            self.assertEqual(harness.csc.summary_state, salobj.State.STANDBY)

            # send exitControl; new state is OFFLINE
            cmd_attr = getattr(harness.remote, f"cmd_exitControl")
            state_coro = harness.remote.evt_summaryState.next(flush=False, timeout=10)
            id_ack = await cmd_attr.start(cmd_attr.DataType())
            state = await state_coro
            self.assertEqual(id_ack.ack.ack, harness.remote.salinfo.lib.SAL__CMD_COMPLETE)
            self.assertEqual(id_ack.ack.error, 0)
            self.assertEqual(harness.csc.summary_state, salobj.State.OFFLINE)

            await asyncio.wait_for(harness.csc.done_task, 2)

        asyncio.get_event_loop().run_until_complete(doit())

    def test_commands_to_atdome(self):
        """Test commands to ATDome. Firs it goes to enable and then command ATDome when applies
        """
        async def doit():
            harness = Harness(initial_state=salobj.State.STANDBY)
            commands = ("start", "enable", "disable", "exitControl", "standby")
            self.assertEqual(harness.csc.summary_state, salobj.State.STANDBY)

            # send start; new state is DISABLED
            cmd_attr = getattr(harness.remote, f"cmd_start")
            state_coro = harness.remote.evt_summaryState.next(flush=True, timeout=10)
            id_ack = await cmd_attr.start(cmd_attr.DataType())
            state = await state_coro
            self.assertEqual(id_ack.ack.ack, harness.remote.salinfo.lib.SAL__CMD_COMPLETE)
            self.assertEqual(id_ack.ack.error, 0)
            self.assertEqual(harness.csc.summary_state, salobj.State.DISABLED)
            self.assertEqual(state.summaryState, salobj.State.DISABLED)

            # send enable; new state is ENABLED
            cmd_attr = getattr(harness.remote, f"cmd_enable")
            state_coro = harness.remote.evt_summaryState.next(flush=False, timeout=10)
            id_ack = await cmd_attr.start(cmd_attr.DataType(), timeout=10)
            state = await state_coro
            self.assertEqual(id_ack.ack.ack, harness.remote.salinfo.lib.SAL__CMD_COMPLETE)
            self.assertEqual(id_ack.ack.error, 0)
            self.assertEqual(harness.csc.summary_state, salobj.State.ENABLED)
            self.assertEqual(state.summaryState, salobj.State.ENABLED)

            atDomeData = harness.atdome_controller.tel_position.DataType()
            setattr(atDomeData, f"dropoutOpeningPercentage",100)
            setattr(atDomeData, f"mainDoorOpeningPercentage",100)
            setattr(atDomeData, f"azimuthPosition",randint(-270, 270))
            setattr(atDomeData, f"dropoutOpeningPercentageSet",100)
            setattr(atDomeData, f"mainDoorOpeningPercentageSet",100)
            setattr(atDomeData, f"azimuthPositionSet",randint(-270, 270))
        
            harness.atdome_controller.tel_position.put(atDomeData)

            # Validate if command is sent
            command = await asyncio.wait_for(harness.atdome_controller.cmd_moveAzimuth.next(), timeout=1)
            print(command.data.azimuth)
            
            await asyncio.sleep(5)

            setattr(atDomeData, f"dropoutOpeningPercentage",100)
            setattr(atDomeData, f"mainDoorOpeningPercentage",100)
            setattr(atDomeData, f"azimuthPosition",randint(-270, 270))
            setattr(atDomeData, f"dropoutOpeningPercentageSet",100)
            setattr(atDomeData, f"mainDoorOpeningPercentageSet",100)
            setattr(atDomeData, f"azimuthPositionSet",randint(-270, 270))
        
            harness.atdome_controller.tel_position.put(atDomeData)
            
            # Validate if command is sent
            command = await asyncio.wait_for(harness.atdome_controller.cmd_moveAzimuth.next(), timeout=1)
            print(command.data.azimuth)

            # send start; new state is DISABLED
            cmd_attr = getattr(harness.remote, f"cmd_disable")
            state_coro = harness.remote.evt_summaryState.next(flush=False, timeout=10)
            # this CMD may take some time to complete
            id_ack = await cmd_attr.start(cmd_attr.DataType(), timeout=30.)
            state = await state_coro
            self.assertEqual(id_ack.ack.ack, harness.remote.salinfo.lib.SAL__CMD_COMPLETE)
            self.assertEqual(id_ack.ack.error, 0)
            self.assertEqual(harness.csc.summary_state, salobj.State.DISABLED)

            # send standby; new state is STANDBY
            cmd_attr = getattr(harness.remote, f"cmd_standby")
            state_coro = harness.remote.evt_summaryState.next(flush=False, timeout=10)
            id_ack = await cmd_attr.start(cmd_attr.DataType())
            state = await state_coro
            self.assertEqual(id_ack.ack.ack, harness.remote.salinfo.lib.SAL__CMD_COMPLETE)
            self.assertEqual(id_ack.ack.error, 0)
            self.assertEqual(harness.csc.summary_state, salobj.State.STANDBY)

            # send exitControl; new state is OFFLINE
            cmd_attr = getattr(harness.remote, f"cmd_exitControl")
            state_coro = harness.remote.evt_summaryState.next(flush=False, timeout=10)
            id_ack = await cmd_attr.start(cmd_attr.DataType())
            state = await state_coro
            self.assertEqual(id_ack.ack.ack, harness.remote.salinfo.lib.SAL__CMD_COMPLETE)
            self.assertEqual(id_ack.ack.error, 0)
            self.assertEqual(harness.csc.summary_state, salobj.State.OFFLINE)

            await asyncio.wait_for(harness.csc.done_task, 2)

        asyncio.get_event_loop().run_until_complete(doit())

if __name__ == "__main__":
    unittest.main()
