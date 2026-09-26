import React, { createContext, useContext, useState, useEffect } from 'react';

export type ThemeMode = 'light' | 'dark' | 'system';
export type Theme = 'light' | 'dark';

interface ThemeContextType {
  theme: Theme;
  themeMode: ThemeMode;
  toggleTheme: () => void;
  setTheme: (mode: ThemeMode) => void;
}

const ThemeContext = createContext<ThemeContextType>({
  theme: 'dark',
  themeMode: 'dark',
  toggleTheme: () => {},
  setTheme: () => {},
});

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [themeMode, setThemeMode] = useState<ThemeMode>(() => {
    try {
      const saved = localStorage.getItem('aegistrace_theme') || localStorage.getItem('sih26237_theme');
      if (saved === 'light' || saved === 'dark' || saved === 'system') {
        return saved as ThemeMode;
      }
    } catch {
      // Fallback
    }
    return 'dark'; // Security operations standard
  });

  const [systemPreference, setSystemPreference] = useState<Theme>(() => {
    if (typeof window !== 'undefined' && window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches) {
      return 'light';
    }
    return 'dark';
  });

  // Watch system color-scheme changes
  useEffect(() => {
    if (typeof window === 'undefined' || !window.matchMedia) return;
    const mediaQuery = window.matchMedia('(prefers-color-scheme: light)');
    const handler = (e: MediaQueryListEvent) => {
      setSystemPreference(e.matches ? 'light' : 'dark');
    };
    mediaQuery.addEventListener('change', handler);
    return () => mediaQuery.removeEventListener('change', handler);
  }, []);

  const resolvedTheme: Theme = themeMode === 'system' ? systemPreference : themeMode;

  useEffect(() => {
    try {
      document.documentElement.setAttribute('data-theme', resolvedTheme);
      document.documentElement.style.colorScheme = resolvedTheme;
      localStorage.setItem('aegistrace_theme', themeMode);
      localStorage.setItem('sih26237_theme', themeMode);
    } catch {
      // Ignore storage errors in restricted contexts
    }
  }, [themeMode, resolvedTheme]);

  const toggleTheme = () => {
    setThemeMode(prev => {
      const resolved = prev === 'system' ? systemPreference : prev;
      return resolved === 'dark' ? 'light' : 'dark';
    });
  };

  const setTheme = (newMode: ThemeMode) => {
    setThemeMode(newMode);
  };

  return (
    <ThemeContext.Provider value={{ theme: resolvedTheme, themeMode, toggleTheme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = () => useContext(ThemeContext);
