const { test, expect } = require("@playwright/test");

const SESSION_KEY = "finance.session";
const TOKEN = "token-de-teste";
const TOKENS = {
  access_token: TOKEN,
  refresh_token: "refresh-de-teste"
};
const ROTATED = {
  access_token: "novo-access-token",
  refresh_token: "novo-refresh-token"
};

function sessionResponse(tokens) {
  return {
    ...tokens,
    token_type: "bearer",
    expires_in: 900,
    refresh_expires_in: 2592000
  };
}

const PASSWORD = "S3nha!Forte123";

const USER = {
  id: "17c263e5-2b67-4268-a3a2-cc06409c81ec",
  email: "email@exemplo.com",
  role: "user"
};

// Intercepta a API e registra os pedidos feitos pelo frontend.
// Nenhuma chamada interceptada chega ao backend real.
async function mockApi(page, options = {}) {
  const calls = [];

  await page.route("**/api/v1/**", async (route) => {
    const request = route.request();

    const call = {
      method: request.method(),
      path: new URL(request.url()).pathname,
      body: request.postDataJSON(),
      authorization: request.headers().authorization
    };

    calls.push(call);

    let status;
    let body;

    if (
      call.method === "POST" &&
      call.path === "/api/v1/auth/login"
    ) {
      status = options.loginStatus ?? 200;
      body =
        status === 200
          ? sessionResponse(TOKENS)
          : { error: status === 429 ? "too_many_attempts" : "invalid_credentials" };
    } else if (
      call.method === "POST" &&
      call.path === "/api/v1/users"
    ) {
      status = options.registrationStatus ?? 201;
      body =
        status === 201
          ? USER
          : {
              error:
                status === 429 ? "too_many_attempts" :
                  status === 409 ? "email_taken" : "weak_password"
            };
    } else if (
      call.method === "GET" &&
      call.path === "/api/v1/users/me"
    ) {
      status = options.meStatus ??
        (call.authorization === `Bearer ${options.expiredToken}` ? 401 : 200);
      body =
        status === 200
          ? USER
          : { error: "invalid_token" };
    } else if (call.method === "POST" && call.path === "/api/v1/auth/refresh") {
      if (options.waitForRefresh) await options.waitForRefresh;
      status = options.refreshStatus ?? 200;
      body = status === 200
        ? sessionResponse(ROTATED)
        : { error: "invalid_refresh_token" };
    } else if (call.method === "POST" && call.path === "/api/v1/auth/logout") {
      if (options.abortLogout) {
        await route.abort();
        return;
      }
      status = 204;
    } else {
      status = 404;
      body = { error: "not_found" };
    }

    await route.fulfill({
      status,
      contentType: "application/json",
      headers: status === 429 && options.retryAfter
        ? { "Retry-After": options.retryAfter }
        : undefined,
      body: JSON.stringify(body)
    });
  });

  return calls;
}

async function fillLogin(page, password = PASSWORD) {
  await page.getByLabel("E-mail", { exact: true }).fill(USER.email);
  await page.getByLabel("Senha", { exact: true }).fill(password);
}

async function submitLogin(page) {
  await page.getByRole("button", { name: "Entrar", exact: true }).click();
}

async function fillRegistration(
  page,
  password = PASSWORD,
  confirmation = password
) {
  await page
    .getByRole("button", { name: "Quero me cadastrar", exact: true })
    .click();

  await page.getByLabel("E-mail", { exact: true }).fill(USER.email);
  await page.getByLabel("Senha", { exact: true }).fill(password);
  await page.getByLabel("Confirme sua senha").fill(confirmation);
}

async function submitRegistration(page) {
  await page
    .getByRole("button", { name: "Criar conta", exact: true })
    .click();
}

async function expectAuthenticated(page) {
  await expect(page.getByText("Bem-vindo!", { exact: true }))
    .toBeVisible();

  await expect(page.getByText(USER.email, { exact: true }))
    .toBeVisible();
}

async function storedSession(page) {
  return page.evaluate(
    (key) => JSON.parse(sessionStorage.getItem(key)),
    SESSION_KEY
  );
}

test("login envia as credenciais e consulta o usuário com o token", async ({
  page
}) => {
  const calls = await mockApi(page);

  await page.goto("/");
  await fillLogin(page);
  await submitLogin(page);
  await expectAuthenticated(page);

  expect(calls).toHaveLength(2);

  expect(calls[0]).toMatchObject({
    method: "POST",
    path: "/api/v1/auth/login",
    body: {
      email: USER.email,
      password: PASSWORD
    }
  });

  expect(calls[1]).toMatchObject({
    method: "GET",
    path: "/api/v1/users/me",
    authorization: `Bearer ${TOKEN}`
  });

  await expect.poll(() => storedSession(page)).toEqual(TOKENS);
});

test("credenciais incorretas mostram erro e não criam sessão", async ({
  page
}) => {
  const calls = await mockApi(page, { loginStatus: 401 });

  await page.goto("/");
  await fillLogin(page);
  await submitLogin(page);

  await expect(page.getByRole("alert"))
    .toHaveText("E-mail ou senha incorretos.");

  await expect(
    page.getByRole("button", { name: "Entrar", exact: true })
  ).toBeEnabled();

  expect(calls).toHaveLength(1);
  expect(await storedSession(page)).toBeNull();
});

test("login não exige os requisitos de senha do cadastro", async ({
  page
}) => {
  const calls = await mockApi(page);

  await page.goto("/");
  await fillLogin(page, "curta");
  await submitLogin(page);
  await expectAuthenticated(page);

  expect(calls[0].body.password).toBe("curta");
});

test("cadastro envia somente e-mail e senha e retorna ao login", async ({
  page
}) => {
  const calls = await mockApi(page);

  await page.goto("/");
  await fillRegistration(page);
  await submitRegistration(page);

  await expect(page.getByRole("status"))
    .toHaveText("Conta criada com sucesso. Entre para continuar.");

  expect(calls).toHaveLength(1);

  expect(calls[0]).toMatchObject({
    method: "POST",
    path: "/api/v1/users"
  });

  expect(calls[0].body).toEqual({
    email: USER.email,
    password: PASSWORD
  });

  await expect(page.getByLabel("Senha", { exact: true }))
    .toHaveValue("");

  await expect(page.getByLabel("E-mail", { exact: true }))
    .toHaveValue(USER.email);

  expect(await storedSession(page)).toBeNull();
});

test("confirmação diferente impede o envio do cadastro", async ({
  page
}) => {
  const calls = await mockApi(page);

  await page.goto("/");
  await fillRegistration(page, PASSWORD, "Outra!Senha123");
  await submitRegistration(page);

  await expect(page.getByRole("alert"))
    .toHaveText("As senhas não coincidem.");

  expect(calls).toHaveLength(0);
});

test("e-mail já cadastrado apresenta mensagem específica", async ({
  page
}) => {
  await mockApi(page, { registrationStatus: 409 });

  await page.goto("/");
  await fillRegistration(page);
  await submitRegistration(page);

  await expect(page.getByRole("alert"))
    .toHaveText("Este e-mail já está cadastrado. Entre na sua conta.");

  await expect(
    page.getByRole("button", { name: "Criar conta", exact: true })
  ).toBeEnabled();
});

test("senha recusada pelo backend apresenta orientação", async ({
  page
}) => {
  await mockApi(page, { registrationStatus: 422 });

  await page.goto("/");

  // Tem 12 caracteres, mas não atende à política do backend.
  await fillRegistration(page, "aaaaaaaaaaaa");
  await submitRegistration(page);

  await expect(page.getByRole("alert"))
    .toHaveText("Confira o e-mail e os requisitos da senha.");
});

test("trocar de formulário limpa a senha e a confirmação", async ({
  page
}) => {
  await mockApi(page);

  await page.goto("/");
  await fillRegistration(page);

  await page
    .getByRole("button", { name: "Já tenho uma conta", exact: true })
    .click();

  await expect(page.getByLabel("Senha", { exact: true }))
    .toHaveValue("");

  await page
    .getByRole("button", { name: "Quero me cadastrar", exact: true })
    .click();

  await expect(page.getByLabel("Confirme sua senha"))
    .toHaveValue("");
});

test("atualizar a página restaura a sessão sem repetir o login", async ({
  page
}) => {
  const calls = await mockApi(page);

  await page.goto("/");
  await fillLogin(page);
  await submitLogin(page);
  await expectAuthenticated(page);

  await expect.poll(() => storedSession(page)).toEqual(TOKENS);

  await page.reload();
  await expectAuthenticated(page);

  expect(
    calls.filter((call) => call.path === "/api/v1/auth/login")
  ).toHaveLength(1);

  expect(
    calls.filter((call) => call.path === "/api/v1/users/me")
  ).toHaveLength(2);
});

test("sair remove a sessão e ela não retorna ao atualizar", async ({
  page
}) => {
  const calls = await mockApi(page);

  await page.goto("/");
  await fillLogin(page);
  await submitLogin(page);
  await expectAuthenticated(page);

  await expect.poll(() => storedSession(page)).toEqual(TOKENS);

  await page.getByRole("button", { name: "Sair", exact: true }).click();

  await expect.poll(() => storedSession(page)).toBeNull();
  await expect.poll(() => calls.find((call) => call.path === "/api/v1/auth/logout"))
    .toMatchObject({
      method: "POST",
      authorization: `Bearer ${TOKEN}`,
      body: { refresh_token: TOKENS.refresh_token }
    });

  await page.reload();

  await expect(
    page.getByRole("button", { name: "Entrar", exact: true })
  ).toBeVisible();

  expect(
    calls.filter((call) => call.path === "/api/v1/users/me")
  ).toHaveLength(1);
});

test("token expirado é renovado na restauração da sessão", async ({ page }) => {
  const calls = await mockApi(page, { expiredToken: TOKEN });

  await page.addInitScript(({ key, tokens }) => {
    if (!sessionStorage.getItem(key)) {
      sessionStorage.setItem(key, JSON.stringify(tokens));
    }
  }, { key: SESSION_KEY, tokens: TOKENS });

  await page.goto("/");
  await expectAuthenticated(page);
  await expect.poll(() => storedSession(page)).toEqual(ROTATED);

  expect(calls).toEqual([
    {
      method: "GET",
      path: "/api/v1/users/me",
      authorization: `Bearer ${TOKEN}`,
      body: null
    },
    {
      method: "POST",
      path: "/api/v1/auth/refresh",
      authorization: undefined,
      body: { refresh_token: TOKENS.refresh_token }
    },
    {
      method: "GET",
      path: "/api/v1/users/me",
      authorization: `Bearer ${ROTATED.access_token}`,
      body: null
    }
  ]);
});

test("refresh recusado encerra a sessão", async ({ page }) => {
  const calls = await mockApi(page, { meStatus: 401, refreshStatus: 401 });

  await page.addInitScript(({ key, tokens }) => {
    sessionStorage.setItem(key, JSON.stringify(tokens));
  }, { key: SESSION_KEY, tokens: TOKENS });

  await page.goto("/");

  await expect(page.getByRole("alert"))
    .toHaveText("Sua sessão expirou ou não é válida. Entre novamente.");
  await expect.poll(() => storedSession(page)).toBeNull();

  expect(calls.map((call) => call.path)).toEqual([
    "/api/v1/users/me",
    "/api/v1/auth/refresh"
  ]);
});

test("um token renovado que também é recusado não causa um loop", async ({ page }) => {
  const calls = await mockApi(page, { meStatus: 401 });

  await page.addInitScript(({ key, tokens }) => {
    sessionStorage.setItem(key, JSON.stringify(tokens));
  }, { key: SESSION_KEY, tokens: TOKENS });

  await page.goto("/");
  await expect(page.getByRole("alert"))
    .toHaveText("Sua sessão expirou ou não é válida. Entre novamente.");
  await expect.poll(() => storedSession(page)).toBeNull();

  expect(calls.map((call) => call.path)).toEqual([
    "/api/v1/users/me",
    "/api/v1/auth/refresh",
    "/api/v1/users/me"
  ]);
});

test("pedidos protegidos concorrentes usam uma única renovação", async ({ page }) => {
  const options = {};
  let releaseRefresh;
  options.waitForRefresh = new Promise((resolve) => { releaseRefresh = resolve; });
  const calls = await mockApi(page, options);
  await page.goto("/");
  await fillLogin(page);
  await submitLogin(page);
  await expectAuthenticated(page);

  options.expiredToken = TOKEN;

  const pending = page.evaluate(() => Promise.all(["a", "b"].map((id) =>
    requestProtected({ id, method: "GET", path: "/users/me" })
  )));
  const getCount = () => calls.filter((call) => call.path === "/api/v1/users/me").length;

  try {
    await expect.poll(getCount).toBe(3);
    await expect.poll(() => calls.filter((call) =>
      call.path === "/api/v1/auth/refresh").length).toBe(1);
  } finally {
    releaseRefresh();
  }

  expect((await pending).map((response) => response.status)).toEqual([200, 200]);
  expect(calls.filter((call) => call.path === "/api/v1/auth/refresh")).toHaveLength(1);
  expect(calls.filter((call) => call.authorization ===
    `Bearer ${ROTATED.access_token}`)).toHaveLength(2);
  await expect.poll(() => storedSession(page)).toEqual(ROTATED);
});

test("falha no logout não mantém a sessão local", async ({ page }) => {
  const calls = await mockApi(page, { abortLogout: true });
  await page.goto("/");
  await fillLogin(page);
  await submitLogin(page);
  await expectAuthenticated(page);

  await page.getByRole("button", { name: "Sair", exact: true }).click();

  await expect.poll(() => storedSession(page)).toBeNull();
  await expect.poll(() => calls.filter((call) =>
    call.path === "/api/v1/auth/logout").length).toBe(1);
  await page.reload();
  await expect(page.getByRole("button", { name: "Entrar", exact: true }))
    .toBeEnabled();
});

test("login informa o limite de tentativas e o tempo de espera", async ({ page }) => {
  await mockApi(page, { loginStatus: 429, retryAfter: "37" });
  await page.goto("/");
  await fillLogin(page);
  await submitLogin(page);

  await expect(page.getByRole("alert"))
    .toHaveText("Muitas tentativas. Aguarde 37 segundos antes de tentar novamente.");
  await expect(page.getByRole("button", { name: "Entrar", exact: true }))
    .toBeEnabled();
});

test("cadastro informa o limite de tentativas sem Retry-After", async ({ page }) => {
  await mockApi(page, { registrationStatus: 429 });
  await page.goto("/");
  await fillRegistration(page);
  await submitRegistration(page);

  await expect(page.getByRole("alert"))
    .toHaveText("Muitas tentativas. Aguarde antes de tentar novamente.");
});

test("sessão antiga sem refresh token exige um novo login", async ({ page }) => {
  const calls = await mockApi(page);
  await page.addInitScript(() => {
    sessionStorage.setItem("finance.token", "token-antigo");
  });

  await page.goto("/");
  await expect(page.getByRole("button", { name: "Entrar", exact: true }))
    .toBeEnabled();

  expect(await page.evaluate(() => sessionStorage.getItem("finance.token"))).toBeNull();
  expect(calls).toHaveLength(0);
});

test("login só é confirmado depois da consulta do usuário", async ({
  page
}) => {
  await mockApi(page, { meStatus: 503 });

  await page.goto("/");
  await fillLogin(page);
  await submitLogin(page);

  await expect(page.getByRole("alert"))
    .toHaveText(
      "Não foi possível consultar sua conta. Tente entrar novamente."
    );

  await expect(page.getByText("Bem-vindo!", { exact: true }))
    .not.toBeVisible();

  expect(await storedSession(page)).toBeNull();
});

test("falha de conexão permite tentar o login novamente", async ({
  page
}) => {
  await page.route("**/api/v1/auth/login", (route) => route.abort());

  await page.goto("/");
  await fillLogin(page);
  await submitLogin(page);

  await expect(page.getByRole("alert"))
    .toHaveText("Não foi possível conectar ao servidor.");

  await expect(
    page.getByRole("button", { name: "Entrar", exact: true })
  ).toBeEnabled();
});

test("armazenamento bloqueado não impede o login em memória", async ({
  page
}) => {
  await mockApi(page);

  await page.addInitScript(() => {
    Storage.prototype.getItem = function () {
      throw new Error("Armazenamento bloqueado");
    };

    Storage.prototype.setItem = function () {
      throw new Error("Armazenamento bloqueado");
    };

    Storage.prototype.removeItem = function () {
      throw new Error("Armazenamento bloqueado");
    };
  });

  await page.goto("/");
  await fillLogin(page);
  await submitLogin(page);
  await expectAuthenticated(page);

  await page.getByRole("button", { name: "Sair", exact: true }).click();

  await expect(
    page.getByRole("button", { name: "Entrar", exact: true })
  ).toBeVisible();
});