import { create } from "zustand";
import type { Child } from "@/types";

interface ChildState {
  currentChild: Child | null;
  setCurrentChild: (child: Child | null) => void;
  loadFromStorage: () => void;
}

export const useChildStore = create<ChildState>((set) => ({
  currentChild: null,
  setCurrentChild: (child) => {
    if (child) {
      localStorage.setItem("currentChild", JSON.stringify(child));
    } else {
      localStorage.removeItem("currentChild");
    }
    set({ currentChild: child });
  },
  loadFromStorage: () => {
    if (typeof window === "undefined") return;
    const str = localStorage.getItem("currentChild");
    if (str) {
      try {
        set({ currentChild: JSON.parse(str) });
      } catch {
        set({ currentChild: null });
      }
    }
  },
}));
