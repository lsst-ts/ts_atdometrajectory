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

from lsst.ts.salobj import *
from lsst.ts.ATDomeTrajectory.ATDomeTrajectoryUtils import ATDomeTrajectoryConfiguration, ATDomePosition, ATMountTarget, simulatePointingCommand
from lsst.ts.ATDomeTrajectoryAlgorithm import AlgorithmA
import asyncio
import contextlib
import os
import random
import string
import time
import warnings

import numpy as np

try:
    import SALPY_ATDomeTrajectory
except ImportError:
    warnings.warn("Could not import SALPY_ATDomeTrajectory; ATDomeTrajectory will not work")

try:
    import SALPY_ATDome
except ImportError:
    warnings.warn("Could not import SALPY_ATDome; ATDome will not work")

#import ATHexapodSim
 
class ATDomeTrajectoryCsc(base_csc.BaseCsc):
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
    def __init__(self, index, initial_state=base_csc.State.STANDBY):
        if initial_state not in base_csc.State:
            raise ValueError(f"intial_state={initial_state} is not a salobj.State enum")
        super().__init__(SALPY_ATDomeTrajectory, index)

        self.algorithmFrequency = 0.5
        self.configuration = ATDomeTrajectoryConfiguration()
        self.target = ATMountTarget()
        self.position = ATDomePosition()
        self.ATDome = salobj.Remote(SALPY_ATDome, f'ATDome')
        self.pointingSimulator = simulatePointingCommand()

        self.algorithmTask = asyncio.Future()
        self.algorithmTask.set_result(None)
        self.updatePositionTask = asyncio.Future()
        self.updatePositionTask.set_result(None)

        #Setting up the algorithm, this will become an if case with different algorithms
        if(True):
            self.algorithm = AlgorithmA()
        else
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
        while self.summary_state == base_csc.State.ENABLED:
            self.algorithmTask = asyncio.ensure_future(asyncio.sleep(self.configuration.algorithmFrequency))
            await self.algorithmTask
            self.algorithm.followTarget(ATDomePosition(), ATMountTarget(), self.configuration)

    async def updatePosition(self):    
        """Update position and target through SAL
        """   
        while self.summary_state == (base_csc.State.STANDBY, base_csc.State.ENABLED):

            self.updatePositionTask = asyncio.ensure_future(asyncio.sleep(self.configuration.updateFrequency))
            await self.updatePositionTask

            positionData = self.ATDome.tel_position.get()
            if(positionData is not None):
                self.position.update(azimuthAngle = positionData.azimuthPosition)
            
            azimuth, elevation = self.pointingSimulator.getData()
            self.target.update(azimuthAngleTarget=azimuth, elevationAngleTarget=elevation)