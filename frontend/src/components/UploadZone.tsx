import React, { useState, useRef } from 'react';
import { UploadCloud, Film, Settings2, Sparkles, VolumeX } from 'lucide-react';

interface UploadZoneProps {
  onStartProcessing: (config: {
    videoPath: string;
    aspectRatio: string;
    styleName: string;
    removeSilence: boolean;
  }) => void;
}

export default function UploadZone({ onStartProcessing }: UploadZoneProps) {
  const [dragActive, setDragActive] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [aspectRatio, setAspectRatio] = useState("9:16");
  const [styleName, setStyleName] = useState("TikTok");
  const [removeSilence, setRemoveSilence] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const selectFile = () => {
    fileInputRef.current?.click();
  };

  const handleUploadAndAnalyze = async () => {
    if (!file) return;
    
    setUploading(true);
    setUploadError(null);
    setUploadProgress(15);
    
    // Simulate real chunk upload timing
    const interval = setInterval(() => {
      setUploadProgress(prev => {
        if (prev >= 90) {
          clearInterval(interval);
          return 90;
        }
        return prev + 12;
      });
    }, 400);

    try {
      const formData = new FormData();
      formData.append("file", file);
      
      const response = await fetch("/api/upload", {
        method: "POST",
        body: formData
      });
      
      clearInterval(interval);
      setUploadProgress(100);

      if (!response.ok) {
        throw new Error(`Upload rejected (${response.status}): ${await response.text()}`);
      }

      const data = await response.json();

      onStartProcessing({
        videoPath: data.saved_path,
        aspectRatio,
        styleName,
        removeSilence
      });
    } catch (err) {
      clearInterval(interval);
      setUploadError(err instanceof Error ? err.message : String(err));
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto py-12 px-4 animate-fade-in">
      {/* Title Header */}
      <div className="text-center mb-10">
        <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight mb-3">
          Create Viral Shorts In <span className="bg-gradient-to-r from-brand-cyan via-brand-violet to-brand-rose bg-clip-text text-transparent">One Click</span>
        </h1>
        <p className="text-zinc-400 max-w-xl mx-auto text-base">
          Upload any long-form video. Our open-source AI automatically finds high-engagement hooks, tracks active speakers, crops to vertical aspect ratio, and burns animated subtitles.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Upload Box Component */}
        <div className="lg:col-span-2 space-y-6">
          <div
            onDragEnter={handleDrag}
            onDragOver={handleDrag}
            onDragLeave={handleDrag}
            onDrop={handleDrop}
            onClick={selectFile}
            className={`border-2 border-dashed rounded-3xl p-12 text-center cursor-pointer transition-all duration-300 min-h-[380px] flex flex-col justify-center items-center ${
              dragActive 
                ? 'border-brand-cyan bg-brand-cyan/5 scale-[1.01]' 
                : 'border-zinc-800 bg-zinc-900/40 hover:border-zinc-700/80 hover:bg-zinc-900/60'
            }`}
          >
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              className="hidden"
              accept="video/*"
            />
            
            <div className="bg-zinc-800/80 p-5 rounded-2xl mb-4 border border-zinc-700/50 flex items-center justify-center shadow-lg">
              <UploadCloud className="h-10 w-10 text-brand-cyan" />
            </div>

            {file ? (
              <div className="space-y-2">
                <p className="text-lg font-bold text-zinc-100">{file.name}</p>
                <p className="text-xs text-zinc-500 font-semibold uppercase">{(file.size / (1024 * 1024)).toFixed(1)} MB • Video File</p>
                <div className="flex items-center justify-center space-x-2 text-brand-cyan text-xs font-bold pt-2">
                  <Film className="h-4 w-4" />
                  <span>Click box to change video</span>
                </div>
              </div>
            ) : (
              <div className="space-y-2">
                <p className="text-lg font-semibold text-zinc-200">Drag and drop your video file here</p>
                <p className="text-sm text-zinc-500 font-medium">Or click anywhere to search directory</p>
                <p className="text-xs text-zinc-600 pt-4">Supports MP4, MOV, MKV, AVI (Max 4GB)</p>
              </div>
            )}
          </div>
          
          {file && (
            <button
              onClick={handleUploadAndAnalyze}
              disabled={uploading}
              className="w-full bg-gradient-to-r from-brand-violet via-brand-cyan to-brand-cyan text-dark-900 font-extrabold text-lg py-4 px-6 rounded-2xl shadow-xl hover:opacity-95 transform active:scale-[0.99] transition flex items-center justify-center space-x-3 glow-cyan"
            >
              {uploading ? (
                <>
                  <div className="h-5 w-5 border-2 border-dark-900 border-t-transparent rounded-full animate-spin"></div>
                  <span>Uploading video to engine ({uploadProgress}%)</span>
                </>
              ) : (
                <>
                  <Sparkles className="h-5 w-5 fill-dark-900" />
                  <span>Analyze & Extract Viral Clips</span>
                </>
              )}
            </button>
          )}

          {uploadError && (
            <p className="px-4 py-3 rounded-xl border border-rose-500/40 bg-rose-500/10 text-rose-300 text-sm font-medium break-words">
              {uploadError}
            </p>
          )}
        </div>

        {/* Processing Config Sidebar Panel */}
        <div className="glass-panel rounded-3xl p-6 border border-zinc-800 space-y-6">
          <div className="flex items-center space-x-2 pb-4 border-b border-zinc-800/80">
            <Settings2 className="h-5 w-5 text-brand-cyan" />
            <h3 className="font-bold text-zinc-200">Processing Variables</h3>
          </div>

          {/* Aspect Ratio Configurator */}
          <div className="space-y-3">
            <label className="text-xs text-zinc-400 font-bold uppercase tracking-wider">Target Aspect Ratio</label>
            <div className="grid grid-cols-3 gap-2">
              {[
                { label: "9:16", desc: "Shorts/TikTok" },
                { label: "16:9", desc: "YouTube" },
                { label: "1:1", desc: "Instagram" }
              ].map(opt => (
                <button
                  key={opt.label}
                  onClick={() => setAspectRatio(opt.label)}
                  className={`flex flex-col items-center justify-center p-3 rounded-xl border transition ${
                    aspectRatio === opt.label 
                      ? 'border-brand-cyan bg-brand-cyan/5 text-brand-cyan font-bold' 
                      : 'border-zinc-800 hover:border-zinc-700 text-zinc-400 hover:bg-zinc-800/30'
                  }`}
                >
                  <span className="text-sm">{opt.label}</span>
                  <span className="text-[9px] opacity-70 font-normal">{opt.desc}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Caption Burner Style selector */}
          <div className="space-y-3">
            <label className="text-xs text-zinc-400 font-bold uppercase tracking-wider">Subtitles Template</label>
            <div className="grid grid-cols-2 gap-2">
              {[
                { name: "TikTok", desc: "Bold, Yellow highlighted" },
                { name: "Meme", desc: "Classic Impact, red outline" }
              ].map(opt => (
                <button
                  key={opt.name}
                  onClick={() => setStyleName(opt.name)}
                  className={`flex flex-col items-start p-3.5 rounded-xl border transition text-left ${
                    styleName === opt.name 
                      ? 'border-brand-violet bg-brand-violet/5 text-brand-violet font-bold' 
                      : 'border-zinc-800 hover:border-zinc-700 text-zinc-400 hover:bg-zinc-800/30'
                  }`}
                >
                  <span className="text-sm">{opt.name}</span>
                  <span className="text-[9px] opacity-70 font-normal">{opt.desc}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Silence Detector Toggle */}
          <div className="space-y-3 pt-2">
            <label className="text-xs text-zinc-400 font-bold uppercase tracking-wider">Advanced Options</label>
            <div className="flex items-center justify-between p-4 rounded-xl bg-zinc-900/60 border border-zinc-800/80">
              <div className="flex items-center space-x-3">
                <VolumeX className="h-5 w-5 text-brand-cyan" />
                <div>
                  <p className="text-sm font-semibold text-zinc-200">Auto Silence Remover</p>
                  <p className="text-[10px] text-zinc-500">Stitch out gaps in speech</p>
                </div>
              </div>
              <input
                type="checkbox"
                checked={removeSilence}
                onChange={(e) => setRemoveSilence(e.target.checked)}
                className="w-4 h-4 rounded text-brand-cyan focus:ring-brand-cyan bg-zinc-800 border-zinc-700"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
