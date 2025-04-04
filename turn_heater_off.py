from pyHS100 import SmartPlug
from datetime import datetime, timedelta
import time
import os
import pandas as pd
import argparse
import sys

sys.stdout.reconfigure(line_buffering=True)

# SmartPlug IPs
WP03 = "134.34.225.167"  # Light
WP04 = "134.34.225.135"  # Heater

growLight = SmartPlug(WP03)
heater = SmartPlug(WP04)

heater.turn_off()