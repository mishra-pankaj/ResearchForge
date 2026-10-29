// src/pages/Auth.jsx
import { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { login, register, getMe } from "../api";
import { saveToken } from "../auth";
import ErrorMessage from "../components/ErrorMessage";

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const MIN_PASSWORD = 8;
const MAX_PASSWORD = 128;

export default function Auth() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const emailRef = useRef(null);

  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [formError, setFormError] = useState("");
  const [fieldErrors, setFieldErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);

  const isRegister = mode === "register";

  useEffect(() => {
    emailRef.current?.focus();
  }, []);

  function switchMode() {
    setMode(isRegister ? "login" : "register");
    setPassword("");
    setFormError("");
    setFieldErrors({});
  }

  function validate() {
    const errors = {};
    const trimmedEmail = email.trim();

    if (!EMAIL_PATTERN.test(trimmedEmail)) {
      errors.email = "Enter a valid email address.";
    }
    if (password.length < MIN_PASSWORD) {
      errors.password = `Password must be at least ${MIN_PASSWORD} characters.`;
    } else if (password.length > MAX_PASSWORD) {
      errors.password = `Password must be at most ${MAX_PASSWORD} characters.`;
    }
    return errors;
  }

  async function handleSubmit(event) {
    event.preventDefault();
    if (submitting) return;

    const errors = validate();
    setFieldErrors(errors);
    setFormError("");
    if (Object.keys(errors).length > 0) return;

    const cleanEmail = email.trim().toLowerCase();
    setSubmitting(true);

    try {
      if (isRegister) {
        await register(cleanEmail, password);

        try {
          const { access_token } = await login(cleanEmail, password);
          saveToken(access_token);
        } catch {
          // The account exists, but logging in failed. Ask the user to log in.
          setMode("login");
          setPassword("");
          setFormError("Account created. Please log in.");
          return;
        }
      } else {
        const { access_token } = await login(cleanEmail, password);
        saveToken(access_token);
      }

      navigate("/home", { replace: true });
    } catch (err) {
      setFormError(
        err.status === 409
          ? "This email is already registered."
          : err.status === 401
            ? "Invalid email or password."
            : err.message
      );
      setPassword("");
    } finally {
      setSubmitting(false);
    }
  }

  const title = isRegister ? "Create account" : "Log in";
  const buttonText = isRegister ? "Create account" : "Log in";
  const switchText = isRegister
    ? "Already have an account? Log in"
    : "New here? Create an account";

  const inputClass =
    "w-full rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-slate-800 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200";

  return (
    <div className="flex min-h-screen flex-col bg-slate-50">
      <header className="px-6 py-4">
        <Link to="/" className="text-sm font-medium text-blue-600 hover:underline">
          ← Back to home
        </Link>
      </header>

      <main className="flex flex-1 items-center justify-center px-4 py-8">
        <div className="w-full max-w-sm rounded-xl border border-slate-200 bg-white p-8 shadow-sm">
          <h1 className="mb-6 text-2xl font-bold text-slate-800">{title}</h1>

          <form onSubmit={handleSubmit} noValidate className="space-y-4">
            <div>
              <label htmlFor="email" className="mb-1 block text-sm font-medium text-slate-700">
                Email
              </label>
              <input
                id="email"
                ref={emailRef}
                type="email"
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className={inputClass}
              />
              {fieldErrors.email && (
                <p className="mt-1 text-sm text-red-600">{fieldErrors.email}</p>
              )}
            </div>

            <div>
              <label htmlFor="password" className="mb-1 block text-sm font-medium text-slate-700">
                Password
              </label>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  autoComplete={isRegister ? "new-password" : "current-password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className={`${inputClass} pr-16`}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((value) => !value)}
                  className="absolute inset-y-0 right-3 my-auto h-fit text-xs font-medium text-slate-500 hover:text-slate-700"
                >
                  {showPassword ? "Hide" : "Show"}
                </button>
              </div>
              {fieldErrors.password && (
                <p className="mt-1 text-sm text-red-600">{fieldErrors.password}</p>
              )}
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="w-full rounded-lg bg-blue-600 px-4 py-2.5 font-medium text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-300"
            >
              {submitting ? "Please wait..." : buttonText}
            </button>

            <ErrorMessage message={formError} />
          </form>

          <div className="mt-6 text-center">
            <button
              type="button"
              onClick={switchMode}
              className="text-sm text-blue-600 hover:underline"
            >
              {switchText}
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}