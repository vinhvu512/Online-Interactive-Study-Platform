import { NextRequest, NextResponse } from 'next/server';
import { db } from "@/lib/db"; // Make sure this is correctly set up and points to your Prisma client

export async function POST(req: NextRequest) {
  try {
    // Parse the JSON body
    const { chapterId, videoUrl } = await req.json();

    // Validate request body
    if (!chapterId || !videoUrl) {
      return NextResponse.json({ error: 'Chapter ID and Video URL are required' }, { status: 400 });
    }

    // Update the chapter with the new video URL
    const updatedChapter = await db.chapter.update({
      where: { id: chapterId },
      data: { videoUrl },
    });

    return NextResponse.json({ message: 'Video URL updated successfully', updatedChapter });
  } catch (error) {
    console.error('Error updating video URL:', error);
    return NextResponse.json({ error: 'Failed to update video URL' }, { status: 500 });
  }
}
