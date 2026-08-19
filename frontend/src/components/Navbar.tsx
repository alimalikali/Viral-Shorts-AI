import React from 'react';
import { Clapperboard, Circle } from 'lucide-react';

interface NavbarProps {
  backendOnline: boolean;
}

export default function Navbar({ backendOnline }: NavbarProps) {
  return (
    <header className="border-b border-zinc-900 bg-dark-900/80 backdrop-blur sticky top-0 z-30">
      <div className="max-w-6xl mx-auto flex items-center justify-between px-6 py-3">
        <div className="flex items-center space-x-2">
          <div className="p-1.5 rounded-lg bg-gradient-to-br from-brand-violet to-brand-cyan">
            <Clapperboard className="h-4 w-4 text-dark-900" strokeWidth={2.5} />
          </div>
          <span className="text-sm font-extrabold tracking-tight text-zinc-100">
            Viral Shorts <span className="text-brand-cyan">AI</span>
          </span>
        </div>

        <div
          className={`flex items-center space-x-1.5 text-[10px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-full border ${
            backendOnline
              ? 'text-emerald-400 border-emerald-500/30 bg-emerald-500/5'
              : 'text-zinc-500 border-zinc-800 bg-zinc-900/40'
          }`}
        >
          <Circle
            className={`h-2 w-2 ${backendOnline ? 'fill-emerald-400 text-emerald-400' : 'fill-zinc-600 text-zinc-600'}`}
          />
          <span>{backendOnline ? 'Backend Online' : 'Backend Offline'}</span>
        </div>
      </div>
    </header>
  );
}
