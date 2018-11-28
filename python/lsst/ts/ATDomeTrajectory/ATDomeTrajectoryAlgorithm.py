from abc import ABC, abstractmethod
import SALPY_ATDome
from lsst.ts.ATDomeTrajectory.ATDomeTrajectoryUtils import ATDomeTrajectoryConfiguration, ATDomePosition, ATMountTarget

class IATDomeTrajectoryAlgorithm(ABC):
	"""Abstract class to handle different algorithms but following the same interface.
	----------

	Notes
	-----"""
	@abstractmethod
    def followTarget(position: ATDomePosition, mtTarget: ATMountTarget, configuration: ATDomeTrajectoryConfiguration):
        pass


class AlgorithmA(IATDomeTrajectoryAlgorithm):
	def followTarget(position: ATDomePosition, mtTarget: ATMountTarget, configuration: ATDomeTrajectoryConfiguration): 
		pass