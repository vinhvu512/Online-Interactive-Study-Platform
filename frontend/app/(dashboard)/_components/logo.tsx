"use client";

import Image from "next/image";
import imageLoader from "@/utils/imageLoader";

export const Logo = () => {
  return (
    <div>
      <Image
        src="/logo.png"
        alt="Logo"
        width={180}
        height={180}
        loader={imageLoader}
        unoptimized
      />
    </div>
  );
};
