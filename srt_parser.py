from dataclasses import dataclass
from pathlib import Path
import re

@dataclass
class TextEntry:
	idx: int
	text: str
	start: str
	end: str

def parse_srt_block(srt_block: str) -> TextEntry|None:
	srt_match = re.search(r'(.+)\n(\d\d:\d\d:\d\d,\d\d\d)\s*-->\s*(\d\d:\d\d:\d\d,\d\d\d)\n+(.*)', srt_block.strip())

	if not srt_match:
		print(f"ValueError: Srt block doesnt match the srt format, double check it:\n{srt_block}\n---\n{repr(srt_block)}")
		return
	
	return TextEntry(text=srt_match.group(4), start=srt_match.group(2), end=srt_match.group(3), idx=int(srt_match.group(1)))

def parse_srt_file(file_path: str) -> list[TextEntry]:
	if not Path(file_path).exists():
		raise ValueError(f'Path "{file_path}" doesnt exist, double check the path')
	
	print(f"parsing file: {file_path}")
	with open(file_path, 'r', encoding="utf-8-sig") as f:
		file_contence = f.read()

	srt_blocks = re.split(r'\n\n+', file_contence.strip())
	
	result = []
	
	for block in srt_blocks:
		parsed = parse_srt_block(block.strip())
		if parsed is not None: result.append(parsed)

	return result

if __name__ == "__main__":
	things = parse_srt_file("subtitles/Vinland Saga/1.srt")
	[print(thing) for thing in things[:5]]