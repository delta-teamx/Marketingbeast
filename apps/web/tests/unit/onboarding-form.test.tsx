import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { OnboardingForm } from "@/components/onboarding-form";

// Stub Next navigation + the API client so the form renders in jsdom.
vi.mock("next/navigation", () => ({ useRouter: () => ({ push: vi.fn() }) }));
vi.mock("@/lib/api-client", () => ({
  api: { conversationalOnboarding: vi.fn(), submitOnboarding: vi.fn() },
}));

describe("OnboardingForm", () => {
  // Regression: the wrapper used to be a component defined inside render, so
  // every keystroke remounted the whole form and dropped input focus — on mobile
  // that made the spacebar scroll the page instead of typing a space.
  it("keeps the describe field mounted and focused across keystrokes", () => {
    render(<OnboardingForm embedded />);
    const ta = screen.getByPlaceholderText(/CrossFit gym/i) as HTMLTextAreaElement;
    ta.focus();
    expect(document.activeElement).toBe(ta);

    fireEvent.change(ta, { target: { value: "I run" } });

    // Same DOM node after a state update => not remounted => focus retained.
    const taAfter = screen.getByPlaceholderText(/CrossFit gym/i);
    expect(taAfter).toBe(ta);
    expect(document.activeElement).toBe(ta);
  });

  it("accepts spaces between words in the fields", () => {
    render(<OnboardingForm embedded />);
    const name = screen.getByLabelText(/Business name/i) as HTMLInputElement;
    fireEvent.change(name, { target: { value: "Glove Cars Dealership" } });
    expect(screen.getByLabelText(/Business name/i)).toHaveValue("Glove Cars Dealership");
  });
});
