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

import unittest

from astropy.coordinates import Angle
import astropy.units as u

from lsst.ts.ATDomeTrajectory import angle_diff, assert_angles_almost_equal


class UtilsTestCase(unittest.TestCase):
    def test_angle_diff(self):
        for angle1, angle2, expected_diff in (
            (5.15, 0, 5.15),
            (5.21, 359.20, 6.01),
            (270, -90, 0),
        ):
            with self.subTest(angle1=angle1, angle2=angle2, expected_diff=expected_diff):
                diff = angle_diff(angle1, angle2)
                self.assertAlmostEqual(diff.deg, expected_diff)
                diff = angle_diff(angle2, angle1)
                self.assertAlmostEqual(diff.deg, -expected_diff)
                diff = angle_diff(Angle(angle1, u.deg), angle2)
                self.assertAlmostEqual(diff.deg, expected_diff)
                diff = angle_diff(angle1, Angle(angle2, u.deg))
                self.assertAlmostEqual(diff.deg, expected_diff)
                diff = angle_diff(Angle(angle1, u.deg), Angle(angle2, u.deg))
                self.assertAlmostEqual(diff.deg, expected_diff)

    def test_assert_angles_almost_equal(self):
        for angle1, angle2 in (
            (5.15, 5.14),
            (-0.20, 359.81),
            (270, -90.1),
        ):
            epsilon = Angle(1e-15, u.deg)
            with self.subTest(angle1=angle1, angle2=angle2):
                diff = abs(angle_diff(angle1, angle2))
                bad_diff = diff - epsilon
                self.assertGreater(bad_diff.deg, 0)
                with self.assertRaises(AssertionError):
                    assert_angles_almost_equal(angle1, angle2, bad_diff)
                with self.assertRaises(AssertionError):
                    assert_angles_almost_equal(angle1, angle2, bad_diff.deg)
                with self.assertRaises(AssertionError):
                    assert_angles_almost_equal(angle2, angle1, bad_diff)
                with self.assertRaises(AssertionError):
                    assert_angles_almost_equal(Angle(angle1, u.deg), angle2, bad_diff)
                with self.assertRaises(AssertionError):
                    assert_angles_almost_equal(angle1, Angle(angle2, u.deg), bad_diff)
                with self.assertRaises(AssertionError):
                    assert_angles_almost_equal(Angle(angle1, u.deg), Angle(angle2, u.deg), bad_diff)

                good_diff = diff + epsilon
                assert_angles_almost_equal(angle1, angle2, good_diff)
                assert_angles_almost_equal(angle1, angle2, good_diff.deg)
                assert_angles_almost_equal(angle2, angle1, good_diff)
                assert_angles_almost_equal(Angle(angle1, u.deg), angle2, good_diff)
                assert_angles_almost_equal(angle1, Angle(angle2, u.deg), good_diff)
                assert_angles_almost_equal(Angle(angle1, u.deg), Angle(angle2, u.deg), good_diff)


if __name__ == "__main__":
    unittest.main()
