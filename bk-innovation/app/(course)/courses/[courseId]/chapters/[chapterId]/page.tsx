import { auth } from "@clerk/nextjs/server";
import { redirect } from "next/navigation";
// @ts-ignore
import { db } from "@/lib/db";
// @ts-ignore
import { getChapter } from "@/actions/get-chapter";
// @ts-ignore
import { Banner } from "@/components/banner";
// @ts-ignore
import { VideoPlayer } from "@/app/(course)/courses/[courseId]/chapters/[chapterId]/_components/video-player";
import { CourseEnrollButton } from "@/app/(course)/courses/[courseId]/chapters/[chapterId]/_components/course-enroll-button";
import { Separator } from "@/components/ui/separator";
import { Preview } from "@/components/preview";
import { File } from "lucide-react";
import { CourseProgressButton } from "@/app/(course)/courses/[courseId]/chapters/[chapterId]/_components/course-progress-button";
import { ChainlitChatbot } from "@/app/(course)/courses/[courseId]/chapters/[chapterId]/_components/chainlit-chatbot";

interface ChapterIdPageProps {
  params: {
    courseId: string;
    chapterId: string;
  };
}

const ChapterIdPage = async ({ params }: ChapterIdPageProps) => {
  const { userId } = auth();

  if (!userId) {
    return redirect("/");
  }

  const { chapter, course, muxData, attachments, nextChapter, userProgress } =
    await getChapter({
      userId,
      chapterId: params.chapterId,
      courseId: params.courseId,
    });

  if (!chapter || !course) {
    return redirect("/");
  }

  // const isLocked = !chapter.isFree;
  const completeOnEnd = !userProgress?.isCompleted;
  return (
    <div>
      {userProgress?.isCompleted && (
        <Banner variant="success" label="You already completed this chapter." />
      )}
      {/*{isLocked && (*/}
      {/*  <Banner*/}
      {/*    variant="warning"*/}
      {/*    label="You need to purchase this course to watch this chapter. "*/}
      {/*  />*/}
      {/*)}*/}
      <div className="flex flex-col max-w-6xl mx-auto pb-20">
        <div className="p-2.5 mt-20">
          {chapter.videoUrl && !chapter.videoUrl.includes("utfs.io") ? (
            <div className="relative aspect-video rounded-lg shadow-lg overflow-hidden bg-gray-900">
              <video
                controls
                src={chapter.videoUrl}
                className="w-full h-full"
                style={{ borderRadius: "0.5rem" }}
              ></video>
            </div>
          ) : (
            <div className="p-4">
              <VideoPlayer
                chapterId={params.chapterId}
                title={chapter.title}
                courseId={params.courseId}
                nextChapterId={nextChapter?.id}
                playbackId={muxData?.playbackId!}
                isLocked={false}
                completeOnEnd={completeOnEnd}
              />
            </div>
          )}
          
          <div>
            <div className="p-4 flex flex-col md:flex-row items-center justify-between">
              <h2 className="text-2xl font-semibold mb-2">{chapter.title}</h2>
              {chapter.isFree ? (
                <CourseProgressButton
                  chapterId={params.chapterId}
                  courseId={params.courseId}
                  nextChapterId={nextChapter?.id}
                  isCompleted={!!userProgress?.isCompleted}
                />
              ) : (
                <CourseEnrollButton
                // courseId={params.courseId}
                // price={course.price!}
                />
              )}
            </div>
            <Separator />
            <div>
              <Preview value={chapter.description!} />
            </div>
            {!!attachments.length && (
              <>
                <Separator />
                <div className="p-4">
                  {attachments.map((attachment) => (
                    <a
                      href={attachment.url}
                      target="_blank"
                      key={attachment.id}
                      className="flex items-center p-3 w-full bg-sky-200 border text-sky-700 rounded-md hover:underline"
                    >
                      <File />
                      <p className="line-clamp-1">{attachment.name}</p>
                    </a>
                  ))}
                </div>
              </>
            )}
          </div>
          <ChainlitChatbot />
        </div>
      </div>
    </div>
  );
};

export default ChapterIdPage;