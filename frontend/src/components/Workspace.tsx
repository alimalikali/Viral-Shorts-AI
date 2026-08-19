import React, { useState, useEffect } from 'react';
import { Film, Sparkles, Type, ArrowLeft } from 'lucide-react';
import PreviewPlayer from './PreviewPlayer';
import Timeline from './Timeline';
import CaptionEditor from './CaptionEditor';
import ViralMetrics from './ViralMetrics';

interface WorkspaceProps {
  jobId: string;
  onReset: () => void;
}

export interface Word {
  word: string;
  start: number;
  end: number;
  confidence: number;
}

export interface Clip {
  clip_id: string;
  start: number;
  end: number;
  duration: number;
  viral_score: number;
  engagement_rating: string;
  retention_prediction: string;
  suggested_title: string;
  suggested_hashtags: string;
  suggested_caption: string;
  hook_type: string;
  video_url: string;
  words?: Word[];
}

export default function Workspace({ jobId, onReset }: WorkspaceProps) {
  const [status, setStatus] = useState("processing");
  const [progress, setProgress] = useState(0);
  const [clips, setClips] = useState<Clip[]>([]);
  const [activeClip, setActiveClip] = useState<Clip | null>(null);
  const [activeTab, setActiveTab] = useState<"metrics" | "captions">("metrics");
  const [aspectRatio, setAspectRatio] = useState("9:16");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const pollStatus = async () => {
      try {
        const res = await fetch(`/api/status/${jobId}`);
        if (!res.ok) throw new Error("Status query failed");
        
        const data = await res.json();
        setStatus(data.status);
        setProgress(data.progress);
        setAspectRatio(data.aspect_ratio ?? "9:16");
        
        if (data.status === "completed") {
          setClips(data.clips);
          if (data.clips.length > 0) {
            setActiveClip(data.clips[0]);
          }
          clearInterval(interval);
        } else if (data.status === "failed") {
          setError(data.error || "AI processing pipeline encountered a runtime error.");
          clearInterval(interval);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : String(err));
        setStatus("failed");
        clearInterval(interval);
      }
    };

    // Run poll every 1.5 seconds
    const interval = setInterval(pollStatus, 1500);
    pollStatus();

    return () => clearInterval(interval);
  }, [jobId]);

  if (status === "failed") {
    return (
      <div className="max-w-xl mx-auto py-24 px-6 text-center space-y-6">
        <h2 className="text-2xl font-bold tracking-tight text-rose-400">Pipeline Failed</h2>
        <p className="bg-zinc-900/60 p-4 rounded-xl border border-rose-500/30 text-left text-xs text-rose-300 font-mono break-words">
          {error}
        </p>
        <button
          onClick={onReset}
          className="text-zinc-500 hover:text-zinc-300 text-xs font-bold transition"
        >
          Back to Upload
        </button>
      </div>
    );
  }

  if (status !== "completed") {
    return (
      <div className="max-w-xl mx-auto py-24 px-6 text-center space-y-8 animate-pulse-slow">
        <div className="relative inline-block">
          <div className="h-24 w-24 rounded-full border-4 border-brand-cyan/20 border-t-brand-cyan animate-spin flex items-center justify-center">
            <Sparkles className="h-8 w-8 text-brand-cyan" />
          </div>
          <span className="absolute top-0 right-0 h-4 w-4 bg-brand-violet rounded-full ring-4 ring-dark-900 animate-bounce"></span>
        </div>

        <div className="space-y-3">
          <h2 className="text-2xl font-bold tracking-tight">AI Moment Pipeline Active</h2>
          <p className="text-zinc-400 text-sm font-semibold uppercase tracking-wider">
            Phase: <span className="text-brand-cyan">{status.replace("_", " ")}</span> ({progress}%)
          </p>
          <div className="h-1.5 w-full bg-zinc-800 rounded-full overflow-hidden max-w-sm mx-auto">
            <div
              style={{ width: `${progress}%` }}
              className="h-full bg-gradient-to-r from-brand-violet to-brand-cyan transition-all duration-300 rounded-full"
            ></div>
          </div>
        </div>

        <div className="bg-zinc-900/60 p-4 rounded-xl border border-zinc-800/80 text-left max-w-md mx-auto text-xs text-zinc-500 font-mono space-y-1">
          <p className="text-brand-cyan font-bold">{`> Discovering GPU availability... SUCCESS`}</p>
          <p>{`> Extracting 16kHz audio tracks... DONE`}</p>
          {progress > 10 && <p className="text-brand-violet">{`> Scanning transcription boundaries via Whisper... ACTIVE`}</p>}
          {progress > 45 && <p className="text-zinc-400">{`> Computing visual motion & scene changes... ACTIVE`}</p>}
          {progress > 80 && <p className="text-zinc-200">{`> Compiling crop filters & burning ASS styles... ACTIVE`}</p>}
        </div>

        <button 
          onClick={onReset}
          className="text-zinc-500 hover:text-zinc-300 text-xs font-bold transition pt-4"
        >
          Cancel Operation
        </button>
      </div>
    );
  }

  return (
    <div className="h-[calc(100vh-84px)] grid grid-rows-[1fr_220px] bg-dark-900">
      {/* Top Section Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-4 overflow-hidden border-b border-zinc-800/60">
        
        {/* Left sidebar: Generated Moment list */}
        <div className="border-r border-zinc-800/60 flex flex-col overflow-y-auto bg-dark-900">
          <div className="p-4 border-b border-zinc-800/80 flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Film className="h-4 w-4 text-brand-cyan" />
              <span className="font-bold text-sm tracking-tight">Extracted Shorts ({clips.length})</span>
            </div>
            <button 
              onClick={onReset}
              className="p-1.5 text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800/40 rounded transition"
            >
              <ArrowLeft className="h-4 w-4" />
            </button>
          </div>

          <div className="p-3 space-y-2.5 flex-1">
            {clips.map((clip, index) => (
              <button
                key={clip.clip_id}
                onClick={() => setActiveClip(clip)}
                className={`w-full text-left p-3.5 rounded-2xl border transition relative overflow-hidden group ${
                  activeClip?.clip_id === clip.clip_id 
                    ? 'border-brand-cyan bg-brand-cyan/5' 
                    : 'border-zinc-800/80 hover:border-zinc-700 bg-zinc-900/20'
                }`}
              >
                {/* Score badge indicator */}
                <div className="absolute top-3 right-3 bg-gradient-to-tr from-brand-violet to-brand-cyan text-dark-900 text-[10px] font-extrabold px-2 py-0.5 rounded-full shadow">
                  {clip.viral_score}/100
                </div>

                <p className="text-xs text-zinc-500 font-bold uppercase tracking-wider mb-1">Moment #{index+1}</p>
                <h4 className="font-bold text-sm text-zinc-200 truncate pr-16 mb-2">{clip.suggested_title}</h4>
                
                <div className="flex items-center space-x-4 text-[11px] text-zinc-400 font-medium">
                  <span>Duration: <strong className="text-zinc-200 font-bold">{clip.duration}s</strong></span>
                  <span>Range: <strong className="text-zinc-200 font-bold">{clip.start}s - {clip.end}s</strong></span>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Middle main: HTML5 Video Canvas Player */}
        <div className="lg:col-span-2 bg-zinc-950 flex flex-col justify-between p-4 overflow-hidden relative">
          {activeClip ? (
            <PreviewPlayer
              videoUrl={activeClip.video_url}
              aspectRatio={aspectRatio}
              start={activeClip.start}
              end={activeClip.end}
            />
          ) : (
            <div className="flex-1 flex items-center justify-center text-zinc-500 text-sm">
              Select an extracted short to launch video workspace
            </div>
          )}
        </div>

        {/* Right sidebar: Tabs for subtitles and analytics */}
        <div className="border-l border-zinc-800/60 flex flex-col overflow-hidden bg-dark-900">
          <div className="flex border-b border-zinc-800/80">
            <button
              onClick={() => setActiveTab("metrics")}
              className={`flex-1 py-3 text-xs font-bold uppercase tracking-wider border-b-2 transition flex items-center justify-center space-x-2 ${
                activeTab === "metrics" 
                  ? 'border-brand-cyan text-brand-cyan bg-brand-cyan/5' 
                  : 'border-transparent text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900/40'
              }`}
            >
              <Sparkles className="h-3.5 w-3.5" />
              <span>Viral Index</span>
            </button>
            <button
              onClick={() => setActiveTab("captions")}
              className={`flex-1 py-3 text-xs font-bold uppercase tracking-wider border-b-2 transition flex items-center justify-center space-x-2 ${
                activeTab === "captions" 
                  ? 'border-brand-violet text-brand-violet bg-brand-violet/5' 
                  : 'border-transparent text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900/40'
              }`}
            >
              <Type className="h-3.5 w-3.5" />
              <span>Subtitles</span>
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-4">
            {activeClip && activeTab === "metrics" && (
              <ViralMetrics clip={activeClip} />
            )}
            {activeClip && activeTab === "captions" && (
              <CaptionEditor clip={activeClip} />
            )}
          </div>
        </div>

      </div>

      {/* Bottom Timeline Section */}
      {activeClip && (
        <Timeline clip={activeClip} />
      )}
    </div>
  );
}
