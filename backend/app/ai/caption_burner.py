import re
from typing import List, Dict, Any

LATIN_FONT = "DejaVu Sans"
# DejaVu misses Urdu glyphs and Noto Sans Arabic Bold drops the lam-alef ligature
ARABIC_FONT = "Noto Naskh Arabic"
ARABIC_RANGE = re.compile(r"[؀-ۿݐ-ݿﭐ-﷿ﹰ-﻿]")


class CaptionBurner:
    def __init__(self):
        # High impact keywords map to emojis
        self.emoji_map = {
            "crazy": "🤪", "insane": "🤯", "shocking": "😱", "amazing": "🤩",
            "fire": "🔥", "look": "👀", "wait": "⏳", "believe": "🤫",
            "screaming": "🙀", "laughs": "😂", "money": "💰", "rocket": "🚀",
            "gaming": "🎮", "love": "❤️", "time": "⏰", "shouting": "🔊"
        }

    def select_emoji(self, word: str) -> str:
        """Finds matching emoji for a word if any exists."""
        clean = re.sub(r'[^\w]', '', word.lower())
        for key, emoji in self.emoji_map.items():
            if key in clean:
                return emoji
        return ""

    def generate_ass_file(self, words: List[Dict[str, Any]], ass_output_path: str, style_name: str = "TikTok") -> bool:
        """
        Generates a highly styled ASS subtitle file from list of words.
        Uses advanced subtitle styles: thick borders, active word colored yellow,
        inactive words white, and auto emoji insertions.
        """
        try:
            # Group words into short lines (e.g., maximum 3 words per line for high readability shorts)
            lines = []
            current_line = []
            
            # Words per line limit
            limit = 3
            
            for i, w in enumerate(words):
                current_line.append(w)
                # Group when we hit limit, or punctuation, or long pauses
                pause = 0.0
                if i < len(words) - 1:
                    pause = words[i+1]["start"] - w["end"]
                    
                if len(current_line) >= limit or pause > 0.6 or w["word"].endswith(".") or w["word"].endswith("!") or w["word"].endswith("?"):
                    lines.append(current_line)
                    current_line = []
                    
            if current_line:
                lines.append(current_line)

            font = ARABIC_FONT if ARABIC_RANGE.search(" ".join(w["word"] for w in words)) else LATIN_FONT

            # ASS Header
            ass_content = [
                "[Script Info]",
                "Title: Styled Captions",
                "ScriptType: v4.00+",
                "Collisions: Normal",
                "PlayResX: 1080",
                "PlayResY: 1920",
                "",
                "[V4+ Styles]",
                "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
                # Style TikTok: Ultra Bold, large font size, white primary, yellow outline highlight, aligned in center
                f"Style: TikTok,{font},90,&H00FFFFFF,&H0000FFFF,&H00000000,&H80000000,-1,0,0,0,100,100,2,0,1,10,5,5,10,10,960,1",
                f"Style: Meme,{font},80,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,1,0,1,8,2,5,10,10,1650,1",
                "",
                "[Events]",
                "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"
            ]

            # Write subtitle lines with active word highlights
            for line_words in lines:
                line_start = self._format_timestamp(line_words[0]["start"])
                line_end = self._format_timestamp(line_words[-1]["end"])
                
                # We write a subtitle event for each individual word inside the group,
                # highlighting that word and graying out/keeping other words white.
                for active_idx, active_word in enumerate(line_words):
                    word_start_str = self._format_timestamp(active_word["start"])
                    word_end_str = self._format_timestamp(active_word["end"])
                    
                    styled_text = ""
                    for j, w in enumerate(line_words):
                        word_str = w["word"]
                        emoji = self.select_emoji(word_str)
                        if emoji:
                            word_str = f"{emoji} {word_str}"
                            
                        if j == active_idx:
                            # Highlight active word in Yellow (&H0000FFFF&) and scale up
                            styled_text += f"{{\\c&H0000FFFF&}}{word_str}{{\\c&H00FFFFFF&}} "
                        else:
                            # Render standard white
                            styled_text += f"{word_str} "
                            
                    styled_text = styled_text.strip()
                    
                    # Add caption event
                    ass_content.append(
                        f"Dialogue: 0,{word_start_str},{word_end_str},{style_name},,0,0,0,,{styled_text}"
                    )

            with open(ass_output_path, "w", encoding="utf-8") as f:
                f.write("\n".join(ass_content))
            return True
        except Exception as e:
            print(f"Error generating ASS subtitles: {str(e)}")
            return False

    def _format_timestamp(self, seconds: float) -> str:
        """Converts float seconds to ASS timestamp format H:MM:SS.cs"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centiseconds = int((seconds - int(seconds)) * 100)
        return f"{hours}:{minutes:02d}:{secs:02d}.{centiseconds:02d}"

caption_burner = CaptionBurner()
