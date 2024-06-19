"use client";
import { Layout, Compass, List } from "lucide-react";
import { SidebarItem } from "@/app/(dashboard)/_components/sidebar-item";
import { usePathname, useRouter } from "next/navigation";

const guestRoutes = [
  {
    icon: Layout,
    label: "Dashboard",
    href: "/",
  },
  {
    icon: Compass,
    label: "Browser",
    href: "/search",
  },
];

const teacherRoutes = [
  {
    icon: List,
    label: "Courses",
    href: "/teacher/courses",
  },
  // {
  //   icon: Compass,
  //   label: "Browser",
  //   href: "/search",
  // },
];

export const SidebarRoutes = () => {
  const pathname = usePathname();
  // const router = useRouter();

  const isTeacherPage = pathname?.startsWith("/teacher");
  const isStudentPage = pathname?.includes("/chapter");
  const students = guestRoutes;
  const teacher = teacherRoutes;
  return (
    <div className="flex flex-col w-full">
      {isTeacherPage || isStudentPage
        ? teacher.map((route) => (
            <SidebarItem
              key={route.label}
              icon={route.icon}
              label={route.label}
              href={route.href}
            />
          ))
        : students.map((route) => (
            <SidebarItem
              key={route.label}
              icon={route.icon}
              label={route.label}
              href={route.href}
            />
          ))}
    </div>
  );
};
