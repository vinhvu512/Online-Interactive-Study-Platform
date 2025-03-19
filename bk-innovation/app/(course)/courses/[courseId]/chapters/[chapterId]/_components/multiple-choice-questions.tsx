"use client";
import React, { useState } from 'react';

interface Question {
  question: string;
  options: string[];
  answer: number;
}

interface MultipleChoiceQuestionsProps {
  questions: Question[];
}

export const MultipleChoiceQuestions: React.FC<MultipleChoiceQuestionsProps> = ({ questions }) => {
  const [userAnswers, setUserAnswers] = useState<{ [key: number]: number | null }>({});
  const [feedback, setFeedback] = useState<{ [key: number]: boolean | null }>({});

  const handleAnswer = (questionIndex: number, selectedOptionIndex: number) => {
    setUserAnswers(prev => ({ ...prev, [questionIndex]: selectedOptionIndex }));
    const isCorrect = selectedOptionIndex === questions[questionIndex].answer;
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
                  onClick={() => handleAnswer(index, optionIndex)}
                  className={`w-full text-left p-2 rounded ${
                    userAnswers[index] === optionIndex
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
          {feedback[index] === false && (
            <div className="mt-2 p-2 rounded bg-red-100">
              Incorrect
            </div>
          )}
        </div>
      ))}
    </div>
  );
}