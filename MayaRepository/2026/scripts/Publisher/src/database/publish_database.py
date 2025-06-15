import sqlite3
from datetime import datetime
from typing import List, Tuple
from pathlib import Path
from ..core.models import PublishRecord


class PublishDatabase:
    """SQLite database manager for publish records"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize database tables"""
        # Ensure directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS publishes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    show_name TEXT NOT NULL,
                    asset_type TEXT NOT NULL,
                    asset_id TEXT NOT NULL,
                    task TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    file_path TEXT NOT NULL,
                    file_size INTEGER DEFAULT 0,
                    artist TEXT NOT NULL,
                    comments TEXT DEFAULT '',
                    published_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    maya_version TEXT DEFAULT '',
                    UNIQUE(show_name, asset_type, asset_id, task, version)
                )
            """
            )

            # Create indexes for faster queries
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_show_asset
                ON publishes(show_name, asset_type, asset_id)
            """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_published_at
                ON publishes(published_at DESC)
            """
            )

    def create_publish(self, record: PublishRecord) -> PublishRecord:
        """Create a new publish record"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO publishes
                (show_name, asset_type, asset_id, task, version, file_path,
                 file_size, artist, comments, published_at, maya_version)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    record.show_name,
                    record.asset_type,
                    record.asset_id,
                    record.task,
                    record.version,
                    record.file_path,
                    record.file_size,
                    record.artist,
                    record.comments,
                    record.published_at or datetime.now(),
                    record.maya_version,
                ),
            )

            record.id = cursor.lastrowid
            return record

    def get_publishes_by_show(self, show_name: str) -> List[PublishRecord]:
        """Get all publishes for a show"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT * FROM publishes
                WHERE show_name = ?
                ORDER BY asset_type, asset_id, task, version
            """,
                (show_name,),
            )

            return [PublishRecord.from_dict(dict(row)) for row in cursor.fetchall()]

    def get_asset_versions(
        self, show_name: str, asset_type: str, asset_id: str, task: str
    ) -> List[PublishRecord]:
        """Get all versions for a specific asset/task"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT * FROM publishes
                WHERE show_name = ? AND asset_type = ? AND asset_id = ? AND task = ?
                ORDER BY version DESC
            """,
                (show_name, asset_type, asset_id, task),
            )

            return [PublishRecord.from_dict(dict(row)) for row in cursor.fetchall()]

    def get_next_version(self, show_name: str, asset_type: str, asset_id: str, task: str) -> int:
        """Get the next available version number"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT MAX(version) FROM publishes
                WHERE show_name = ? AND asset_type = ? AND asset_id = ? AND task = ?
            """,
                (show_name, asset_type, asset_id, task),
            )

            result = cursor.fetchone()
            return (result[0] or 0) + 1

    def get_recent_publishes(self, limit: int = 20) -> List[PublishRecord]:
        """Get recent publishes across all shows"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT * FROM publishes
                ORDER BY published_at DESC
                LIMIT ?
            """,
                (limit,),
            )

            return [PublishRecord.from_dict(dict(row)) for row in cursor.fetchall()]

    def delete_publish(self, publish_id: int) -> bool:
        """Delete a publish record"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM publishes WHERE id = ?", (publish_id,))
            return cursor.rowcount > 0

    def get_publish_by_id(self, publish_id: int) -> PublishRecord:
        """Get a specific publish by ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM publishes WHERE id = ?", (publish_id,))
            row = cursor.fetchone()

            if row:
                return PublishRecord.from_dict(dict(row))
            return None
