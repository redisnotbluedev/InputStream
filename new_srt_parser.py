from dataclasses import dataclass
from pathlib import Path
import re

@dataclass
class TextEntry:
	idx: int
	text: str
	start: str
	end: str

def parse_srt_block(srt_block: str) -> TextEntry:
	srt_match = re.match(r'(\d+)\n(\d\d:\d\d:\d\d,\d\d\d)\s-->\s(\d\d:\d\d:\d\d,\d\d\d)\n+(.*)', srt_block.strip())

	if not srt_match:
		raise ValueError(f'Srt block doesnt match the srt format, double check it:\n{srt_block}')
	
	return TextEntry(text=srt_match.group(4), start=srt_match.group(2), end=srt_match.group(3), idx=int(srt_match.group(1)))

def parse_srt_file(file_path: str) -> list[TextEntry]:
	if not Path(file_path).exists():
		raise ValueError(f'Path "{file_path}" doesnt exist, double check the path')
	
	with open(file_path, 'r', encoding="utf-8") as f:
		file_contence = f.read()

	srt_blocks = re.split(r'\n\n+', file_contence)
	
	result = []
	
	for block in srt_blocks:
		result.append(parse_srt_block(block))

	return result