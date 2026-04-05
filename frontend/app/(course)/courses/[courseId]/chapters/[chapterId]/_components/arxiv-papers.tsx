import React from 'react';

interface ArxivPaper {
  title: string;
  link: string;
}

interface ArxivPapersProps {
  papers: ArxivPaper[];
}

export const ArxivPapers: React.FC<ArxivPapersProps> = ({ papers }) => {
  return (
    <div>
      {papers.map((paper, index) => (
        <div key={index} className="mb-2">
          <a href={paper.link} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
            {paper.title}
          </a>
        </div>
      ))}
    </div>
  );
};
