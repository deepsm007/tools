#! /usr/bin/python3

import sys
import logging

from rh_gitleaks.gl_account import main

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)
sys.exit(main())
