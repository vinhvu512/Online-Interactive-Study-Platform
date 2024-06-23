"use client";

import { Category } from "@prisma/client";
import { IconType } from "react-icons";

import {
  FcMultipleDevices,
  FcEngineering,
  FcMindMap,
  FcGlobe,
  FcPrivacy,
  FcStatistics,
  FcFlowChart,
} from "react-icons/fc";
import { CategoryItem } from "@/app/(dashboard)/(routes)/search/_components/category-item";
interface CategoriesProps {
  items: Category[];
}

const iconMap: Record<Category["name"], IconType> = {
  "Computer Science": FcMultipleDevices, // Icon representing multiple devices
  "Computer Engineering": FcEngineering, // Icon representing engineering
  "Artificial Intelligence": FcMindMap, // Icon representing a mind map
  "Web Development": FcGlobe, // Icon representing the web
  Cybersecurity: FcPrivacy, // Icon representing privacy
  "Data Science": FcStatistics, // Icon representing statistics
  "Machine Learning": FcFlowChart, // Icon representing a flowchart
};

export const Categories = ({ items }: CategoriesProps) => {
  return (
    <div className="flex items-center gap-x-2 overflow-x-auto pb-2">
      {items.map((item) => (
        <CategoryItem
          key={item.id}
          label={item.name}
          icon={iconMap[item.name]}
          value={item.id}
        />
      ))}
    </div>
  );
};
