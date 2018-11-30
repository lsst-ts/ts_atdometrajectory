from abc import ABC, abstractmethod
import SALPY_ATDome
import lsst.ts.salobj as salobj
from lsst.ts.ATDomeTrajectory.ATDomeTrajectoryUtils \
    import ATDomeTrajectoryConfiguration, ATDomePosition, ATMountTarget


class IATDomeTrajectoryAlgorithm(ABC):
    """Abstract class to handle different algorithms but following the same interface.
    ----------

    Notes
    -----"""
    @abstractmethod
    def followTarget(self, position: ATDomePosition, mtTarget: ATMountTarget,
                     configuration: ATDomeTrajectoryConfiguration):
        pass


class AlgorithmA(IATDomeTrajectoryAlgorithm):
    def __init__(self):
        self.ATDomeRemote = salobj.Remote(SALPY_ATDome, 0)

    async def followTarget(self, position: ATDomePosition, mtTarget: ATMountTarget,
                           configuration: ATDomeTrajectoryConfiguration):
        """Simple algorithm to follow the target position from the pointing kernel

        Arguments:
            position {ATDomePosition} -- Last position value obtained from ATDome
            mtTarget {ATMountTarget} -- Last target obtained from the pointing
            configuration {ATDomeTrajectoryConfiguration} -- Configuration obtained from a configuration file
        """
        if((not mtTarget.isNewValue()) or (not position.isNewValue())):
            return
        target = mtTarget.getLastValue()
        position = position.getLastValue()

        if(abs(target.azimuthAngleTarget - position.azimuthAngle) < configuration.minDifTomove):
            return
        azimuth = BestPositionCalculator().calculateBestPosition(target, position)
        moveAzimuthTopic = self.ATDomeRemote.cmd_moveAzimuth.DataType()
        moveAzimuthTopic.azimuth = azimuth
        await self.ATDomeRemote.cmd_moveAzimuth.start(moveAzimuthTopic, timeout=0.5)  # Move to position
        return


class BestPositionCalculator:
    def calculateBestPosition(self, target, currentPosition):
        """Calculate the best azimuth position for the ATDome.
        It should consider the vigneting and direction of that angle

        Arguments:
            target {ATMountTarget} -- Targeted position
            currentPosition {ATDomePosition} -- Last position obtained from the ATDome

        Returns:
            double -- Best azimuth angle to go to
        """

        target = target.getLastValue()
        return target.azimuthAngleTarget
