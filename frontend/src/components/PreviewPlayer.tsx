import React, { useRef, useState, useEffect } from 'react';
import { Play, Pause, RotateCcw, Volume2, VolumeX } from 'lucide-react';

interface PreviewPlayerProps {
  videoUrl: string;
  aspectRatio: string;
  start: number;
  end: number;
}

export default function PreviewPlayer({ videoUrl, aspectRatio, start, end }: PreviewPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(start);
  const [isMuted, setIsMuted] = useState(false);

  // Restart video playback when URL or start times change
  useEffect(() => {
    if (videoRef.current) {
      videoRef.current.load();
      videoRef.current.currentTime = start;
      if (isPlaying) {
        videoRef.current.play().catch(() => setIsPlaying(false));
      }
    }
  }, [videoUrl, start]);

  const togglePlay = () => {
    if (!videoRef.current) return;
    if (isPlaying) {
      videoRef.current.pause();
      setIsPlaying(false);
    } else {
      videoRef.current.play().catch(() => {});
      setIsPlaying(true);
    }
  };

  const handleTimeUpdate = () => {
    if (!videoRef.current) return;
    const t = videoRef.current.currentTime;
    setCurrentTime(t);
    
    // Loop playback smoothly if it goes past the end bounds of the short clip
    if (t >= end || t < start) {
      videoRef.current.currentTime = start;
    }
  };

  const toggleMute = () => {
    if (!videoRef.current) return;
    videoRef.current.muted = !isMuted;
    setIsMuted(!isMuted);
  };

  const handleRestart = () => {
    if (!videoRef.current) return;
    videoRef.current.currentTime = start;
    if (!isPlaying) {
      videoRef.current.play().catch(() => {});
      setIsPlaying(true);
    }
  };

  // Compute responsive sizing based on aspect ratio
  const getAspectClass = () => {
    switch (aspectRatio) {
      case "9:16":
        return "aspect-[9/16] h-[480px] md:h-[520px]";
      case "1:1":
        return "aspect-square h-[380px]";
      case "16:9":
      default:
        return "aspect-[16/9] w-full max-w-2xl";
    }
  };

  return (
    <div className="flex-1 flex flex-col items-center justify-center space-y-4">
      {/* Visual Aspect Ratio Phone Container */}
      <div className={`relative bg-zinc-900 rounded-3xl overflow-hidden border border-zinc-800 shadow-2xl ${getAspectClass()} flex items-center justify-center`}>
        
        {/* HTML5 video element */}
        <video
          ref={videoRef}
          src={videoUrl}
          onTimeUpdate={handleTimeUpdate}
          className="w-full h-full object-cover"
          onClick={togglePlay}
          muted={isMuted}
          playsInline
          loop
        />

        {/* Center overlay button when paused */}
        {!isPlaying && (
          <div 
            onClick={togglePlay}
            className="absolute inset-0 bg-dark-900/30 flex items-center justify-center cursor-pointer transition group"
          >
            <div className="bg-brand-cyan p-5 rounded-full shadow-lg scale-90 group-hover:scale-100 transition duration-300">
              <Play className="h-6 w-6 text-dark-900 fill-dark-900" />
            </div>
          </div>
        )}

        {/* Small watermark/badge */}
        <div className="absolute top-4 left-4 bg-dark-900/60 backdrop-blur border border-white/5 px-2.5 py-1 rounded-lg text-[9px] font-bold text-zinc-300 uppercase tracking-wider flex items-center space-x-1.5">
          <span className="h-1.5 w-1.5 bg-brand-cyan rounded-full animate-ping"></span>
          <span>Preview Render</span>
        </div>
      </div>

      {/* Control Dashboard Panel */}
      <div className="glass-panel px-6 py-3.5 rounded-2xl border border-zinc-800/80 w-full max-w-sm flex items-center justify-between shadow-lg">
        <div className="flex items-center space-x-3">
          <button
            onClick={togglePlay}
            className="p-2 text-zinc-300 hover:text-white hover:bg-zinc-800/50 rounded-lg transition"
          >
            {isPlaying ? <Pause className="h-5 w-5 fill-zinc-300" /> : <Play className="h-5 w-5 fill-zinc-300" />}
          </button>
          <button
            onClick={handleRestart}
            className="p-2 text-zinc-300 hover:text-white hover:bg-zinc-800/50 rounded-lg transition"
          >
            <RotateCcw className="h-4 w-4" />
          </button>
          <button
            onClick={toggleMute}
            className="p-2 text-zinc-300 hover:text-white hover:bg-zinc-800/50 rounded-lg transition"
          >
            {isMuted ? <VolumeX className="h-5 w-5 text-brand-rose" /> : <Volume2 className="h-5 w-5" />}
          </button>
        </div>

        {/* Small clock readout */}
        <div className="text-[11px] text-zinc-500 font-mono font-bold uppercase">
          <span className="text-zinc-200">{(currentTime - start).toFixed(1)}s</span> / {(end - start).toFixed(1)}s
        </div>
      </div>
    </div>
  );
}
