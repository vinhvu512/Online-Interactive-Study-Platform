import axios from 'axios';

const MAX_RETRIES = 3;
const RETRY_DELAY = 1000; // 1 second

async function fetchWithRetry(url: string, retries = MAX_RETRIES): Promise<Buffer> {
  try {
    const response = await axios.get(url, { responseType: 'arraybuffer', timeout: 5000 });
    return Buffer.from(response.data, 'binary');
  } catch (error) {
    if (retries > 0) {
      console.log(`Retrying image fetch for ${url}. Attempts left: ${retries - 1}`);
      await new Promise(resolve => setTimeout(resolve, RETRY_DELAY));
      return fetchWithRetry(url, retries - 1);
    }
    throw error;
  }
}

export default function imageLoader({ src, width, quality }: { src: string, width: number, quality?: number }) {
  return `${process.env.NEXT_PUBLIC_APP_URL}/api/imageProxy?url=${encodeURIComponent(src)}&w=${width}&q=${quality || 75}`;
}

export { fetchWithRetry };