import React from 'react';
import { ZoomIn, ZoomOut, Scissors, Download } from 'lucide-react';
import { Clip } from './Workspace';

interface TimelineProps {
  clip: Clip;
}

export default function Timeline({ clip }: TimelineProps) {
  // Generate random heights for waveform decoration
  const waveformBars = Array.from({ length: 90 }, () => Math.floor(Math.random() * 32) + 8);

  const handleExportClip = () => {
    const link = document.createElement("a");
    link.href = clip.video_url;
    link.download = `viral_short_${clip.clip_id}.mp4`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="glass-panel border-t border-zinc-800/80 p-4 grid grid-rows-[40px_1fr] gap-2 overflow-hidden bg-dark-800/90 shadow-2xl">
      {/* Timeline Utility Menu */}
      <div className="flex items-center justify-between border-b border-zinc-800/60 pb-2">
        <div className="flex items-center space-x-3">
          <button className="bg-brand-cyan/15 hover:bg-brand-cyan/20 border border-brand-cyan/25 text-brand-cyan text-xs font-bold px-3 py-1.5 rounded-lg transition flex items-center space-x-1.5">
            <Scissors className="h-3.5 w-3.5" />
            <span>AI Smart Cut Active</span>
          </button>
          <span className="text-[11px] text-zinc-500 font-mono">Boundaries aligned to spoken word boundaries</span>
        </div>

        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-1 bg-zinc-900/60 rounded-lg p-1 border border-zinc-800">
            <button className="p-1 hover:bg-zinc-800 rounded transition text-zinc-400 hover:text-zinc-200">
              <ZoomOut className="h-3.5 w-3.5" />
            </button>
            <span className="text-[10px] text-zinc-500 px-1 font-bold">1x</span>
            <button className="p-1 hover:bg-zinc-800 rounded transition text-zinc-400 hover:text-zinc-200">
              <ZoomIn className="h-3.5 w-3.5" />
            </button>
          </div>

          <button
            onClick={handleExportClip}
            className="bg-gradient-to-r from-brand-violet to-brand-cyan text-dark-900 text-xs font-black px-4 py-2 rounded-xl shadow-lg hover:opacity-90 transition flex items-center space-x-2"
          >
            <Download className="h-4 w-4 stroke-[2.5]" />
            <span>Export Short</span>
          </button>
        </div>
      </div>

      {/* Timeline Waveform Canvas Track */}
      <div className="relative bg-zinc-900/40 rounded-2xl border border-zinc-800/80 p-3 overflow-hidden flex items-center h-24">
        {/* Timestamp rulers */}
        <div className="absolute top-1 left-3 right-3 flex justify-between text-[9px] text-zinc-600 font-mono font-bold">
          <span>{clip.start.toFixed(1)}s</span>
          <span>{((clip.start + clip.end) / 2.0).toFixed(1)}s</span>
          <span>{clip.end.toFixed(1)}s</span>
        </div>

        {/* Visual Waveform tracks */}
        <div className="flex-1 flex items-center justify-between px-6 pt-2 select-none h-10 w-full opacity-60">
          {waveformBars.map((height, i) => (
            <div
              key={i}
              style={{ height: `${height}px` }}
              className="w-[3px] rounded-full bg-zinc-700/80 waveform-bar"
            ></div>
          ))}
        </div>

        {/* Highlighted active crop window overlay */}
        <div className="absolute inset-y-0 left-6 right-6 border-2 border-brand-cyan bg-brand-cyan/5 rounded-xl pointer-events-none flex justify-between items-center px-2">
          {/* Left Crop Bar Bracket */}
          <div className="w-1.5 h-8 bg-brand-cyan rounded-full"></div>
          {/* Right Crop Bar Bracket */}
          <div className="w-1.5 h-8 bg-brand-cyan rounded-full"></div>
        </div>
      </div>
    </div>
  );
}
