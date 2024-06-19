// UploadSelector.tsx
"use client";

import { useState } from "react";
import { ChapterVideoForm } from "@/app/(dashboard)/(routes)/teacher/courses/[courseId]/chapters/[chapterId]/_components/chapter-video-form";
import { AttachmentForm } from "@/app/(dashboard)/(routes)/teacher/courses/[courseId]/_components/attachment-form";
import { IconBadge } from "@/components/icon-badge";
import { Video, File } from "lucide-react";
import { ChapterSlideForm } from "@/app/(dashboard)/(routes)/teacher/courses/[courseId]/chapters/[chapterId]/_components/chapter-slide-form";

interface UploadSelectorProps {
  courseId: string;
  chapterId: string;
  initialData: any; // Replace with your actual type
}

const UploadSelector: React.FC<UploadSelectorProps> = ({
  courseId,
  chapterId,
  initialData,
}) => {
  const [uploadType, setUploadType] = useState<"video" | "slides" | null>(null);

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-x-2">
        <IconBadge icon={Video} />
        <h2 className="text-xl font-semibold">Upload Type</h2>
      </div>
      <div className="flex space-x-4">
        <button
          onClick={() => setUploadType("video")}
          className={`px-6 py-3 rounded-lg shadow-md transition-all ${
            uploadType === "video"
              ? "bg-blue-500 text-white"
              : "bg-white border border-gray-300 text-black hover:bg-gray-100"
          }`}
        >
          Upload Video
        </button>
        <button
          onClick={() => setUploadType("slides")}
          className={`px-6 py-3 rounded-lg shadow-md transition-all ${
            uploadType === "slides"
              ? "bg-blue-500 text-white"
              : "bg-white border border-gray-300 text-black hover:bg-gray-100"
          }`}
        >
          Upload Slides/PDF
        </button>
      </div>
      {uploadType === "video" && (
        <div className="mt-4">
          <ChapterVideoForm
            initialData={initialData}
            courseId={courseId}
            chapterId={chapterId}
          />
        </div>
      )}
      {uploadType === "slides" && (
        <div className="mt-4">
          <ChapterSlideForm
            initialData={initialData}
            courseId={courseId}
            chapterId={chapterId}
          />
        </div>
      )}
    </div>
  );
};

export default UploadSelector;
