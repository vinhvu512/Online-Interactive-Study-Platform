import { Chapter, Course, UserProgress } from "@prisma/client";
import { redirect } from "next/navigation";
import { auth } from "@clerk/nextjs/server";
import { CourseSidebarItem } from "@/app/(course)/courses/[courseId]/_components/course-sidebar-item";

interface CourseSidebarProps {
  course: Course & {
    chapters: (Chapter & {
      userProgress: UserProgress[];
    })[];
  };
  progressCount: number;
}

export const CourseSidebar = ({
  course,
  progressCount,
}: CourseSidebarProps) => {
  const { userId } = auth();
  if (!userId) {
    return redirect("/");
  }

  return (
    <div className="h-full border-r flex flex-col overflow-y-auto shadow-sm bg-white">
      <div className="p-6 flex flex-col border-b bg-gray-100">
        <h1 className="font-semibold text-xl mb-2">{course.title}</h1>
        <p className="text-sm text-gray-600">
          Progress: <span className="font-medium">{progressCount}%</span>
        </p>
      </div>
      <div className="flex flex-col w-full px-2 py-4 space-y-2">
        {course.chapters.map((chapter) => {
          const isCompleted = chapter.userProgress?.some(
            (up) => up.isCompleted,
          );
          // const isLocked = !chapter.isFree && !isCompleted;

          return (
            <CourseSidebarItem
              key={chapter.id}
              id={chapter.id}
              label={chapter.title}
              isCompleted={isCompleted}
              courseId={course.id}
              isLocked={false}
              iconType={isCompleted ? "check" : "play"}
            />
          );
        })}
        {course.chapters.length === 0 && (
          <div className="text-center text-sm text-gray-500 mt-10">
            No chapters found
          </div>
        )}
      </div>
    </div>
  );
};
