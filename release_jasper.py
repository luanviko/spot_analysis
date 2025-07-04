from dataclasses import dataclass, field
from typing import List, Any, Optional, Union, Tuple
from pathlib import Path
import sqlite3, json, os
from utils import Jasper 
from time import sleep
import signal, sys

def go_inside(sig, frame):
    print("\nJasper stopped fetching.")
    sys.exit(0)

def main():

    good_boy = Jasper('./photos.sqlite')

    # If SIGINT or SIGTERM, Jasper will stop fetching
    signal.signal(signal.SIGINT,  good_boy.go_inside )
    signal.signal(signal.SIGTERM, good_boy.go_inside )
    
    while True:
        good_boy.check_folder()
        sleep(5)


if __name__ == '__main__':
    main()