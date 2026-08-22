/**
 * Clinical Flight Deck: route shell stays calm, operational, and role-aware.
 * Mineral navy anchors context; Queue Teal carries live state.
 */
import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import NotFound from "@/pages/NotFound";
import { Route, Switch } from "wouter";
import ErrorBoundary from "./components/ErrorBoundary";
import { SessionProvider } from "./contexts/SessionContext";
import { ThemeProvider } from "./contexts/ThemeContext";
import Dashboard from "./pages/Dashboard";
import Home from "./pages/Home";
import SignIn from "./pages/SignIn";
import Register from "./pages/Register";

function Router() {
  return (
    <Switch>
      <Route path="/" component={Home} />
      <Route path="/sign-in" component={SignIn} />
      <Route path="/register" component={Register} />
      <Route path="/dashboard" component={Dashboard} />
      <Route path="/404" component={NotFound} />
      <Route component={NotFound} />
    </Switch>
  );
}

export default function App() {
  return (
    <ErrorBoundary>
      <ThemeProvider defaultTheme="light">
        <SessionProvider>
          <TooltipProvider>
            <Toaster richColors position="top-right" />
            <Router />
          </TooltipProvider>
        </SessionProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}
