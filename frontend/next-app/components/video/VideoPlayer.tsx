"use client";

import * as React from "react";
import { Play, Pause, Volume2, VolumeX, Maximize, RotateCcw, Captions } from "lucide-react";
import { cn, formatClock } from "@/lib/format";
import VideoInteractionOverlay from "@/components/video/VideoInteractionOverlay";
import type { VideoInteractionEvent } from "@/types/interaction";

export interface VideoPlayerHandle {
  seekTo: (seconds: number) => void;
  play: () => void;
  pause: () => void;
}

interface VideoPlayerProps {
  src?: string | null;
  poster?: string;
  captionsSrc?: string;
  onTimeUpdate?: (current: number) => void;
  onReady?: () => void;
  onPlayChange?: (playing: boolean) => void;
  autoPlay?: boolean;
  className?: string;
  ariaLabel?: string;
  enableCaptions?: boolean;
  onCaptionsToggle?: (on: boolean) => void;
  /** When true the video element is muted and an overlay badge is shown. */
  audioMuted?: boolean;
  /** Small translucent label shown in the top-right corner when audio is muted externally. */
  overlayBadge?: string;
  /** Synchronized creative interaction events */
  interactionEvents?: VideoInteractionEvent[];
  /** Whether the interactive layer is initially active */
  enableInteractiveLayer?: boolean;
  /** Callback when an interaction event triggers or is clicked */
  onInteractionAction?: (event: VideoInteractionEvent) => void;
}

export const VideoPlayer = React.forwardRef<VideoPlayerHandle, VideoPlayerProps>(function VideoPlayer(
  {
    src,
    captionsSrc,
    onTimeUpdate,
    onReady,
    onPlayChange,
    autoPlay = false,
    className,
    ariaLabel = "Lecture video",
    enableCaptions = false,
    onCaptionsToggle,
    audioMuted = false,
    overlayBadge,
    interactionEvents = [],
    enableInteractiveLayer = true,
    onInteractionAction,
  },
  ref
) {
  const videoRef = React.useRef<HTMLVideoElement>(null);
  const [playing, setPlaying] = React.useState(false);
  const [current, setCurrent] = React.useState(0);
  const [duration, setDuration] = React.useState(0);
  const [userMuted, setUserMuted] = React.useState(false);
  const [ccOn, setCcOn] = React.useState(true);
  const [ready, setReady] = React.useState(false);
  const [interactiveEnabled, setInteractiveEnabled] = React.useState(enableInteractiveLayer);
  const effectiveMuted = audioMuted || userMuted;

  React.useEffect(() => {
    const syncCaptions = (event: Event) => {
      const detail = (event as CustomEvent<{ captions?: boolean }>).detail;
      if (typeof detail?.captions !== "boolean") return;
      setCcOn(detail.captions);
      const track = videoRef.current?.textTracks[0];
      if (track) track.mode = detail.captions ? "showing" : "hidden";
    };
    window.addEventListener("eduaccess:accessibility_update", syncCaptions);
    try {
      const stored = localStorage.getItem("eduaccess_accessibility_settings");
      if (stored) syncCaptions(new CustomEvent("eduaccess:accessibility_update", { detail: JSON.parse(stored) }));
    } catch { /* Preferences are optional. */ }
    return () => window.removeEventListener("eduaccess:accessibility_update", syncCaptions);
  }, []);

  React.useImperativeHandle(ref, () => ({
    seekTo: (seconds: number) => {
      if (videoRef.current) {
        videoRef.current.currentTime = seconds;
        setCurrent(seconds);
      }
    },
    play: () => videoRef.current?.play().catch(() => {}),
    pause: () => videoRef.current?.pause(),
  }));

  // Keep the <video> element in sync with the effective mute state.
  React.useEffect(() => {
    if (videoRef.current) videoRef.current.muted = effectiveMuted;
  }, [effectiveMuted]);

  const togglePlay = () => {
    const v = videoRef.current;
    if (!v) return;
    if (v.paused) v.play().catch(() => {});
    else v.pause();
  };

  const handleTime = () => {
    const v = videoRef.current;
    if (!v) return;
    setCurrent(v.currentTime);
    onTimeUpdate?.(v.currentTime);
  };

  const handleLoaded = () => {
    const v = videoRef.current;
    if (v) {
      setDuration(v.duration || 0);
      setReady(true);
      onReady?.();
    }
  };

  const handlePlay = () => {
    setPlaying(true);
    onPlayChange?.(true);
  };
  const handlePause = () => {
    setPlaying(false);
    onPlayChange?.(false);
  };

  const seek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const v = videoRef.current;
    if (!v) return;
    const t = Number(e.target.value);
    v.currentTime = t;
    setCurrent(t);
  };

  const toggleCaptions = () => {
    setCcOn((c) => {
      const n = !c;
      if (videoRef.current) videoRef.current.textTracks[0] && (videoRef.current.textTracks[0].mode = n ? "showing" : "hidden");
      onCaptionsToggle?.(n);
      return n;
    });
  };

  const [speed, setSpeed] = React.useState(1.0);
  const SPEEDS = [0.75, 1.0, 1.25, 1.5, 2.0];

  const handleSpeedChange = (nextSpeed: number) => {
    setSpeed(nextSpeed);
    if (videoRef.current) {
      videoRef.current.playbackRate = nextSpeed;
    }
  };

  const cycleSpeed = () => {
    const currentIdx = SPEEDS.indexOf(speed);
    const nextIdx = (currentIdx + 1) % SPEEDS.length;
    handleSpeedChange(SPEEDS[nextIdx]);
  };

  if (!src) {
    return (
      <div
        className={cn(
          "flex aspect-video w-full items-center justify-center rounded-2xl border border-app-edge bg-slate-100 text-app-muted",
          className
        )}
      >
        No video available.
      </div>
    );
  }

  const pct = duration ? (current / duration) * 100 : 0;

  return (
    <div className={cn("group relative flex flex-col overflow-hidden rounded-2xl border border-app-edge bg-black shadow-sm", className)}>
      <video
        ref={videoRef}
        src={src}
        className="aspect-video w-full"
        onTimeUpdate={handleTime}
        onLoadedMetadata={handleLoaded}
        onPlay={handlePlay}
        onPause={handlePause}
        onEnded={() => setPlaying(false)}
        onClick={togglePlay}
        aria-label={ariaLabel}
        preload="metadata"
      >
        {captionsSrc && <track ref={(el) => { if (el) {
          el.addEventListener("load", () => {
          if (videoRef.current?.textTracks[0]) videoRef.current.textTracks[0].mode = ccOn ? "showing" : "hidden";
          });
        } }} kind="captions" src={captionsSrc} label="Captions" default />}
      </video>

      <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
        {!playing && (
          <button
            onClick={togglePlay}
            aria-label="Play"
            className="pointer-events-auto flex size-16 items-center justify-center rounded-full bg-black/40 text-white ring-1 ring-white/40 backdrop-blur transition hover:scale-105 hover:bg-brand-purple/90"
          >
            <Play className="ml-1 size-7" aria-hidden />
          </button>
        )}
      </div>

      {/* Creative Video Interaction Layer */}
      {interactionEvents.length > 0 && (
        <VideoInteractionOverlay
          currentTime={current}
          playing={playing}
          events={interactionEvents}
          enabled={interactiveEnabled}
          onToggleEnabled={setInteractiveEnabled}
          onEventAction={onInteractionAction}
        />
      )}

      {overlayBadge && (
        <span className="pointer-events-none absolute right-3 top-3 z-10 rounded-md bg-black/60 px-2 py-1 text-[11px] font-semibold uppercase tracking-wider text-white shadow ring-1 ring-white/20 backdrop-blur">
          {overlayBadge}
        </span>
      )}

      <div className="flex items-center gap-2 bg-slate-900/95 px-3 py-2 text-white">
        <button onClick={togglePlay} aria-label={playing ? "Pause" : "Play"} className="text-slate-200 hover:text-white">
          {playing ? <Pause className="size-4" aria-hidden /> : <Play className="size-4" aria-hidden />}
        </button>
        <button
          onClick={() => {
            const v = videoRef.current;
            if (v) {
              v.currentTime = 0;
              setCurrent(0);
            }
          }}
          aria-label="Restart"
          className="text-slate-200 hover:text-white"
        >
          <RotateCcw className="size-4" aria-hidden />
        </button>

        <span className="w-24 text-center text-xs tabular-nums text-slate-300">
          {formatClock(current)} / {formatClock(duration)}
        </span>

        <input
          type="range"
          min={0}
          max={duration || 0}
          step={0.1}
          value={current}
          onChange={seek}
          aria-label="Seek"
          className="h-1.5 flex-1 cursor-pointer appearance-none rounded-full bg-slate-700 accent-brand-indigo"
          style={{
            background: `linear-gradient(to right, #6C4FF7 ${pct}%, #334155 ${pct}%)`,
          }}
        />

        {/* Playback Speed Selector */}
        <button
          onClick={cycleSpeed}
          title="Change playback speed"
          aria-label={`Playback speed ${speed}x`}
          className="rounded px-1.5 py-0.5 font-mono text-xs font-semibold text-slate-300 transition hover:bg-white/10 hover:text-white"
        >
          {speed}x
        </button>

        {enableCaptions && (
          <button
            onClick={toggleCaptions}
            aria-pressed={ccOn}
            aria-label={ccOn ? "Disable captions" : "Enable captions"}
            className={cn("rounded-md p-1 transition", ccOn ? "text-brand-cyan" : "text-slate-300 hover:text-white")}
          >
            <Captions className="size-4" aria-hidden />
          </button>
        )}

        <button
          onClick={() => setUserMuted((m) => !m)}
          aria-label={effectiveMuted
            ? (audioMuted ? "Lecture audio is currently muted externally." : "Unmute")
            : "Mute"}
          className="text-slate-200 hover:text-white"
        >
          {effectiveMuted ? <VolumeX className="size-4" aria-hidden /> : <Volume2 className="size-4" aria-hidden />}
        </button>
        <button
          onClick={() => videoRef.current?.requestFullscreen?.().catch(() => {})}
          aria-label="Fullscreen"
          className="text-slate-200 hover:text-white"
        >
          <Maximize className="size-4" aria-hidden />
        </button>
      </div>
      {!ready && <span className="sr-only">Video loading</span>}
    </div>
  );
});
