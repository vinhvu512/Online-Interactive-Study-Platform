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
      <div className="flex flex-col max-w-4xl mx-auto pb-20">
        <div className="p-2.5 mt-20">
          {!chapter.videoUrl.includes("utfs.io") ? (
            <div className="relative aspect-video rounded-lg shadow-lg overflow-hidden bg-gray-900">
              <video
                controls
                src={chapter.videoUrl}
                className="w-full h-full object-cover"
                style={{ borderRadius: "0.5rem" }}
              ></video>
            </div>
          ) : (
            <VideoPlayer
              chapterId={params.chapterId}
              title={chapter.title}
              courseId={params.courseId}
              nextChapterId={nextChapter?.id}
              playbackId={muxData?.playbackId!}
              isLocked={false}
              completeOnEnd={completeOnEnd}
            />
          )}
        </div>
      </div>
    </div>
  );
};

export default ChapterIdPage;
