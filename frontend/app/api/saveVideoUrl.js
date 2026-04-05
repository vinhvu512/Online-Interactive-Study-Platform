import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

export default async function handler(req, res) {
  if (req.method === 'PATCH') {
    const { chapterId, videoUrl } = req.body;

    try {
      // Update the chapter with the video URL
      await prisma.chapter.update({
        where: { id: chapterId },
        data: { videoUrl },
      });

      res.status(200).json({ message: 'Video URL saved successfully' });
    } catch (error) {
      console.error('Error saving video URL:', error);
      res.status(500).json({ error: 'Failed to save video URL' });
    }
  } else {
    res.setHeader('Allow', ['PATCH']);
    res.status(405).end(`Method ${req.method} Not Allowed`);
  }
}
