"use client";
import React, { useState, useEffect } from "react";
import { Loader2, Zap, ExternalLink } from "lucide-react";

/** Set NEXT_PUBLIC_CHAINLIT_URL in bk-innovation/.env if Chainlit is not on localhost:8501 */
const chainlitBase = (
  process.env.NEXT_PUBLIC_CHAINLIT_URL ?? "http://localhost:8501"
).replace(/\/$/, "");

export const ChainlitChatbot = () => {
  const [iframeLoaded, setIframeLoaded] = useState(false);
  const [reachable, setReachable] = useState<boolean | null>(null);

  useEffect(() => {
    const timer = setTimeout(() => setIframeLoaded(true), 800);
    return () => clearTimeout(timer);
  }, []);

  useEffect(() => {
    let cancelled = false;
    fetch(`${chainlitBase}/health`)
      .then((r) => {
        if (!cancelled) setReachable(r.ok);
      })
      .catch(() => {
        if (!cancelled) setReachable(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="mt-8 border rounded-xl overflow-hidden shadow-lg transition-all duration-300 hover:shadow-xl">
      <div className="bg-gradient-to-r from-purple-600 via-blue-500 to-indigo-400 text-white p-6 relative">
        <div className="absolute top-0 left-0 w-full h-full bg-black opacity-10 z-0"></div>
        <div className="relative z-10">
          <h2 className="text-2xl font-bold flex items-center mb-2">
            <Zap className="mr-3" size={28} />
            AI Lecture Assistant
          </h2>
          <p className="text-sm opacity-90">
            Powered by advanced AI, this assistant enhances your learning experience. Ask questions, seek clarifications, or explore topics further!
          </p>
          <p className="mt-3 text-sm">
            <a
              href={chainlitBase}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 underline font-medium text-white/95 hover:text-white"
            >
              Open assistant in a new tab
              <ExternalLink className="h-3.5 w-3.5" />
            </a>
          </p>
        </div>
      </div>
      {reachable === false && (
        <div className="bg-amber-50 border-b border-amber-200 text-amber-950 px-4 py-3 text-sm">
          <strong className="font-semibold">Chainlit is not reachable</strong> at{" "}
          <code className="rounded bg-amber-100 px-1">{chainlitBase}</code>. Start it from the
          repo:{" "}
          <code className="rounded bg-amber-100 px-1">
            cd tes &amp;&amp; chainlit run chatbot.py --port 8501
          </code>
          . The area below stays blank until the server is running (use the link above to verify).
        </div>
      )}
      {iframeLoaded ? (
        <iframe
          title="AI Lecture Assistant"
          src={chainlitBase}
          width="100%"
          height="600px"
          style={{ border: "none" }}
          className="block w-full bg-white transition-opacity duration-500 ease-in-out"
        />
      ) : (
        <div className="flex flex-col justify-center items-center h-[600px] bg-gradient-to-b from-gray-50 to-gray-100">
          <Loader2 className="h-10 w-10 text-blue-600 animate-spin mb-4" />
          <p className="text-gray-600 font-medium">Initializing AI Assistant...</p>
          <p className="text-sm text-gray-400 mt-2">Preparing neural networks</p>
        </div>
      )}
    </div>
  );
};