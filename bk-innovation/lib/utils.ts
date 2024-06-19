import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
import axios from "axios";
import Cookies from "js-cookie";

// Fetch CSRF token

export const getCsrfToken = async () => {
  try {
    const response = await axios.get("http://localhost:8000/watching/csrf/", {
      withCredentials: true,
    });
    Cookies.set("csrftoken", response.data.csrfToken);
    return response.data.csrfToken;
  } catch (error) {
    console.error("Error fetching CSRF token:", error);
    return null;
  }
};
