#! /usr/bin/python3

import sys
import logging

from rh_pre_commit import main

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    stream=sys.stdout,
)
sys.exit(main())
