from srt_parser import TextEntry, parse_srt_file
from dataclasses import dataclass
import janome.tokenizer as t
from pathlib import Path
import sqlite3
import re


COMMON_DB_PATH = "data/index.db"
COMMON_SUB_PATH = "subtitles"
Tokenizer = t.Tokenizer()

@dataclass
class WordEntry:
	word: str
	text: str
	show: str
	start: str
	end: str
	season: int
	episode: int

def tokenize(string: str) -> list[str]:
	return [
		token.surface if isinstance(token, t.Token) else token 
		for token in Tokenizer.tokenize(string)
		]

def ready_database(db_path: str):
	conn = sqlite3.connect(db_path)
	c = conn.cursor()

	index_to_subtitle = """CREATE TABLE IF NOT EXISTS index_to_subtitle (
	id INTEGER NOT NULL PRIMARY KEY,
	text TEXT NOT NULL,
	start TEXT NOT NULL,
	end TEXT NOT NULL,
	show TEXT NOT NULL,
	season INTEGER NOT NULL,
	episode INTEGER NOT NULL)"""

	word_to_index = """CREATE TABLE IF NOT EXISTS word_to_index (
	word TEXT NOT NULL,
	subtitle_id INTEGER NOT NULL,
	FOREIGN KEY(subtitle_id) REFERENCES subtitles(id)

	)"""

	c.execute(index_to_subtitle)
	c.execute(word_to_index)
	
	conn.commit()
	conn.close()

def save_index_to_db(index: list[WordEntry], db_path: str = COMMON_DB_PATH):
	Path(db_path).parent.mkdir(parents=True, exist_ok=True)

	if Path(db_path).exists():
		Path(db_path).unlink()
	
	ready_database(db_path)

	conn = sqlite3.connect(db_path)
	c = conn.cursor()

	c.executemany(
		"""INSERT INTO index_to_subtitle (id, text, start, end, show, season, episode) VALUES (?, ?, ?, ?, ?, ?, ?)
		INSERT INTO word_to_index (word, subtitle_id) VALUES (?, ?)""",
		[(idx, entry.text, entry.start, entry.end, entry.show, entry.season, entry.episode, entry.word, idx) for idx, entry in enumerate(index)])
	
	conn.commit()
	conn.close()

def search(
		search: str,
		included_shows: list[str]|None = None,
		excluded_shows: list[str]|None = None,
		seasons: list[int]|None = None,
		episodes: list[int]|None = None,
		exact_match: bool = False,
		db_path: str = COMMON_DB_PATH
		) -> list[WordEntry]:
	conn = sqlite3.connect(db_path)
	c = conn.cursor()

	splitted_search: list[str] = tokenize(search)

	querry = f"""
	SELECT DISTINCT s.*
	FROM index_to_subtitle s
	{' '.join([f'INNER JOIN word_to_index w{i} ON s.id = w{i}.subtitle_id' for i in range(len(splitted_search))])}
	WHERE {' AND '.join([f'w{i}.word = ?' for i in range(len(splitted_search))])}
	"""

	parameters = splitted_search
	# if you are wondering why i dont just put the search right in the string instead of making them question marks, adding an intermediate step where failure can happen.
	# Fuck you.
	# i do what i want.
	# and i dont even know what the fuck im doing,
	# im so tired

	if included_shows:
		querry += f" AND s.show IN ({', '.join(['?' for i in range(len(included_shows))])})"
		parameters += included_shows
	
	if excluded_shows:
		querry += f" AND s.show NOT IN ({', '.join(['?' for i in range(len(excluded_shows))])})"
		parameters += excluded_shows
	
	if seasons:
		querry += f" AND s.season IN ({', '.join(['?' for i in range(len(seasons))])})"
		parameters += seasons

	if episodes:
		querry += f" AND s.episode IN ({', '.join(['?' for i in range(len(episodes))])})"
		parameters += episodes

	c.execute(querry, parameters)

	results_unstructured = c.fetchall()

	results = [
		WordEntry(
			word=entry[0],
			text=entry[1],
			start=entry[2],
			end=entry[3],
			show=entry[4],
			season=entry[5],
			episode=entry[6]
			) for entry in results_unstructured
		]

	return results

def get_metadata(srt_path, root_path) -> dict:
	# what needs
	# 1. get the relative path
	# 2. get show name/season
	# 3. get episode number

	# 1. relative
	relative_path = Path(srt_path).relative_to(root_path)

	# 2. get show name/season

	show_match = re.match(r"([^(]+)\(?(\d+)?\)?", str(relative_path.parent))

	if not show_match:
		show = None
		season = None
	else:
		show = show_match.group(1)
		season = show_match.group(2) if show_match.group(2) is not None else "1"
	
	ep = relative_path.stem

	return {"show": show, "season": int(season) if season is not None else season, "episode": int(ep)}

def build_index(root_path: str = COMMON_SUB_PATH) -> list[WordEntry]:
	index: list[WordEntry] = []
	
	# what needs to be done:
	# 1. get all srt file directorys
	# 2. loop through each, parsing the file and getting metadata
	# 3. add to index as a WordEntry

	# 1. get all srt file directorys
	subtitle_dir = Path(root_path)

	srt_files = list(subtitle_dir.rglob("*.srt"))

	# 2. loop through each, parsing the file and getting metadata
	for file in srt_files:
		text_entries = parse_srt_file(str(file))

		metadata = get_metadata(file, root_path)

		for tex in text_entries:
			words = tokenize(tex.text)

			for word in words:
				index.append(WordEntry(
					word=	word,
					text=	tex.text,
					show=	metadata["show"],
					start=	tex.start,
					end=	tex.end,
					season=	metadata["season"],
					episode=metadata["episode"]
				))

	return index

def build_on_database(root_path: str = COMMON_SUB_PATH, db_path: str = COMMON_DB_PATH):
	Path(db_path).parent.mkdir(parents=True, exist_ok=True)

	if Path(db_path).exists():
		Path(db_path).unlink()
	
	ready_database(db_path)

	subtitle_dir = Path(root_path)
	srt_files = list(subtitle_dir.rglob('*.srt'))

	conn = sqlite3.connect(db_path)
	c = conn.cursor()

	idx = 0

	for file in srt_files:
		text_entries = parse_srt_file(str(file))
		metadata = get_metadata(file, root_path)

		subtitles = [(idx + i, te.text, te.start, te.end, metadata["show"], metadata["season"], metadata["episode"]) for i, te in enumerate(text_entries)]

		idx += len(subtitles)

		c.executemany(
			"INSERT INTO index_to_subtitle (id, text, start, end, show, season, episode) VALUES (?, ?, ?, ?, ?, ?, ?)",
			subtitles)
		
		words = []
		for sub in subtitles:
			tokens = tokenize(sub[1])

			words += [(word, sub[0]) for word in tokens]
		
		c.executemany(
			"INSERT INTO word_to_index (word, subtitle_id) VALUES (?, ?)", 
			words)
	
	conn.commit()
	conn.close()


if __name__ == "__main__":
	
	print("=== Starting search ===")
	result = search("私")
	print(f"result:")
	for we in result[:5]:
		print(we)
