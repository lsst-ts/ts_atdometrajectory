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

__all__ = ["AlgorithmRegistry", "SimpleAlgorithm"]

import abc
import math

from astropy.coordinates import Angle, AltAz
import astropy.units as u

from lsst.ts import salobj
from . import utils

AlgorithmRegistry = dict()


class BaseAlgorithm(abc.ABC):
    """Abstract class to handle different dome trajectory algorithms.

    Parameters
    ----------
    **kwargs : `dict` of `str`: `value`
        Configuration. For details see the ``configure`` method
        for the algorithm in question.
    """
    def __init__(self, **kwargs):
        self.configure(**kwargs)

    @abc.abstractmethod
    def desired_dome_az(self, dome_az: Angle,
                        target_azalt: AltAz):
        """Compute the desired dome azimuth.

        Parameters
        ----------
        dome_az : `astropy.coordinates.Angle`
            Current dome azimuth.
        target_azalt : `astropy.coordinates.AltAz`
            Telescope target azimuth.

        Returns
        -------
        dome_az : `astropy.coordinates.Angle`
            The desired dome azimuth.
        """
        pass

    @abc.abstractmethod
    def configure(self, **kwargs):
        """Configure the algorithm.
        """
        pass


class SimpleAlgorithm(BaseAlgorithm):
    """Simple algorithm to follow the target position from the pointing kernel.

    If the dome would vignette the telescope at the telescope target position
    then specify dome azimuth = target azimuth. Otherwise don't move the dome.
    """
    def desired_dome_az(self, dome_az: Angle, target_azalt: AltAz):
        """Return a new desired dome azimuth if movement wanted, else None."""
        # Compute scaled_daz: the difference between target and dome azimuth,
        # wrapped to [-180, 180] and multiplied by cos(target alt).
        # If scaled_daz is large enough to vignette then ask the dome
        # to move to the telescope azimuth.
        scaled_daz = utils.angle_diff(target_azalt.az, dome_az)*math.cos(target_azalt.alt.rad)
        if abs(scaled_daz) < self.max_daz:
            return
        return target_azalt.az

    def configure(self, *, max_daz=5):
        """Configure the algorithm.

        Parameters
        ----------
        max_daz : `float`
            Maximum allowed difference between dome commanded azimuth
            and telescope target azimuth.
        """
        if max_daz < 0:
            raise salobj.ExpectedError(f"max_daz={max_daz} must not be negative")
        self.max_daz = Angle(max_daz, u.deg)


AlgorithmRegistry["simple"] = SimpleAlgorithm
