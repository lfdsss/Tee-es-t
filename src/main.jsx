import React from "react";
import ReactDOM from "react-dom/client";
import { Analytics } from "@vercel/analytics/react";
import QuizApp from "./components/QuizApp";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <QuizApp />
    <Analytics />
  </React.StrictMode>
);
