const SESSION_KEY = "finance.session";
const LEGACY_ACCESS_KEY = "finance.token";
const PROFILE = { id: "profile", method: "GET", path: "/users/me" };

function readTokens(body) {
  if (
    typeof body?.access_token !== "string" || !body.access_token ||
    typeof body?.refresh_token !== "string" || !body.refresh_token
  ) {
    return null;
  }

  return { access_token: body.access_token, refresh_token: body.refresh_token };
}

function loadSession() {
  try {
    sessionStorage.removeItem(LEGACY_ACCESS_KEY);
    const tokens = readTokens(JSON.parse(sessionStorage.getItem(SESSION_KEY)));

    return tokens ? { tokens, confirmed: true, refresh: null } : null;
  } catch {
    return null;
  }
}

function storeSession(tokens) {
  try {
    if (tokens) {
      sessionStorage.setItem(SESSION_KEY, JSON.stringify(tokens));
    } else {
      sessionStorage.removeItem(SESSION_KEY);
    }
  } catch {
    // A sessão continua funcionando em memória se o navegador bloquear o armazenamento.
  }
}

let session = loadSession();

const app = Elm.Main.init({
  node: document.getElementById("app"),
  flags: session !== null
});

function failure(error, status = 0) {
  return { status, error, retryAfter: null, body: null };
}

function deliver(id, response) {
  app.ports.receiveResponse.send({ id, ...response });
}

async function send({ method, path, body }, accessToken, keepalive = false) {
  const url = new URL("/api/v1" + path, window.location.origin);

  if (url.origin !== window.location.origin || !url.pathname.startsWith("/api/v1/")) {
    return failure("invalid_path");
  }

  const headers = { Accept: "application/json" };
  if (accessToken) headers.Authorization = "Bearer " + accessToken;
  if (body != null) headers["Content-Type"] = "application/json";

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 15000);

  try {
    const response = await fetch(url, {
      method,
      headers,
      body: body == null ? undefined : JSON.stringify(body),
      signal: controller.signal,
      keepalive,
      redirect: "error"
    });
    const raw = await response.text();
    let payload = null;

    try {
      payload = raw ? JSON.parse(raw) : null;
    } catch {
      return failure("invalid_response", response.status);
    }

    const retryAfter = response.headers.get("Retry-After");

    return {
      status: response.status,
      error: typeof payload?.error === "string" ? payload.error : null,
      retryAfter: /^\d+$/.test(retryAfter ?? "") ? Number(retryAfter) : null,
      body: payload
    };
  } catch {
    return failure(controller.signal.aborted ? "timeout" : "network_error");
  } finally {
    clearTimeout(timeout);
  }
}

function clearSession() {
  session = null;
  storeSession(null);
}

function refreshSession(current) {
  if (!current.refresh) {
    current.refresh = (async () => {
      const response = await send({
        method: "POST",
        path: "/auth/refresh",
        body: { refresh_token: current.tokens.refresh_token }
      });
      const tokens = response.status === 200 ? readTokens(response.body) : null;

      if (tokens) {
        current.tokens = tokens;
        if (session === current && current.confirmed) storeSession(tokens);
        return null;
      }

      // Após falha de transporte, a API pode já ter consumido o refresh token.
      // Reenviá-lo poderia revogar toda a família de tokens.
      return response.status === 401
        ? failure("invalid_token", 401)
        : failure(response.error ?? "invalid_response", response.status);
    })().finally(() => {
      current.refresh = null;
    });
  }

  return current.refresh;
}

function isInvalidToken(response) {
  return response.status === 401 && response.error === "invalid_token";
}

async function requestProtected(request, current = session) {
  if (!current) return failure("not_authenticated", 401);

  // Quem inicia enquanto o refresh está pendente aproveita o novo par de tokens.
  if (current.refresh) {
    const error = await current.refresh;
    if (error) return error;
    if (session !== current) return failure("not_authenticated", 401);
  }

  const initialToken = current.tokens.access_token;
  let response = await send(request, initialToken);

  if (session === current && isInvalidToken(response)) {
    if (current.tokens.access_token === initialToken) {
      const error = await refreshSession(current);
      if (error) {
        if (session === current) expireSession(request.id, error);
        return error;
      }
    }

    if (session !== current) return failure("not_authenticated", 401);

    const retryToken = current.tokens.access_token;
    response = await send(request, retryToken);

    if (session === current && current.tokens.access_token === retryToken && isInvalidToken(response)) {
      expireSession(request.id, response);
    }
  }

  return response;
}

function expireSession(requestId, response) {
  clearSession();
  if (requestId !== PROFILE.id) deliver("session-ended", response);
}

async function loadProfile(current) {
  const response = await requestProtected(PROFILE, current);

  if (session && session !== current) return;

  const validProfile =
    response.status === 200 &&
    typeof response.body?.id === "string" &&
    typeof response.body?.email === "string";

  if (validProfile && session === current) {
    current.confirmed = true;
    storeSession(current.tokens);
  } else if (!validProfile && session === current) {
    clearSession();
  }

  deliver(PROFILE.id, response);
}

app.ports.sendLogin.subscribe(async (body) => {
  const response = await send({ method: "POST", path: "/auth/login", body });
  const tokens = response.status === 200 ? readTokens(response.body) : null;

  if (tokens) {
    session = { tokens, confirmed: false, refresh: null };
    deliver("login", { ...response, body: null });
  } else {
    deliver("login", response.status === 200
      ? failure("invalid_response", response.status)
      : response);
  }
});

app.ports.sendRegistration.subscribe(async (body) => {
  deliver("registration", await send({ method: "POST", path: "/users", body }));
});

app.ports.sendRequest.subscribe(async (request) => {
  const current = session;
  if (request.id === PROFILE.id && current) {
    await loadProfile(current);
    return;
  }

  const response = await requestProtected(request, current);

  if (session === current) deliver(request.id, response);
});

app.ports.sendLogout.subscribe(async () => {
  const current = session;
  clearSession();

  if (current) {
    // Se há renovação em andamento, revogue com o par mais recente disponível.
    await current.refresh;
    await send({
      method: "POST",
      path: "/auth/logout",
      body: { refresh_token: current.tokens.refresh_token }
    }, current.tokens.access_token, true);
  }
});

if (session) loadProfile(session);
