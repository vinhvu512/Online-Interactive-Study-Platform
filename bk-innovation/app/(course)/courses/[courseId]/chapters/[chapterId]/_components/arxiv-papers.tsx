import React from 'react';

interface Paper {
  title: string;
  url: string;
}

interface ArxivPapersProps {
  papers: Paper[];
}

export const ArxivPapers: React.FC<ArxivPapersProps> = ({ papers }) => {
  return (
    <div>
      {papers.map((paper, index) => (
        <div key={index} className="mb-2">
          <a href={paper.url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
            {paper.title}
          </a>
        </div>
      ))}
    </div>
  );
};
