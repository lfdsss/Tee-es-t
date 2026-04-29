import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import MatchCard from "./MatchCard";

describe("MatchCard", () => {
  it("renders title, company, city and score as percent", () => {
    render(
      <MatchCard
        match={{
          offer_id: "off-1",
          title: "Alternance développeur React",
          company: "Acme SAS",
          city: "paris",
          score: 0.87,
          reasons: ["skills chevauchent (0.75)", "même ville"],
        }}
      />,
    );
    expect(screen.getByText(/Alternance développeur React/)).toBeInTheDocument();
    expect(screen.getByText(/Acme SAS/)).toBeInTheDocument();
    expect(screen.getByText(/paris/)).toBeInTheDocument();
    expect(screen.getByText("87%")).toBeInTheDocument();
    expect(screen.getByText(/skills chevauchent/)).toBeInTheDocument();
  });

  it("handles missing title and empty reasons", () => {
    render(
      <MatchCard
        match={{
          offer_id: "off-2",
          title: "",
          company: "",
          city: "",
          score: 0.5,
          reasons: [],
        }}
      />,
    );
    expect(screen.getByText(/sans titre/)).toBeInTheDocument();
    expect(screen.getByText("50%")).toBeInTheDocument();
  });
});
