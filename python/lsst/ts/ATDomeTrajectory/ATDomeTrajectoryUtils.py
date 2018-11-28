import time
from random import randint

class ATDomeTrajectoryConfiguration:
    self.algorithmFrequency = 0.5
    self.minDifTomove = 5    #Minimum dist
    self.updateFrequency = 0.5

    def updateConfiguration(settingsToApply: str):
        """Update settings according to settingsToApply
        Parameters
        ----------
        settingsToApply : settingToApply at the start command
        """
        pass

class ATDomePosition:
    def __init__():
        self.azimuthAngle = 0
        self.newValue = False

    def update(azimuthAngle=None):
        """Update current position and set newValue to True
        Parameters
        ----------
        azimuthAngle : New Azimuth target position
        """
        self.azimuthAngle = azimuthAngle if azimuthAngle is not None else self.azimuthAngle
        self.newValue = True

    def getLastValue():
        """Get last value and set lastValue to False
        Returns
        ----------
        lastValue : Return last value updated
        """
        lastValue = self
        self.newValue = False
        return lastValue

    def newValue():
        """Check if there's a new value since last getLastValue
        Returns
        ----------
        newValue : True if position has been updated since last getLastValue else False
        """
        return self.newValue

class ATMountTarget:

    def __init__():
        self.azimuthAngleTarget = 0
        self.elevationAngleTarget = 0
        self.newValue = False

    def update(azimuthAngleTarget=None, elevationAngleTarget=None):
        """Update current position and set newValue to True
        Parameters
        ----------
        azimuthAngleTarget : New Azimuth target position
        elevationAngleTarget : New Elevation target position
        
        """
        self.azimuthAngleTarget = azimuthAngleTarget if azimuthAngleTarget is not None else self.azimuthAngleTarget
        self.elevationAngleTarget = elevationAngleTarget if azimuthAngleTarget is not None else self.elevationAngleTarget
        self.newValue = True

    def getLastValue():
        """Get last value and set lastValue to False
        Returns
        ----------
        lastValue : Return last value updated
        """
        lastValue = self
        self.newValue = False
        return lastValue

    def newValue():
        """Check if there's a new value since last getLastValue
        Returns
        ----------
        newValue : True if position has been updated since last getLastValue else False
        """
        return self.newValue

class simulatePointingCommand:
    def __init__():
        self.time = time.time()
        self.azimuth = 0
        self.elevation = 0
        self.timeToCommand = 10
        self.delta = 0.001

    def getData():
        timePassed = self.time - time.time()
        if(timePassed > self.timeToCommand):
            self.time = time.time()
            self.azimuth = randint(-270, 270)
            self.elevation = randint(20, 88)
        else:
            self.azimuth += self.delta
            self.elevation += self.delta

        return self.azimuth, self.elevation

