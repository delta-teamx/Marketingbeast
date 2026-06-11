const agree = document.getElementById("agree") as HTMLInputElement;
const accept = document.getElementById("accept") as HTMLButtonElement;
const done = document.getElementById("done")!;

agree.addEventListener("change", () => {
  accept.disabled = !agree.checked;
});

accept.addEventListener("click", () => {
  chrome.runtime.sendMessage(
    { type: "saveSettings", patch: { consentAccepted: true } },
    () => {
      done.textContent = "Enabled. You can close this tab and open the Presence popup.";
    },
  );
});
