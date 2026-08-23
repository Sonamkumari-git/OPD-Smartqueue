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
import RoleDashboard from "./components/RoleDashboard";

function SignInLanding() { return <SignIn />; }
function PatientSignIn() { return <SignIn requiredRole="patient" />; }
function DoctorSignIn() { return <SignIn requiredRole="doctor" />; }
function NurseSignIn() { return <SignIn requiredRole="nurse" />; }
function AdminSignIn() { return <SignIn requiredRole="admin" />; }
function DashboardLanding() { return <RoleDashboard />; }
function PatientDashboard() { return <RoleDashboard requiredRole="patient" />; }
function DoctorDashboard() { return <RoleDashboard requiredRole="doctor" />; }
function NurseDashboard() { return <RoleDashboard requiredRole="nurse" />; }
function AdminDashboard() { return <RoleDashboard requiredRole="admin" />; }

function Router() {
  return (
    <Switch>
      <Route path="/" component={Home} />
      <Route path="/sign-in" component={SignInLanding} />
      <Route path="/sign-in/patient" component={PatientSignIn} />
      <Route path="/sign-in/doctor" component={DoctorSignIn} />
      <Route path="/sign-in/nurse" component={NurseSignIn} />
      <Route path="/sign-in/admin" component={AdminSignIn} />
      <Route path="/register" component={Register} />
      <Route path="/dashboard" component={DashboardLanding} />
      <Route path="/dashboard/patient" component={PatientDashboard} />
      <Route path="/dashboard/doctor" component={DoctorDashboard} />
      <Route path="/dashboard/nurse" component={NurseDashboard} />
      <Route path="/dashboard/admin" component={AdminDashboard} />
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
