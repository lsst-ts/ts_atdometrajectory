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

import lsst.ts.salobj as salobj
from lsst.ts.ATDomeTrajectory.ATDomeTrajectoryUtils \
    import ATDomeTrajectoryConfiguration, ATDomePosition, ATMountTarget, SimulatePointingCommand
from lsst.ts.ATDomeTrajectory.ATDomeTrajectoryAlgorithm import AlgorithmA
import asyncio
import warnings

try:
    import SALPY_ATDomeTrajectory
except ImportError:
    warnings.warn("Could not import SALPY_ATDomeTrajectory; ATDomeTrajectory will not work")

try:
    import SALPY_ATDome
except ImportError:
    warnings.warn("Could not import SALPY_ATDome; ATDome will not work")


class ATDomeTrajectoryCsc(salobj.base_csc.BaseCsc):
    """A skeleton implementation of ATDomeTrajectory
    Supported commands:
    * The standard state transition commands do the usual thing
      and output the ``summaryState`` event. The ``exitControl``
      command shuts the CSC down.
    Parameters
    ----------
    initial_state : `salobj.State` (optional)
        The initial state of the CSC. Typically one of:
        - State.ENABLED if you want the CSC immediately usable.
        - State.STANDBY if you want full emulation of a CSC.
    """
    def __init__(self, index, initial_state=salobj.base_csc.State.STANDBY):
        if initial_state not in salobj.base_csc.State:
            raise ValueError(f"intial_state={initial_state} is not a salobj.State enum")
        super().__init__(SALPY_ATDomeTrajectory, index)
        self.summary_state = salobj.base_csc.State.STANDBY

        self.algorithmFrequency = 0.5
        self.configuration = ATDomeTrajectoryConfiguration()
        self.target = ATMountTarget()
        self.position = ATDomePosition()
        self.ATDomeController = salobj.Controller(SALPY_ATDome, 0)

        self.pointingSimulator = SimulatePointingCommand()

        self.algorithmTask = asyncio.Future()
        self.algorithmTask.set_result(None)
        self.updatePositionTask = asyncio.Future()
        self.updatePositionTask.set_result(None)

        # Setting up the algorithm, this will become an if case with different algorithms
        if(True):
            self.algorithm = AlgorithmA()
        else:
            self.algorithm = AlgorithmA()

        asyncio.ensure_future(self.followTrajectoryLoop())
        asyncio.ensure_future(self.updatePosition())

    def end_disable(self):
        if self.algorithmTask and not self.algorithmTask.done():
            self.algorithmTask.cancel()
        super().end_disable()

    def end_standby(self):
        if self.updatePositionTask and not self.updatePositionTask.done():
            self.updatePositionTask.cancel()
        super().end_standby()

    async def followTrajectoryLoop(self):
        """If in enable, run algorithm to follow target command from the pointing
        """
        while True:
            if(self.summary_state == salobj.base_csc.State.ENABLED):
                self.algorithm.followTarget(self.position, self.target, self.configuration)
            self.algorithmTask = asyncio.ensure_future(asyncio.sleep(self.configuration.algorithmFrequency))
            await self.algorithmTask

    async def updatePosition(self):
        """Update position and target through SAL
        """
        while True:
            if(self.summary_state == (salobj.base_csc.State.STANDBY, salobj.base_csc.State.ENABLED)):
                positionData = self.ATDomeController.tel_position.get()
                if(positionData is not None):
                    self.position.update(azimuthAngle=positionData.azimuthPosition)
                azimuth, elevation = self.pointingSimulator.getData()
                self.target.update(azimuthAngleTarget=azimuth, elevationAngleTarget=elevation)

            self.updatePositionTask = asyncio.ensure_future(asyncio.sleep(self.configuration.updateFrequency))
            await self.updatePositionTask
