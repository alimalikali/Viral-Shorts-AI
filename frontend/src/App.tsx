import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import UploadZone from './components/UploadZone';
import Workspace from './components/Workspace';

export default function App() {
  const [backendOnline, setBackendOnline] = useState(false);
  const [jobId, setJobId] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);

  // Monitor Python AI Backend connection status
  useEffect(() => {
    const checkConnection = async () => {
      try {
        const res = await fetch("/api/health");
        if (res.ok) {
          setBackendOnline(true);
        } else {
          setBackendOnline(false);
        }
      } catch {
        setBackendOnline(false);
      }
    };

    checkConnection();
    // Re-verify server heartbeat every 5 seconds
    const interval = setInterval(checkConnection, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleStartProcessing = async (config: {
    videoPath: string;
    aspectRatio: string;
    styleName: string;
    removeSilence: boolean;
  }) => {
    setSubmitError(null);
    try {
      const response = await fetch("/api/process", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          video_path: config.videoPath,
          aspect_ratio: config.aspectRatio,
          style_name: config.styleName,
          remove_silence: config.removeSilence
        })
      });

      if (!response.ok) {
        const detail = await response.text();
        throw new Error(`Backend rejected the job (${response.status}): ${detail}`);
      }

      const data = await response.json();
      setJobId(data.job_id);
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : String(err));
    }
  };

  const handleReset = () => {
    setJobId(null);
    setSubmitError(null);
  };

  return (
    <div className="min-h-screen bg-dark-900 text-zinc-100 flex flex-col justify-between selection:bg-brand-cyan/20 select-none">
      <div className="flex-1 flex flex-col">
        {/* Glowing Headboard Navigation bar */}
        <Navbar backendOnline={backendOnline} />

        <main className="flex-1">
          {submitError && !jobId && (
            <div className="max-w-2xl mx-auto mt-6 px-4 py-3 rounded-xl border border-rose-500/40 bg-rose-500/10 text-rose-300 text-sm font-medium">
              {submitError}
            </div>
          )}
          {jobId ? (
            <Workspace jobId={jobId} onReset={handleReset} />
          ) : (
            <UploadZone onStartProcessing={handleStartProcessing} />
          )}
        </main>
      </div>
      
      {/* Visual bottom dark board footer */}
      <footer className="py-5 border-t border-zinc-900 text-center text-[10px] text-zinc-600 font-medium">
        <span>Licensed under MIT Open Source • Self-Hosted Local Server • GPU Cuda Acceleration Supported</span>
      </footer>
    </div>
  );
}
