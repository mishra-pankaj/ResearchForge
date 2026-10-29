// // src/components/Header.jsx
// import { Link, useLocation, useNavigate } from "react-router-dom";
// import { clearToken } from "../auth";

// export default function Header() {
//   const location = useLocation();
//   const navigate = useNavigate();

//   // On Home the left link opens History. Everywhere else it opens Home.
//   const onHome = location.pathname === "/home";

//     function handleLogout() {
//     clearToken();
//     window.location.replace("/");
//   }

//   return (
//     <header className="border-b border-slate-200 bg-white">
//       <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
//         {onHome ? (
//           <Link to="/history" className="text-sm font-medium text-blue-600 hover:underline">
//             History
//           </Link>
//         ) : (
//           <Link to="/home" className="text-sm font-medium text-blue-600 hover:underline">
//             Home
//           </Link>
//         )}

//         <button
//           type="button"
//           onClick={handleLogout}
//           className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
//         >
//           Logout
//         </button>
//       </div>
//     </header>
//   );
// }

// src/components/Header.jsx
import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { clearToken, isLoggedIn } from "../auth";

export default function Header() {
  const location = useLocation();
  const [loggedIn, setLoggedIn] = useState(isLoggedIn());

  // Re-check the token on every route change, so the header updates
  // after login, logout, or an expired session.
  useEffect(() => {
    setLoggedIn(isLoggedIn());
  }, [location]);

  const onHome = location.pathname === "/home";

  function handleLogout() {
    clearToken();
    window.location.replace("/");
  }

  return (
    <header className="sticky top-0 z-10 border-b border-slate-200 bg-white">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        {loggedIn ? (
          <>
            {onHome ? (
              <Link to="/history" className="text-sm font-medium text-blue-600 hover:underline">
                History
              </Link>
            ) : (
              <Link to="/home" className="text-sm font-medium text-blue-600 hover:underline">
                Home
              </Link>
            )}
            <button
              type="button"
              onClick={handleLogout}
              className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
            >
              Logout
            </button>
          </>
        ) : (
          <>
            <Link to="/" className="text-xl font-bold text-slate-800">
              ResearchForge
            </Link>
            <Link
              to="/auth"
              className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
            >
              Register / Login
            </Link>
          </>
        )}
      </div>
    </header>
  );
}