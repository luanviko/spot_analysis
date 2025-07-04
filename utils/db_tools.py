from dataclasses import dataclass, field
from typing import Any, Optional
from pathlib import Path
import sqlite3, json
from time import sleep

@dataclass
class Database:
    """Handles SQLite interactions for storing and retrieving photo/run metadata."""

    path: str
    allowed_tables: list[str] = field(default_factory=lambda: ['photos', 'runs'])

    def __post_init__(self) -> None:
        """Initializes the database structure upon object creation."""
        self.setup_database()

    def cursor(
        self,
        statements: str | list[str],
        fetch: str = '',
        params: Optional[list[Any]] = None
    ) -> list[tuple] | tuple | None:
        """
        Executes SQL statements and optionally returns results.

        Args:
            statements (str | list[str]): A SQL command or a list of commands.
            fetch (str): If 'all' or 'one', retrieves corresponding query results.
            params (list[Any] | None): Parameters for parameterized queries.

        Returns:
            list[tuple] | tuple | None: Fetched rows or row if `fetch` is 'all' or 'one'; otherwise, None.
        """
        conn = sqlite3.connect(self.path)
        cursor = conn.cursor()

        if isinstance(statements, str):
            statements = [statements]

        result: list[tuple] | tuple | None = None
        for statement in statements:
            if params:
                cursor.execute(statement, params)
            else:
                cursor.execute(statement)

            if fetch == 'all':
                result = cursor.fetchall()
            elif fetch == 'one':
                result = cursor.fetchone()

        conn.commit()
        conn.close()

        return result

    def setup_database(self) -> None:
        """
        Creates the 'photos' and 'runs' tables if they do not exist.

        Returns:
            None
        """
        self.cursor('''
            CREATE TABLE IF NOT EXISTS photos (
                run_number       INTEGER,
                led_serial       INTEGER,
                date             TEXT,
                photo_directory, TEXT,
                photo_arw        TEXT PRIMARY KEY,              
                photo_jpg        TEXT,
                channel          INTEGER,           
                distance         REAL,              
                voltage          REAL,              
                iso              INTEGER,
                shutterspeed     REAL,
                best_x0          REAL,
                best_y0          REAL,
                best_R           REAL
            );
        ''')

        self.cursor('''
            CREATE TABLE IF NOT EXISTS runs (
                run_number         INTEGER PRIMARY KEY,
                led_serial         INTEGER,
                date               TEXT,
                data_path          TEXT,
                channels           TEXT,   
                distances          TEXT,  
                photos_per_channel INTEGER,
                prefix             TEXT,
                photos             TEXT    
            );
        ''')

    def fetch_table(self, table_name: str) -> list[tuple[Any, ...]] | None:
        """
        Fetches all rows from a specified allowed table.

        Args:
            table_name (str): The name of the table to query.

        Returns:
            list[tuple] | None: List of rows if table is allowed; otherwise, None.
        """
        if table_name in self.allowed_tables:
            return self.cursor(f"SELECT * FROM {table_name}", fetch='all')
        return None
    
    def load_json(self, json_path: str | Path, time:int = 5, attempts:int = 2):

        retry_number = 0
        while retry_number < attempts:
            
            try:
                with open(json_path, "r") as input_file:
                    data = json.load(input_file)
                return data

            except: 
                print(f"Unable to open json file. Waiting {time} seconds to try again.")
                retry_number += 1
                sleep(time)

        return None                

    def add_photo(self, photo_json: str | Path) -> list[tuple] | None:
        """
        Inserts a photo entry from a JSON file into the 'photos' table.

        Args:
            photo_json (str | Path): Path to the JSON file describing the photo.

        Returns:
            list[tuple] | None: Result of the insert operation.
        """
        photo_json = Path(photo_json)
        data = self.load_json(photo_json)
        
        if data == None:
            Warning(f"Unable to load {photo_json} to database. I will try again later.")
            return

        if photo_json.stat().st_size == 0:
            Warning(f"Unable to load {photo_json} to database. File is empty.")
            return

        with photo_json.open("r") as file_input:
            data = json.load(file_input)

        photo_path = data["photo_path"]
        photo_directory = str(Path(photo_path[0]).parent)
        photo_arw  = str(Path(photo_path[0]).name)
        photo_jpg  = str(Path(photo_path[1]).name)

        statement = """
            INSERT OR IGNORE INTO photos (
                run_number,
                led_serial,
                date,
                photo_directory,
                photo_arw,
                photo_jpg,
                channel,
                distance,
                voltage,
                iso,
                shutterspeed,
                best_x0,
                best_y0,
                best_R
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """

        values: list[Any] = [
            data["run_number"],
            data["led_serial"],
            data["date"],
            photo_directory,
            photo_arw,
            photo_jpg,
            data.get("channel"),
            data.get("distance"),
            data.get("voltage"),
            data["iso"],
            data["shutterspeed"],
            data["best_x0"],
            data["best_y0"],
            data["best_R"]
        ]

        return self.cursor(statement, params=values)

    def add_run(self, json_path: str | Path) -> list[tuple] | None:
        """
        Inserts a run entry from a JSON file into the 'runs' table.

        Args:
            json_path (str | Path): Path to the JSON file describing the run.

        Returns:
            list[tuple] | None: Result of the insert operation.
        """
        json_path = Path(json_path)
        with json_path.open("r") as f:
            data: dict[str, Any] = json.load(f)

        insert_sql = """
            INSERT OR IGNORE INTO runs (
                run_number,
                led_serial,
                date,
                data_path,
                channels,
                distances,
                photos_per_channel,
                prefix,
                photos
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        values: list[Any] = [
            data["run_number"],
            data["led_serial"],
            data["date"],
            data["data_path"],
            json.dumps(data["channels"]),
            json.dumps(data["distances"]),
            data["photos_per_channel"],
            data["prefix"],
            json.dumps(data["photos"])
        ]

        return self.cursor(insert_sql, params=values)

    def fetch_photos(
        self,
        run_number: Optional[str] = None,
        led_serial: Optional[str] = None,
        channel: Optional[str] = None,
        distance: Optional[str] = None
    ) -> list[Path]:
        """
        Retrieves photo JSON paths from the 'photos' table based on optional filters.

        Args:
            run_number (str | None): Filter by run number.
            led_serial (str | None): Filter by LED serial number.
            channel (str | None): Filter by channel.
            distance (str | None): Filter by distance.

        Returns:
            list[Path]: List of Path objects for matching photo JSON files.
        """
        filters: list[str] = []
        params: list[Any] = []
        query = 'SELECT photo_path FROM photos'

        if run_number is not None:
            filters.append('run_number = ?')
            params.append(run_number)
        if led_serial is not None:
            filters.append('led_serial = ?')
            params.append(led_serial)
        if channel is not None:
            filters.append('channel = ?')
            params.append(channel)
        if distance is not None:
            filters.append('distance = ?')
            params.append(distance)

        if filters:
            query += ' WHERE ' + ' AND '.join(filters)

        results = self.cursor(query, params=params, fetch='all') or []

        photo_jsons: list[Path] = []
        for row in results:
            try:
                arw_path = json.loads(row[0])[0]
                photo_jsons.append(Path(arw_path).with_suffix('.json'))
            except Exception as e:
                print(f"Unable to parse row {row}: {e}")

        return photo_jsons
