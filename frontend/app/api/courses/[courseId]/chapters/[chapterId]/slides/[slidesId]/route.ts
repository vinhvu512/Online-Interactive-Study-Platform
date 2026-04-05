import { auth } from "@clerk/nextjs/server";
import { NextResponse } from "next/server";
import { db } from "@/lib/db";

export async function DELETE(
  req: Request,
  { params }: { params: { courseId: string; slideId: string } },
) {
  try {
    const { userId } = auth();

    if (!userId) {
      return new NextResponse("Unauthorized", { status: 401 });
    }

    const slide = await db.attachments.delete({
      where: {
        courseId: params.courseId,
        id: params.slideId,
      },
    });

    return NextResponse.json(slide);
  } catch (error) {
    console.log("SLIDE_ID", error);
    return new NextResponse("Internal Error", { status: 500 });
  }
}
