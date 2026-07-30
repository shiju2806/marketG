import React from "react";
import ReactDOM from "react-dom/client";
import { createBrowserRouter, RouterProvider } from "react-router-dom";
import "./index.css";
import { OrgProvider } from "./state";
import { AppLayout } from "./AppLayout";
import { Overview } from "./pages/Overview";
import { Competitors } from "./pages/Competitors";
import { Prompts } from "./pages/Prompts";
import { Sources } from "./pages/Sources";
import { Opportunities } from "./pages/Opportunities";
import { Twin } from "./pages/Twin";
import { Usage } from "./pages/Usage";

const router = createBrowserRouter(
  [
    {
      path: "/",
      element: <AppLayout />,
      children: [
        { index: true, element: <Overview /> },
        { path: "competitors", element: <Competitors /> },
        { path: "prompts", element: <Prompts /> },
        { path: "sources", element: <Sources /> },
        { path: "opportunities", element: <Opportunities /> },
        { path: "twin", element: <Twin /> },
        { path: "usage", element: <Usage /> },
      ],
    },
  ],
  { future: { v7_startTransition: true, v7_relativeSplatPath: true } }
);

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <OrgProvider>
      <RouterProvider router={router} />
    </OrgProvider>
  </React.StrictMode>
);
