const { test, expect } = require("@playwright/test");

const SESSION_KEY = "finance.token";
const TOKEN = "token-de-teste";
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
          ? {
              access_token: TOKEN,
              token_type: "bearer",
              expires_in: 1800
            }
          : { error: "invalid_credentials" };
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
                status === 409 ? "email_taken" : "weak_password"
            };
    } else if (
      call.method === "GET" &&
      call.path === "/api/v1/users/me"
    ) {
      status = options.meStatus ?? 200;
      body =
        status === 200
          ? USER
          : { error: "invalid_token" };
    } else {
      status = 404;
      body = { error: "not_found" };
    }

    await route.fulfill({
      status,
      contentType: "application/json",
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

async function storedToken(page) {
  return page.evaluate(
    (key) => sessionStorage.getItem(key),
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

  await expect.poll(() => storedToken(page)).toBe(TOKEN);
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
  expect(await storedToken(page)).toBeNull();
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

  expect(await storedToken(page)).toBeNull();
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

  await expect.poll(() => storedToken(page)).toBe(TOKEN);

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

  await expect.poll(() => storedToken(page)).toBe(TOKEN);

  await page.getByRole("button", { name: "Sair", exact: true }).click();

  await expect.poll(() => storedToken(page)).toBeNull();

  await page.reload();

  await expect(
    page.getByRole("button", { name: "Entrar", exact: true })
  ).toBeVisible();

  expect(
    calls.filter((call) => call.path === "/api/v1/users/me")
  ).toHaveLength(1);
});

test("token salvo recusado pelo backend é removido", async ({
  page
}) => {
  const calls = await mockApi(page, { meStatus: 401 });

  await page.addInitScript(
    ({ key, token }) => sessionStorage.setItem(key, token),
    { key: SESSION_KEY, token: "token-expirado" }
  );

  await page.goto("/");

  await expect(page.getByRole("alert"))
    .toHaveText("Sua sessão expirou ou não é válida. Entre novamente.");

  await expect.poll(() => storedToken(page)).toBeNull();

  expect(calls).toHaveLength(1);

  expect(calls[0]).toMatchObject({
    path: "/api/v1/users/me",
    authorization: "Bearer token-expirado"
  });
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

  expect(await storedToken(page)).toBeNull();
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