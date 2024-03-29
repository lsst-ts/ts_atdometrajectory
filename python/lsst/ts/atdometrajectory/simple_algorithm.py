# This file is part of ts_ATDomeTrajectory.
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

__all__ = ["SimpleAlgorithm"]

import math

from lsst.ts import salobj, utils

from . import base_algorithm

RAD_PER_DEG = math.pi / 180


class SimpleAlgorithm(base_algorithm.BaseAlgorithm):
    """Simple algorithm to follow the target position from the pointing kernel.

    If the difference between the telescope target and dome target
    azimuth position is larger than the configured maximum, then command
    dome azimuth position = telescope_target azimuth position.
    Otherwise don't move the dome.
    """

    def desired_dome_azimuth(
        self, dome_target_azimuth, telescope_target, next_telescope_target=None
    ):
        """Return a new target dome azimuth if dome movement is needed
        to avoid vignetting, else None.

        Parameters
        ----------
        dome_target_azimuth : `float` or `None`
            Dome target azimuth (deg), or `None` if unknown.
        telescope_target : `ElevationAzimuth`
            Telescope target elevation and azimuth.
        next_telescope_target : `ElevationAzimuth` or `None`, optional
            Next telescope_target target elevation and azimuth, if known,
            else `None`. Ignored.

        Returns
        -------
        dome_target_azimuth : `float` or `None`
            New desired dome azimuth (deg), or `None` if no change.
        """
        if dome_target_azimuth is None:
            return telescope_target.azimuth.position

        # scaled_delta_azimuth is the difference multiplied by cos(target alt).
        scaled_delta_azimuth = utils.angle_diff(
            telescope_target.azimuth.position, dome_target_azimuth
        ).deg * math.cos(telescope_target.elevation.position * RAD_PER_DEG)
        if abs(scaled_delta_azimuth) < self.max_delta_azimuth:
            return None
        return telescope_target.azimuth.position

    def configure(self, *, max_delta_azimuth=5):
        """Configure the algorithm.

        Parameters
        ----------
        max_delta_azimuth : `float`
            Maximum allowed difference between dome commanded azimuth
            and telescope_target target azimuth.
        """
        if max_delta_azimuth < 0:
            raise salobj.ExpectedError(
                f"max_delta_azimuth={max_delta_azimuth} must not be negative"
            )
        self.max_delta_azimuth = max_delta_azimuth


base_algorithm.AlgorithmRegistry["simple"] = SimpleAlgorithm
