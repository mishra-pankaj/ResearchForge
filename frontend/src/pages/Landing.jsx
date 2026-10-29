// src/pages/Landing.jsx
import { Link } from "react-router-dom";
import Header from "../components/Header";

export default function Landing() {
  return (
    <div className="flex min-h-screen flex-col bg-white">
      <Header />

      <main className="flex flex-1 items-center justify-center px-6 py-12">
        <div className="flex h-72 w-full max-w-3xl items-center justify-center rounded-xl border-2 border-dashed border-slate-300 bg-slate-50">
          <p className="text-sm text-slate-400">Image or video goes here</p>
        </div>
      </main>

      <footer className="border-t border-slate-200 px-6 py-4">
        <div className="mx-auto flex max-w-6xl items-center justify-between">
          <span className="text-sm font-medium text-slate-600">@ResearchForge</span>
          <a
            href="https://github.com/mishra-pankaj"
            target="_blank"
            rel="noreferrer"
            className="text-sm text-slate-600 hover:text-blue-600 hover:underline"
          >
            Made by Pankaj Mishra
          </a>
        </div>
      </footer>
    </div>
  );
}