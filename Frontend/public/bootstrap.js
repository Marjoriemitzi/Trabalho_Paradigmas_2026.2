(() => {
  "use strict";
  const key = "saldo.session.v1";
  const valid = (session) =>
    session &&
    typeof session.value === "string" &&
    session.value.length > 0 &&
    Number.isSafeInteger(session.expiresAt) &&
    session.expiresAt > Date.now();
  let session = null;
  try {
    const stored = JSON.parse(sessionStorage.getItem(key));
    if (valid(stored))
      session = { value: stored.value, expiresAt: stored.expiresAt };
    else sessionStorage.removeItem(key);
  } catch {
    // Access can be denied in privacy modes. Login still works in memory.
  }
  const app = Elm.Main.init({
    node: document.getElementById("app"),
    flags: { now: Date.now(), session },
  });
  let expiration;
  const clear = () => {
    clearTimeout(expiration);
    try {
      sessionStorage.removeItem(key);
    } catch {
      /* Memory-only session. */
    }
  };
  app.ports.saveSession.subscribe((value) => {
    clear();
    if (!valid(value)) return;
    try {
      sessionStorage.setItem(key, JSON.stringify(value));
    } catch {
      /* Memory-only session. */
    }
    expiration = setTimeout(
      clear,
      Math.min(value.expiresAt - Date.now(), 2147483647),
    );
  });
  app.ports.clearSession.subscribe(clear);
  app.ports.focusField.subscribe((id) =>
    requestAnimationFrame(() => document.getElementById(id)?.focus()),
  );
})();
