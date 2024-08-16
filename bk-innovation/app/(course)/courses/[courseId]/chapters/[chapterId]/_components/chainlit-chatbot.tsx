"use client";
import React, { useState, useEffect } from 'react';
import { MessageCircle, Loader2, Zap } from 'lucide-react';

const CHAINLIT_SERVER_URL = 'http://localhost:8501';

export const ChainlitChatbot = () => {
  const [iframeLoaded, setIframeLoaded] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setIframeLoaded(true), 1500);
    return () => clearTimeout(timer);
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
        </div>
      </div>
      {iframeLoaded ? (
        <iframe
          src={CHAINLIT_SERVER_URL}
          width="100%"
          height="600px"
          style={{ border: 'none' }}
          className="transition-opacity duration-500 ease-in-out"
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