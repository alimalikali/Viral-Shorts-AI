import React, { useState } from 'react';
import { Copy, Check, TrendingUp, Award } from 'lucide-react';
import { Clip } from './Workspace';

interface ViralMetricsProps {
  clip: Clip;
}

export default function ViralMetrics({ clip }: ViralMetricsProps) {
  const [copiedField, setCopiedField] = useState<string | null>(null);

  const copyToClipboard = (text: string, field: string) => {
    navigator.clipboard.writeText(text);
    setCopiedField(field);
    setTimeout(() => setCopiedField(null), 1500);
  };

  return (
    <div className="space-y-6 animate-slide-up">
      {/* Viral Score Circular Bar */}
      <div className="bg-zinc-900/40 border border-zinc-800 p-4 rounded-2xl flex items-center justify-between shadow">
        <div className="space-y-1">
          <p className="text-xs text-zinc-500 font-bold uppercase tracking-wider">Viral Score Index</p>
          <h3 className="text-2xl font-black text-white flex items-center space-x-1.5">
            <span>{clip.viral_score} / 100</span>
            <TrendingUp className="h-5 w-5 text-emerald-400 stroke-[2.5]" />
          </h3>
          <p className="text-[10px] text-zinc-400 font-medium">Rating: <strong className="text-brand-cyan">{clip.engagement_rating} Engagement</strong></p>
        </div>
        
        {/* Glow Rating circle */}
        <div className="relative h-16 w-16 flex items-center justify-center">
          <svg className="h-16 w-16 transform -rotate-90">
            <circle cx="32" cy="32" r="28" className="stroke-zinc-800" strokeWidth="4" fill="transparent" />
            <circle
              cx="32"
              cy="32"
              r="28"
              className="stroke-brand-cyan"
              strokeWidth="4"
              fill="transparent"
              strokeDasharray={2 * Math.PI * 28}
              strokeDashoffset={2 * Math.PI * 28 * (1 - clip.viral_score / 100)}
            />
          </svg>
          <span className="absolute text-[11px] font-black text-zinc-200">{clip.retention_prediction}</span>
        </div>
      </div>

      {/* Suggested Hook descriptions */}
      <div className="space-y-1.5">
        <label className="text-[10px] text-zinc-500 font-bold uppercase tracking-wider">Engagement Hook Trigger</label>
        <div className="p-3 bg-zinc-900/60 border border-zinc-800/80 rounded-xl flex items-start space-x-2.5">
          <Award className="h-4 w-4 text-brand-violet mt-0.5 shrink-0" />
          <div>
            <p className="text-xs font-bold text-zinc-200">{clip.hook_type}</p>
            <p className="text-[10px] text-zinc-500 font-medium mt-0.5">Scored higher due to reaction intensity and hook words.</p>
          </div>
        </div>
      </div>

      {/* Suggest title copies */}
      <div className="space-y-4 pt-2 border-t border-zinc-800/60">
        
        <div className="space-y-1.5">
          <div className="flex justify-between items-center">
            <label className="text-[10px] text-zinc-500 font-bold uppercase tracking-wider">Suggested Short Title</label>
            <button
              onClick={() => copyToClipboard(clip.suggested_title, "title")}
              className="text-zinc-500 hover:text-zinc-300 text-[10px] font-semibold flex items-center space-x-1"
            >
              {copiedField === "title" ? <Check className="h-3 w-3 text-emerald-400" /> : <Copy className="h-3 w-3" />}
              <span>{copiedField === "title" ? "Copied!" : "Copy"}</span>
            </button>
          </div>
          <div className="bg-zinc-900/40 border border-zinc-800/80 p-3 rounded-xl text-xs font-bold text-zinc-200 leading-relaxed">
            {clip.suggested_title}
          </div>
        </div>

        <div className="space-y-1.5">
          <div className="flex justify-between items-center">
            <label className="text-[10px] text-zinc-500 font-bold uppercase tracking-wider">Suggested Caption</label>
            <button
              onClick={() => copyToClipboard(clip.suggested_caption, "caption")}
              className="text-zinc-500 hover:text-zinc-300 text-[10px] font-semibold flex items-center space-x-1"
            >
              {copiedField === "caption" ? <Check className="h-3 w-3 text-emerald-400" /> : <Copy className="h-3 w-3" />}
              <span>{copiedField === "caption" ? "Copied!" : "Copy"}</span>
            </button>
          </div>
          <div className="bg-zinc-900/40 border border-zinc-800/80 p-3 rounded-xl text-xs text-zinc-300 leading-relaxed">
            {clip.suggested_caption}
          </div>
        </div>

        <div className="space-y-1.5">
          <div className="flex justify-between items-center">
            <label className="text-[10px] text-zinc-500 font-bold uppercase tracking-wider">Optimized Hashtags</label>
            <button
              onClick={() => copyToClipboard(clip.suggested_hashtags, "tags")}
              className="text-zinc-500 hover:text-zinc-300 text-[10px] font-semibold flex items-center space-x-1"
            >
              {copiedField === "tags" ? <Check className="h-3 w-3 text-emerald-400" /> : <Copy className="h-3 w-3" />}
              <span>{copiedField === "tags" ? "Copied!" : "Copy"}</span>
            </button>
          </div>
          <div className="bg-zinc-900/40 border border-zinc-800/80 p-3 rounded-xl text-xs text-brand-cyan font-semibold leading-relaxed">
            {clip.suggested_hashtags}
          </div>
        </div>

      </div>
    </div>
  );
}
