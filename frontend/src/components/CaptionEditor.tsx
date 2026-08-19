import { useEffect, useMemo, useState } from 'react';
import { AlertCircle, Edit, Check } from 'lucide-react';
import { Clip, Word } from './Workspace';

interface CaptionEditorProps {
  clip: Clip;
}

interface SubtitleLine {
  id: number;
  text: string;
  start: number;
  end: number;
}

const WORDS_PER_LINE = 3;

const formatTime = (seconds: number) => {
  const mins = Math.floor(seconds / 60);
  const secs = (seconds % 60).toFixed(1).padStart(4, "0");
  return `${mins}:${secs}`;
};

// Mirrors caption_burner.generate_ass_file: break on 3 words, punctuation or a long pause
const groupIntoLines = (words: Word[]): SubtitleLine[] => {
  const lines: SubtitleLine[] = [];
  let current: Word[] = [];

  words.forEach((word, i) => {
    current.push(word);
    const pause = i < words.length - 1 ? words[i + 1].start - word.end : 0;
    const breaks = current.length >= WORDS_PER_LINE || pause > 0.6 || /[.!?]$/.test(word.word);
    if (breaks) {
      lines.push({
        id: lines.length,
        text: current.map(w => w.word).join(" "),
        start: current[0].start,
        end: current[current.length - 1].end
      });
      current = [];
    }
  });

  if (current.length) {
    lines.push({
      id: lines.length,
      text: current.map(w => w.word).join(" "),
      start: current[0].start,
      end: current[current.length - 1].end
    });
  }

  return lines;
};

export default function CaptionEditor({ clip }: CaptionEditorProps) {
  const initialLines = useMemo(() => groupIntoLines(clip.words ?? []), [clip]);
  const [captions, setCaptions] = useState<SubtitleLine[]>(initialLines);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editingText, setEditingText] = useState("");

  useEffect(() => {
    setCaptions(initialLines);
    setEditingId(null);
  }, [initialLines]);

  const handleEditClick = (line: SubtitleLine) => {
    setEditingId(line.id);
    setEditingText(line.text);
  };

  const handleSaveClick = (id: number) => {
    setCaptions(prev => prev.map(c => c.id === id ? { ...c, text: editingText } : c));
    setEditingId(null);
  };

  if (!captions.length) {
    return (
      <p className="text-xs text-zinc-500 font-medium">
        No speech was transcribed inside this clip.
      </p>
    );
  }

  return (
    <div className="space-y-4 animate-slide-up">
      <div className="flex items-center space-x-2 bg-brand-violet/10 text-brand-violet px-3 py-2 rounded-xl border border-brand-violet/20">
        <AlertCircle className="h-4 w-4 shrink-0" />
        <span className="text-[10px] font-bold tracking-tight">Edits here are local only — the burned-in captions are already rendered.</span>
      </div>

      <div className="space-y-3">
        {captions.map(line => (
          <div
            key={line.id}
            className={`p-3.5 rounded-2xl border transition ${
              editingId === line.id
                ? 'border-brand-violet bg-brand-violet/5'
                : 'border-zinc-800 bg-zinc-900/30 hover:border-zinc-700/60'
            }`}
          >
            <div className="flex justify-between items-center mb-1.5">
              <span className="text-[10px] text-zinc-500 font-mono font-bold">{formatTime(line.start)} ➔ {formatTime(line.end)}</span>
              {editingId === line.id ? (
                <button
                  onClick={() => handleSaveClick(line.id)}
                  className="p-1 text-emerald-400 hover:bg-emerald-500/10 rounded transition"
                >
                  <Check className="h-4 w-4" />
                </button>
              ) : (
                <button
                  onClick={() => handleEditClick(line)}
                  className="p-1 text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800/40 rounded transition"
                >
                  <Edit className="h-3.5 w-3.5" />
                </button>
              )}
            </div>

            {editingId === line.id ? (
              <textarea
                value={editingText}
                onChange={(e) => setEditingText(e.target.value)}
                className="w-full bg-zinc-900 border border-brand-violet rounded-lg p-2 text-sm text-zinc-100 font-medium focus:ring-0 focus:outline-none h-16 resize-none"
              />
            ) : (
              <p className="text-sm font-bold text-zinc-200 leading-relaxed">{line.text}</p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
