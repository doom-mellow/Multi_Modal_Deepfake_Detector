import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
} from 'react-router-dom';

import IntersectObserver from '@/components/common/IntersectObserver';
import { Toaster } from '@/components/ui/sonner';
import { NavigationHeader } from '@/components/NavigationHeader';
import { ThemeProvider } from '@/contexts/ThemeContext';
import { AuthProvider } from '@/contexts/AuthContext';

import { routes } from './routes';

function App() {
  return (
    <ThemeProvider
      defaultTheme="dark"
      storageKey="deepshield-ui-theme"
    >
      <AuthProvider>
        <Router>
          <IntersectObserver />

          <div className="flex min-h-screen flex-col bg-background text-foreground transition-colors duration-200">
            <NavigationHeader />

            <main className="flex-grow">
              <Routes>
                {routes.map((route) => (
                  <Route
                    key={route.path}
                    path={route.path}
                    element={route.element}
                  />
                ))}

                <Route
                  path="*"
                  element={<Navigate to="/" replace />}
                />
              </Routes>
            </main>
          </div>

          <Toaster />
        </Router>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;