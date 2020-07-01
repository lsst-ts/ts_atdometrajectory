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
import pathlib

# import types  for SimpleNamespace

import jsonschema
import yaml

from lsst.ts import salobj


class ValidationTestCase(unittest.TestCase):
    """Test validation of the config schema."""

    def setUp(self):
        schemaname = "ATDomeTrajectory.yaml"
        schemapath = pathlib.Path(__file__).parents[1].joinpath("schema", schemaname)
        with open(schemapath, "r") as f:
            rawschema = f.read()
        self.schema = yaml.safe_load(rawschema)
        self.validator = salobj.DefaultingValidator(schema=self.schema)

    def test_default(self):
        default_max_daz = 5  # hard-coded in the schema
        result = self.validator.validate(None)
        self.assertEqual(result["algorithm_name"], "simple")
        self.assertEqual(
            result["algorithm_config"], dict(max_delta_azimuth=default_max_daz)
        )

    def test_name_specified(self):
        default_max_daz = 5  # hard-coded in the schema
        data = dict(algorithm_name="simple")
        result = self.validator.validate(data)
        self.assertEqual(result["algorithm_name"], "simple")
        self.assertEqual(
            result["algorithm_config"], dict(max_delta_azimuth=default_max_daz)
        )

    def test_all_specified(self):
        max_delta_azimuth = 3.5
        data = dict(
            algorithm_name="simple",
            algorithm_config=dict(max_delta_azimuth=max_delta_azimuth),
        )
        result = self.validator.validate(data)
        self.assertEqual(result["algorithm_name"], "simple")
        self.assertEqual(
            result["algorithm_config"], dict(max_delta_azimuth=max_delta_azimuth)
        )

    def test_bad_algorithm_name(self):
        data = dict(algorithm_name="invalid_name")
        with self.assertRaises(jsonschema.exceptions.ValidationError):
            self.validator.validate(data)

    def test_bad_algorithm_config(self):
        """The current schema only checks for a dict."""
        data = dict(algorithm_name="simple", algorithm_config=45)
        with self.assertRaises(jsonschema.exceptions.ValidationError):
            self.validator.validate(data)


if __name__ == "__main__":
    unittest.main()
