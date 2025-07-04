from dataclasses import dataclass, field
from typing import List, Any, Optional, Union, Tuple
from pathlib import Path
import sqlite3, json, os, sys
from db_manager import Database


class Jasper(Database):
    """
    Jasper is a subclass of Database that automatically monitors photo folders 
    for new `.json` metadata files and updates the database accordingly.
    """

    incoming_folders: Union[str, Path] | None = None
    json_list: List[str] | None = []

    def __post_init__(self):
        """
        Post-initialization to load all incoming folders from the 'runs' table if not provided.
        """
        if self.incoming_folders is None:
            query = "SELECT data_path FROM runs"
            results = self.cursor(query, fetch='all')
            paths = [Path(row[0]) for row in results]
            self.incoming_folders = paths

        print('Looking for new photos and run files at the following directories: ')
        for path in self.incoming_folders:
            print(str(path / 'photos'))
            print(str(path / 'run_info'))

    def check_folder(self, seconds: float = 10.0):
        """
        Scans incoming folders for new `.json` photo files not yet in the database.

        Args:
            seconds (float): Delay interval between checks (currently unused).
        """
        self.present_jsons = set()

        query = 'SELECT photo_directory, photo_arw FROM photos'
        results = self.cursor(query, fetch='all')

        self.present_jsons = {
            str( Path(row[0]) / Path(row[1]).with_suffix('.json') )
            for row in results
        }

        incoming_jsons = {
            path / "photos" / file
            for path in self.incoming_folders
            for file in (path / "photos").glob("*.json")
            if str(file) not in self.present_jsons
        }

        print(incoming_jsons)

        self.present_jsons.update(incoming_jsons)
        self.update_database(incoming_jsons)

    def update_database(self, json_files: set[Path]):
        """
        Inserts new photo or run entries into the database from given JSON files.

        Args:
            json_files (set[Path]): Set of `.json` files detected in the photo folder.
        """
        for json_path in json_files:
            if 'photos' in json_path.parent.name and 'run_info' not in str(json_path.parent):
                self.add_photo(str(json_path))
            elif 'run_info' in str(json_path.parent):
                self.add_run(str(json_path))

    
    def go_inside(self, sig, frame):
        print("\nJasper stopped fetching.")
        sys.exit(0)