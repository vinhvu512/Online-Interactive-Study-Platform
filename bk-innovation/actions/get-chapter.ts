// @ts-ignore
import { db } from "@/lib/db";
import { Attachments, Chapter } from "@prisma/client";

interface GetChapterProps {
  userId: string;
  courseId: string;
  chapterId: string;
}

export const getChapter = async ({
  userId,
  courseId,
  chapterId,
}: GetChapterProps) => {
  try {
    const course = await db.course.findUnique({
      where: {
        id: courseId,
        isPublished: true,
      },
    });

    const chapter = await db.chapter.findUnique({
      where: {
        id: chapterId,
        isPublished: true,
      },
    });

    if (!chapter || !course) {
      throw new Error("Chapter or Course not found");
    }

    let muxData = null;
    let attachments: Attachments[] = [];
    let nextChapter: Chapter | null = null;

    attachments = await db.attachments.findMany({
      where: {
        courseId: courseId,
      },
    });

    if (chapter.isFree) {
      muxData = await db.muxData.findUnique({
        where: {
          chapterId: chapter.id,
        },
      });

      nextChapter = await db.chapter.findFirst({
        where: {
          courseId,
          isPublished: true,
          position: {
            gt: chapter?.position,
          },
        },
        orderBy: {
          position: "asc",
        },
      });
    }

    const userProgress = await db.userProgress.findUnique({
      where: {
        userId_chapterId: {
          userId,
          chapterId,
        },
      },
    });

    const parsedMultipleChoice = typeof chapter.multipleChoice === 'string' ? JSON.parse(chapter.multipleChoice) : chapter.multipleChoice;
    const parsedArxivPapers = typeof chapter.arxivPapers === 'string' ? JSON.parse(chapter.arxivPapers) : chapter.arxivPapers;

    return {
      chapter: {
        ...chapter,
        multipleChoice: parsedMultipleChoice,
        arxivPapers: parsedArxivPapers,
      },
      course,
      muxData,
      attachments,
      nextChapter,
      userProgress,
    };
  } catch (error) {
    console.log("[GET_CHAPTER]", error);
    return {
      chapter: null,
      course: null,
      muxData: null,
      attachments: [],
      nextChapter: null,
      userProgress: null,
    };
  }
};
