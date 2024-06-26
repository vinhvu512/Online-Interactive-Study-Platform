"use client";

export const CourseEnrollButton = () => {
  return (
    <button
      className="bg-primary-500 text-white font-semibold py-2 px-4 rounded-lg"
      onClick={() => {
        alert(`Enrolling in course`);
      }}
    >
      Enroll Now
    </button>
  );
};
