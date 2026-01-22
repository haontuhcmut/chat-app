import { create } from "zustand";
import { persist } from "zustand/middleware";
import { ThemeState } from "@/types/store";

export const useThemeStore = create<ThemState>()(persist((set, get) => ({})));
