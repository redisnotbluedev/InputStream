from dataclasses import dataclass
from pathlib import Path
import sqlite3


COMMON_DB_PATH = "data/index.db"

@dataclass
class WordEntry:
	word: str
	text: str
	show: str
	start: str
	end: str
	season: int
	episode: int

def ready_database(db_path: str):
	conn = sqlite3.connect(db_path)
	c = conn.cursor()

	c.execute("""CREATE TABLE IF NOT EXISTS word_subtitle_index (
		   word TEXT NOT NULL,
		   text TEXT NOT NULL,
		   start TEXT NOT NULL,
		   end NOT NULL,
		   show TEXT NOT NULL,
		   season INTEGER NOT NULL,
		   episode INTEGER NOT NULL)""")
	
	conn.commit()
	conn.close()


def save_index_to_db(index: list[WordEntry], db_path: str = COMMON_DB_PATH):
	Path(db_path).parent.mkdir(parents=True, exist_ok=True)

	if Path(db_path).exists():
		Path(db_path).unlink()
	
	ready_database(db_path)

	conn = sqlite3
