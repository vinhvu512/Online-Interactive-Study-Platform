"use client";
import React, { useState } from 'react';

interface Question {
  question: string;
  options: string[];
  answer: string;
}

interface MultipleChoiceQuestionsProps {
  questions: Question[];
}

export const MultipleChoiceQuestions: React.FC<MultipleChoiceQuestionsProps> = ({ questions }) => {
  const [userAnswers, setUserAnswers] = useState<{ [key: number]: string | null }>({});
  const [feedback, setFeedback] = useState<{ [key: number]: boolean | null }>({});

  const handleAnswer = (questionIndex: number, selectedOption: string) => {
    setUserAnswers(prev => ({ ...prev, [questionIndex]: selectedOption }));
    const isCorrect = selectedOption === questions[questionIndex].answer;
    setFeedback(prev => ({ ...prev, [questionIndex]: isCorrect }));
  };

  const questionsArray = Array.isArray(questions) ? questions : [];
  const validQuestions = questionsArray.filter(q => 
    q && typeof q === 'object' && Array.isArray(q.options) && q.options.length > 0
  );

  if (validQuestions.length === 0) {
    return null;
  }

  return (
    <div>
      {validQuestions.map((q, index) => (
        <div key={index} className="mb-6 border-b pb-4">
          <p className="font-semibold text-lg mb-2">{q.question}</p>
          <ul className="list-none pl-5 mt-2">
            {q.options.map((option, optionIndex) => (
              <li key={optionIndex} className="mb-2">
                <button
                  onClick={() => handleAnswer(index, option)}
                  className={`w-full text-left p-2 rounded ${
                    userAnswers[index] === option
                      ? feedback[index]
                        ? 'bg-green-200'
                        : 'bg-red-200'
                      : 'bg-gray-100 hover:bg-gray-200'
                  }`}
                >
                  {String.fromCharCode(65 + optionIndex)}) {option}
                </button>
              </li>
            ))}
          </ul>
          {feedback[index] !== null && (
            <div className={`mt-2 p-2 rounded ${feedback[index] ? 'bg-green-100' : 'bg-red-100'}`}>
              {feedback[index] ? 'Correct!' : `Incorrect. The correct answer is: ${q.answer}`}
            </div>
          )}
        </div>
      ))}
    </div>
  );
};
