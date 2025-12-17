from dataclasses import dataclass
import re

@dataclass
class SubtitleEntry:
	index: int
	start_time: str
	end_time: str
	text: str

def parse_srt_file(filepath: str) -> list[SubtitleEntry]:
	with open(filepath, 'r', encoding='utf-8') as f:
		content = f.read()
	
	entries = re.split(r'\n\n+', content.strip())

	parsed_entries: list[SubtitleEntry] = []

	for entry in entries:
		lines = entry.split('\n')

		if len(lines) < 3:
			continue

		try:
			idx = int(lines[0].strip())
		except ValueError:
			continue

		timestamp_match = re.match(
			r'(\d\d:\d\d:\d\d,\d\d\d)\s*-->\s*(\d\d:\d\d:\d\d,\d\d\d)',
			lines[1]
		)

		if not timestamp_match:
			continue

		start_time = timestamp_match.group(1)
		end_time = timestamp_match.group(2)

		text = '\n'.join(lines[2:]).strip()
		
		parsed_entries.append(SubtitleEntry(idx, start_time, end_time, text))
	
	return parsed_entries