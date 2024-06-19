import Image from "next/image";

export const Logo = () => {
  return (
    <div>
      <Image src="/logo.svg" alt="Logo" width={130} height={130} />
    </div>
  );
};
