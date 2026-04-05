"use client";

import { useRouter, usePathname } from "next/navigation";
import { PlayCircle, CheckCircle, Lock, LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface CourseSidebarItemProps {
  label: string;
  id: string;
  isCompleted: boolean;
  courseId: string;
  isLocked: boolean;
  iconType: "play" | "check" | "lock";
}

export const CourseSidebarItem = ({
  label,
  id,
  isCompleted,
  courseId,
  isLocked,
  iconType,
}: CourseSidebarItemProps) => {
  const router = useRouter();
  const pathname = usePathname();

  const isActive = pathname.includes(id); // Check if current route matches the chapter id

  const handleClick = () => {
    if (!isLocked) {
      router.push(`/courses/${courseId}/chapters/${id}`);
    }
  };

  const Icon = {
    play: PlayCircle,
    check: CheckCircle,
    lock: Lock,
  }[iconType] as LucideIcon;

  return (
    <button
      type="button"
      onClick={handleClick}
      className={cn(
        "flex items-center gap-x-3 px-6 py-4 w-full text-left rounded-md transition-colors",
        "text-base font-medium",
        isLocked
          ? "text-gray-400 cursor-not-allowed"
          : isCompleted
            ? "text-emerald-700 bg-emerald-50 hover:bg-emerald-100"
            : isActive
              ? "bg-blue-100 text-blue-700 border-l-4 border-blue-600"
              : "text-slate-700 hover:bg-slate-200/20",
      )}
      disabled={isLocked}
    >
      <Icon size={24} className="flex-shrink-0" />
      <span className="truncate">{label}</span>
    </button>
  );
};
