import { db } from "@/lib/db";

export const getChaptersByCourseId = async (courseId: string) => {
  try {
    const chapters = await db.chapter.findMany({
      where: {
        courseId,
        isPublished: true,
      },
      orderBy: {
        position: "asc", // Assuming you want to order chapters by their position
      },
    });
    return chapters;
  } catch (error) {
    console.error("Error fetching chapters:", error);
    return [];
  }
};
