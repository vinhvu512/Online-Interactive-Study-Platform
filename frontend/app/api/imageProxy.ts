import { NextApiRequest, NextApiResponse } from 'next';
import { fetchWithRetry } from '../../utils/imageLoader';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  const { url, w, q } = req.query;

  if (typeof url !== 'string') {
    return res.status(400).json({ error: 'Invalid URL' });
  }

  try {
    const imageBuffer = await fetchWithRetry(url);
    res.setHeader('Content-Type', 'image/png');
    res.send(imageBuffer);
  } catch (error) {
    console.error('Error fetching image:', error);
    res.status(500).json({ error: 'Failed to fetch image' });
  }
}