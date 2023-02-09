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


__all__ = ["CONFIG_SCHEMA"]

import yaml

CONFIG_SCHEMA = yaml.safe_load(
    """$schema: http://json-schema.org/draft-07/schema#
$id: https://github.com/lsst-ts/ts_atdometrajectory/blob/main/python/lsst/ts/atdometrajectory/config_schema.py
# title must end with one or more spaces followed by the schema version, which must begin with "v"
title: ATDomeTrajectory v3
description: Schema for ATDomeTrajectory configuration files
type: object
properties:
  algorithm_name:
    type: string
    enum:
    - simple
  simple:
    description: Configuration for the "simple" algorithm.
    type: object
    properties:
      max_delta_azimuth:
        type: number
        description: ->
          Maximum difference between dome and telescope azimuth before moving the dome (deg).
          Set to the largest value that reliably avoids vignetting.
    required:
    - max_delta_azimuth
    additionalProperties: false
  azimuth_vignette_min:
    description: >-
      Azimuth angle difference (deg) above which the telescope is partially vignetted
      when the telescope is at elevation 0 (horizon). This is approximately 10°.
    type: number
  azimuth_vignette_max:
    description: >-
      Azimuth angle difference (deg) above which the telescope is fully vignetted
      when the telescope is at elevation 0 (horizon). This is approximately 25°
    type: number
  dropout_door_vignette_min:
    description: >-
      Elevation angle (deg) below which the telescope is partially vignetted
      by the dropout door, if that is closed and the main door is open.
      This is approximately 27°.
    type: number
  dropout_door_vignette_max:
    description: >-
      Elevation angle (deg) below which the telescope is fully vignetted
      by the dropout door, if that is closed and the main door is open.
      This is approximately 12°.
    type: number
  dome_inner_radius:
    description: >-
      Distance (mm) from the center of the telescope (intersection of elevation and azimuth axes)
      to the inner edge of the shutter (with the shutter doors both open).
      This is approximately the inner radius of the dome, which is 4648 mm (183").
      Used to compute vignetting by azimuth mismatch when the telescope elevation is non-zero.
  telescope_height_offset:
    description: >-
      Height (mm) of the center of the telescope (intersection of elevation and azimuth axes)
      above the center of radius of the dome. This is approximately 940 mm (37").
      Used to compute vignetting by azimuth mismatch when the telescope elevation is non-zero.
    type: number
required:
- algorithm_name
- simple
- azimuth_vignette_min
- azimuth_vignette_max
- dropout_door_vignette_min
- dropout_door_vignette_max
- dome_inner_radius
- telescope_height_offset
additionalProperties: false
"""
)
