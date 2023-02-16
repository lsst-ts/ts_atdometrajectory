# This file is part of ts_atdometrajectory.
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

import pathlib
import unittest

import jsonschema
import pytest
import yaml
from lsst.ts import atdometrajectory, salobj

TEST_CONFIG_DIR = pathlib.Path(__file__).parent / "data" / "config"


class ValidationTestCase(unittest.TestCase):
    """Test validation of the config schema."""

    def setUp(self):
        self.schema = atdometrajectory.CONFIG_SCHEMA
        self.validator = salobj.StandardValidator(schema=self.schema)
        with open(TEST_CONFIG_DIR / "_init.yaml", "r") as f:
            raw_config = f.read()
        self.init_config = yaml.safe_load(raw_config)
        self.validator.validate(self.init_config)

    def test_good_files(self):
        config = self.init_config.copy()
        assert config["algorithm_name"] == "simple"
        assert config["simple"] == dict(max_delta_azimuth=5)
        assert config["azimuth_vignette_min"] == 10.1
        assert config["azimuth_vignette_max"] == 25.1
        assert config["dropout_door_vignette_min"] == 27.1
        assert config["dropout_door_vignette_max"] == 15.1
        assert config["dome_inner_radius"] == 5000
        assert config["telescope_height_offset"] == 1000

        with open(TEST_CONFIG_DIR / "valid.yaml", "r") as f:
            raw_config = f.read()
        config.update(yaml.safe_load(raw_config))
        self.validator.validate(config)
        assert config["algorithm_name"] == "simple"
        assert config["simple"] == dict(max_delta_azimuth=7.1)
        assert config["azimuth_vignette_min"] == 11.2
        assert config["azimuth_vignette_max"] == 26.2
        assert config["dropout_door_vignette_min"] == 28.2
        assert config["dropout_door_vignette_max"] == 16.2
        assert config["dome_inner_radius"] == 5050.5
        assert config["telescope_height_offset"] == 1010.1

    def test_bad_files(self):
        for path in TEST_CONFIG_DIR.glob("invalid*.yaml"):
            with self.subTest(path=path):
                config = self.init_config.copy()
                with open(path, "r") as f:
                    raw_config = f.read()
                bad_config = yaml.safe_load(raw_config)
                if path.name == "invalid_malformed.yaml":
                    assert not isinstance(bad_config, dict)
                else:
                    # File is valid but the config is not
                    config.update(bad_config)
                    with pytest.raises(jsonschema.exceptions.ValidationError):
                        self.validator.validate(config)

    def test_missing_fields(self):
        for field in self.init_config:
            with self.subTest(field=field):
                bad_config = self.init_config.copy()
                del bad_config[field]
                with pytest.raises(jsonschema.exceptions.ValidationError):
                    self.validator.validate(bad_config)


if __name__ == "__main__":
    unittest.main()
