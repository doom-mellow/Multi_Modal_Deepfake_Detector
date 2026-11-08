
import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import type { User } from "@supabase/supabase-js";
import { toast } from "sonner";

import { supabase } from "@/db/supabase";

interface AuthContextType {
  user: User | null;
  loading: boolean;
  signInWithUsername: (
    username: string,
    password: string,
  ) => Promise<{ error: Error | null }>;
  signUpWithUsername: (
    username: string,
    password: string,
  ) => Promise<{ error: Error | null }>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

/**
 * Converts a username into the email address used by Supabase Auth.
 *
 * Users can enter either their actual email address or a username.
 * Username-based authentication requires VITE_AUTH_EMAIL_DOMAIN.
 */
function resolveAuthEmail(identifier: string): string {
  const value = identifier.trim().toLowerCase();

  if (!value) {
    throw new Error("Please enter your username or email address.");
  }

  if (value.includes("@")) {
    return value;
  }

  const domain = import.meta.env.VITE_AUTH_EMAIL_DOMAIN?.trim();

  if (!domain) {
    throw new Error(
      "Username authentication is not configured. Set VITE_AUTH_EMAIL_DOMAIN in your .env file, or sign in using your email address.",
    );
  }

  return `${value}@${domain.replace(/^@/, "")}`;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      if (!active) return;

      setUser(session?.user ?? null);
      setLoading(false);
    });

    return () => {
      active = false;
      subscription.unsubscribe();
    };
  }, []);

  const signInWithUsername = async (
    username: string,
    password: string,
  ): Promise<{ error: Error | null }> => {
    try {
      const email = resolveAuthEmail(username);

      const { error } = await supabase.auth.signInWithPassword({
        email,
        password,
      });

      return { error };
    } catch (error: unknown) {
      return {
        error:
          error instanceof Error
            ? error
            : new Error("Failed to sign in."),
      };
    }
  };

  const signUpWithUsername = async (
    username: string,
    password: string,
  ): Promise<{ error: Error | null }> => {
    try {
      const email = resolveAuthEmail(username);

      const { error } = await supabase.auth.signUp({
        email,
        password,
      });

      return { error };
    } catch (error: unknown) {
      return {
        error:
          error instanceof Error
            ? error
            : new Error("Failed to create account."),
      };
    }
  };

  const signOut = async (): Promise<void> => {
    const { error } = await supabase.auth.signOut();

    if (error) {
      toast.error(error.message);
      throw error;
    }

    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        signInWithUsername,
        signUpWithUsername,
        signOut,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider.");
  }

  return context;
}
