import { useEffect, useState } from "react";
import { Moon, Sun, TrendingUp } from "lucide-react";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { NewsFeed } from "@/pages/NewsFeed";
import { Rankings } from "@/pages/Rankings";
import { Portfolio } from "@/pages/Portfolio";

function useTheme() {
  const [dark, setDark] = useState(() => {
    if (typeof window === "undefined") return false;
    const stored = localStorage.getItem("theme");
    if (stored) return stored === "dark";
    return window.matchMedia("(prefers-color-scheme: dark)").matches;
  });

  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
    localStorage.setItem("theme", dark ? "dark" : "light");
  }, [dark]);

  return { dark, toggle: () => setDark((d) => !d) };
}

function App() {
  const { dark, toggle } = useTheme();

  return (
    <div className="min-h-svh bg-background">
      <header className="border-b border-border">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-4">
          <div className="flex items-center gap-2">
            <TrendingUp className="size-5 text-primary" />
            <div>
              <h1 className="text-base font-semibold leading-none">Market Intel</h1>
              <p className="text-xs text-muted-foreground">
                Ειδήσεις &amp; screening αγορών σε πραγματικό χρόνο
              </p>
            </div>
          </div>
          <Button variant="ghost" size="icon" onClick={toggle} aria-label="Εναλλαγή θέματος">
            {dark ? <Sun className="size-4" /> : <Moon className="size-4" />}
          </Button>
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-4 py-6">
        <Tabs defaultValue="news">
          <TabsList>
            <TabsTrigger value="news">Ειδήσεις</TabsTrigger>
            <TabsTrigger value="rankings">Rankings</TabsTrigger>
            <TabsTrigger value="portfolio">Χαρτοφυλάκιο</TabsTrigger>
          </TabsList>
          <TabsContent value="news">
            <NewsFeed />
          </TabsContent>
          <TabsContent value="rankings">
            <Rankings />
          </TabsContent>
          <TabsContent value="portfolio">
            <Portfolio />
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}

export default App;
