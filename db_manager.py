from dataclasses import dataclass, field
from typing import List, Any, Optional, Union, Tuple
from pathlib import Path
import sqlite3, json, os, sys
from utils import Database

def main():

    db = Database('./photos.sqlite')
    db.setup_database()

    query_results = db.cursor("SELECT photo_arw FROM photos", fetch='all')
    for row in query_results:
        print(row)
    sys.exit()

    # Manually add a run to the 'runs' table
    json_path = '/home/lkoerich/Dropbox/Work/LED_FEB/Camera and Database/camera_control/data/run_info/run_info_9998.json'
    sql_return = db.add_run(os.path.abspath(json_path))
    
    # Manually add a photo to the 'photos' table
    json_path = '/home/lkoerich/Dropbox/Work/LED_FEB/Camera and Database/camera_control/data/photos/Run-9998_2025-06-24-T161125.json'
    sql_return = db.add_photo(os.path.abspath(json_path))

    # Print contents in 'photos' and 'runs' tables
    rows = db.fetch_table('photos')
    print(rows)

    rows = db.fetch_table('runs')
    print(rows)

if __name__ == '__main__':
    main()
