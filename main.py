from srt_parser import parse_srt_file
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
import sqlite3
import fugashi
import string
import json
import re

tagger = fugashi.Tagger() #type: ignore

SQL3_DATABASE_PATH = "data/index.db"
JSON_DATABASE_PATH = "data/index.json"

def normalize_word(word: str) -> str:
	return word.translate(str.maketrans('', '', string.punctuation)).lower().strip()

def tokenize_text(text: str) -> list[str]:
	return [word.surface for word in tagger(text)]
	
def extract_metadata(srt_path: Path, root_path: Path) -> dict:
	relative_path = srt_path.relative_to(root_path)
	parts = relative_path.parts
	show_folder = parts[0]
	episode = int(srt_path.stem)
	
	season_match = re.search(r'\((\d+)\)$', show_folder)

	if season_match:
		season = int(season_match.group(1))
		show_name = show_folder[:season_match.start()]
	else:
		season = 1
		show_name = show_folder

	return {
		"show": show_name,
		"season": season,
		"episode": episode
	}

def build_index(subtitles_root: str) -> dict[str, list[dict]]:
	index = defaultdict(list)
	subtitles_path = Path(subtitles_root)

	srt_files = list(subtitles_path.rglob('*.srt'))
	
	for srt_file in srt_files:

		metadata = extract_metadata(srt_file, subtitles_path)

		try:
			entries = parse_srt_file(str(srt_file))

		except Exception as e:
			print(f'Error parsing {srt_file}: {e}')
			continue

		for entry in entries:
			words = tokenize_text(entry.text)

			for word in words:
				normalized = normalize_word(word)

				if not normalized:
					continue

				index[normalized].append({
					"show": metadata["show"],
					"season": metadata["season"],
					"episode": metadata["episode"],
					"start": entry.start_time,
					"end": entry.end_time,
					"text": entry.text
				})
				

	return dict(index)

def save_index_json(index:dict, output_path: str = JSON_DATABASE_PATH):
	Path(output_path).parent.mkdir(parents=True, exist_ok=True)

	with open(output_path, 'w', encoding='utf-8') as f:
		json.dump(index, f, ensure_ascii=False, indent=2)
	
	print(f"Index was saved to {output_path}")

def load_index_json(index_path: str = JSON_DATABASE_PATH):
	with open(index_path, 'r', encoding='utf-8') as f:
		index = json.load(f)

	print(f"Index loaded from {index_path}")
	print(f"Total unique words: {len(index)}")

	return index

def create_sql_database(db_path: str = SQL3_DATABASE_PATH):
	conn = sqlite3.connect(db_path)
	cur = conn.cursor()

	cur.execute('''CREATE TABLE IF NOT EXISTS subtitle_index (
			 id INTEGER PRIMARY KEY AUTOINCREMENT, 
			 word TEXT NOT NULL,
			 show TEXT NOT NULL,
			 season INTEGER NOT NULL,
			 episode INTEGER NOT NULL,
			 start_time TEXT NOT NULL,
			 end_time TEXT NOT NULL,
			 full_text TEXT NOT NULL)''')
	
	cur.execute('CREATE INDEX IF NOT EXISTS word_index ON subtitle_index(word)')

	conn.commit()
	conn.close()

	print(f'Database created at {db_path}')

def save_index_sql(index:dict, db_path: str = SQL3_DATABASE_PATH):
	Path(db_path).parent.mkdir(parents=True, exist_ok=True)

	if Path(db_path).exists():
		Path(db_path).unlink()

	create_sql_database(db_path)

	conn = sqlite3.connect(db_path)
	cur = conn.cursor()

	total_rows = 0
	for word, occurences in index.items():
		for occurence in occurences:
			cur.execute('''INSERT INTO subtitle_index (word, show, season, episode, start_time, end_time, full_text)
			   VALUES (?, ?, ?, ?, ?, ?, ?)''', (
				   word,
				   occurence["show"],
				   occurence["season"],
				   occurence["episode"],
				   occurence["start"],
				   occurence["end"],
				   occurence["text"]
			   ))
			total_rows += 1
	
	conn.commit()
	conn.close()

def load_index_sql(db_path: str = SQL3_DATABASE_PATH):
	conn = sqlite3.connect(db_path)
	cur = conn.cursor()

	cur.execute('SELECT word, show, season, episode, start_time, end_time, full_text FROM subtitle_index')
	rows = cur.fetchall()
	conn.close()

	index = defaultdict(list)
	for row in rows:
		word = row[0]
		index[word].append({
			"show": row[1],
			"season": row[2],
			"episode": row[3],
			"start": row[4],
			"end": row[5],
			"text": row[6]
		})

	return dict(index)

def search_sql(word: str, db_path: str = SQL3_DATABASE_PATH) -> list[dict]:
	normalized = tokenize_text(word)

	if not normalized:
		return []
	
	conn = sqlite3.connect(db_path)
	cur = conn.cursor()

	cur.execute('''SELECT show, season, episode, start_time, end_time, full_text
			 FROM subtitle_index
			 WHERE word = ?
			 ''', (normalized[0],))
	
	results = cur.fetchall()
	conn.close()

	occurences = []
	for row in results:
		occurences.append({
            "show": row[0],
            "season": row[1],
            "episode": row[2],
            "start": row[3],
            "end": row[4],
            "text": row[5]
		})
	
	return occurences

if __name__ == "__main__":
	print("=== Test Build & Search | JSON ===")
	index = build_index("./subtitles")

	print(f"\nIndex built! Total unique words: {len(index)}")

	test_word = "私"
	if test_word in index:
		print(f"\nFound '{test_word}' in {len(index[test_word])} places!:")

		for occurence in index[test_word][:3]:
			print(f"	{occurence}")
		
	print("\n=== Test Save | JSON ===")
	save_index_json(index)

	print("\n=== Test Load & Search | JSON ===")
	new_idx = load_index_json()

	if test_word in new_idx:
		print(f"\nFound '{test_word}' in {len(new_idx[test_word])} places!:")

		for occurence in new_idx[test_word][:3]:
			print(f"	{occurence}")

	print("\n=== Test Save | SQL ===")
	save_index_sql(index)
	
	print("\n=== Test Search | SQL ===")
	print(tokenize_text("私"))
	for occurence in search_sql("私"):
		print(f"\t{occurence}")