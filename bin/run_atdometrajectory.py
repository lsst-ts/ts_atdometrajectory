#!/usr/bin/env python
import asyncio

from lsst.ts import ATDomeTrajectory

asyncio.run(ATDomeTrajectory.ATDomeTrajectory.amain(index=None))
