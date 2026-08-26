import { useEffect, useState } from "react";
import { Moon, Sun, TrendingUp, Rocket, RefreshCw } from "lucide-react";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { refreshAllData } from "@/hooks/useJsonData";
import { NewsFeed } from "@/pages/NewsFeed";
import { Rankings } from "@/pages/Rankings";
import { Portfolio } from "@/pages/Portfolio";
import { Radar } from "@/pages/Radar";

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
  const [refreshing, setRefreshing] = useState(false);

  function handleRefresh() {
    setRefreshing(true);
    refreshAllData();
    // Καθαρά UI feedback (spin) — τα ίδια τα hooks δεν εκθέτουν πότε τελειώνουν
    // όλα τα ταυτόχρονα refetches, οπότε ένα σταθερό μικρό διάστημα αρκεί.
    setTimeout(() => setRefreshing(false), 1000);
  }

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
          <div className="flex items-center gap-1">
            <Button
              variant="ghost"
              size="icon"
              onClick={handleRefresh}
              aria-label="Ανανέωση δεδομένων"
              disabled={refreshing}
            >
              <RefreshCw className={`size-4 ${refreshing ? "animate-spin" : ""}`} />
            </Button>
            <Button variant="ghost" size="icon" onClick={toggle} aria-label="Εναλλαγή θέματος">
              {dark ? <Sun className="size-4" /> : <Moon className="size-4" />}
            </Button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-4 py-6">
        <Tabs defaultValue="news">
          <TabsList>
            <TabsTrigger value="news">Ειδήσεις</TabsTrigger>
            <TabsTrigger value="rankings">Rankings</TabsTrigger>
            <TabsTrigger value="portfolio">Χαρτοφυλάκιο</TabsTrigger>
            <TabsTrigger
              value="radar"
              className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground"
            >
              <Rocket className="size-3.5" /> Ραντάρ
            </TabsTrigger>
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
          <TabsContent value="radar">
            <Radar />
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}

export default App;
