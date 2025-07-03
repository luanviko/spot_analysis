from dataclasses import dataclass, field
from typing import List, Any, Optional, Union, Tuple
from pathlib import Path
import sqlite3, json, os
from utils import Database

def main():

    db = Database('./photos.sqlite')
    db.setup_database()

    query_results = db.cursor("SELECT * FROM photos", fetch='all')
    print(query_results)

    query_results = db.cursor("SELECT name FROM sqlite_master WHERE type='table';", fetch='all')
    print(query_results)

    json_path = '/home/lkoerich/Dropbox/Work/LED_FEB/Camera and Database/camera_control/data/photos/Run-9998_2025-06-24-T161125.json'
    sql_return = db.add_photo(os.path.abspath(json_path))

    json_path = '/home/lkoerich/Dropbox/Work/LED_FEB/Camera and Database/camera_control/data/run_info/run_info_9998.json'
    sql_return = db.add_run(os.path.abspath(json_path))

    rows = db.fetch_table('photos')
    print(rows)

    rows = db.fetch_table('runs')
    print(rows)
    

    # TODO: - Find all data_paths from all runs. Look for photos from all runs' paths.
    # TODO: - Find a photo's path and analyze it.



if __name__ == '__main__':
    main()