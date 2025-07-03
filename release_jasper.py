from dataclasses import dataclass, field
from typing import List, Any, Optional, Union, Tuple
from pathlib import Path
import sqlite3, json, os
from utils import Jasper 
from time import sleep

def main():

    good_boy = Jasper('./photos.sqlite')

    fetch = True
    while fetch:
        good_boy.check_folder()
        sleep(5)


if __name__ == '__main__':
    main()