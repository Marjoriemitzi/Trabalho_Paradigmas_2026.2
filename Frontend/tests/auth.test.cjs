const { test, before, after } = require("node:test");
const assert = require("node:assert/strict");
const http = require("node:http");
const { spawn } = require("node:child_process");
const { chromium } = require("playwright");
const { once } = require("node:events");
let browser, mock, frontend, base, requests, behavior;
const profile = {
  id: "17c263e5-2b67-4268-a3a2-cc06409c81ec",
  email: "arthur@exemplo.com",
  role: "user",
};
const password = "S3nha!Forte123";
async function freePort() {
  const s = http.createServer();
  s.listen(0, "127.0.0.1");
  await once(s, "listening");
  const p = s.address().port;
  await new Promise((r) => s.close(r));
  return p;
}
before(async () => {
  mock = http.createServer(async (req, res) => {
    let body = "";
    for await (const part of req) body += part;
    const data = body ? JSON.parse(body) : null;
    requests.push({
      method: req.method,
      path: req.url,
      data,
      authorization: req.headers.authorization,
    });
    const result = behavior(req, data);
    if (result.delay) await new Promise((r) => setTimeout(r, result.delay));
    res.writeHead(result.status, { "Content-Type": "application/json" });
    res.end(
      typeof result.body === "string"
        ? result.body
        : JSON.stringify(result.body),
    );
  });
  mock.listen(0, "127.0.0.1");
  await once(mock, "listening");
  const port = await freePort();
  base = `http://127.0.0.1:${port}`;
  frontend = spawn(process.execPath, ["scripts/dev.mjs", "--skip-build"], {
    cwd: process.cwd(),
    env: {
      ...process.env,
      PORT: String(port),
      BACKEND_URL: `http://127.0.0.1:${mock.address().port}`,
    },
    stdio: ["ignore", "pipe", "inherit"],
  });
  await once(frontend.stdout, "data");
  browser = await chromium.launch({ headless: true });
});
after(async () => {
  await browser?.close();
  frontend?.kill();
  await new Promise((r) => mock?.close(r));
});
async function setup(options = {}) {
  requests = [];
  behavior = (req) =>
    req.url.endsWith("/login")
      ? {
          status: 200,
          body: {
            access_token: "test-token",
            token_type: "bearer",
            expires_in: 1800,
          },
        }
      : { status: req.method === "POST" ? 201 : 200, body: profile };
  const context = await browser.newContext({
    viewport: { width: 1365, height: 900 },
    ...options,
  });
  const page = await context.newPage();
  page.setDefaultTimeout(10000);
  await page.goto(base);
  return { page, context };
}
async function fill(
  page,
  {
    register = false,
    email = profile.email,
    pass = password,
    confirmation = pass,
  } = {},
) {
  if (register)
    await page
      .getByRole("button", { name: "Criar conta", exact: true })
      .click();
  await page.getByLabel("E-mail", { exact: true }).fill(email);
  await page.getByLabel("Senha", { exact: true }).fill(pass);
  if (register) await page.getByLabel("Confirme sua senha").fill(confirmation);
}
async function submit(page, register = false) {
  await page
    .getByRole("button", {
      name: register ? "Criar minha conta" : "Entrar na minha conta",
    })
    .click();
}
async function signedIn(page) {
  await page.getByRole("heading", { name: "Bem-vindo ao Saldo" }).waitFor();
}

test("login envia o contrato exato, valida /me, restaura a sessão e sai", async () => {
  const { page, context } = await setup();
  try {
    await fill(page, { email: " ARTHUR@EXEMPLO.COM " });
    await submit(page);
    await signedIn(page);
    assert.deepEqual(requests[0], {
      method: "POST",
      path: "/api/v1/auth/login",
      data: { email: profile.email, password },
      authorization: undefined,
    });
    assert.equal(requests[1].authorization, "Bearer test-token");
    const saved = await page.evaluate(() =>
      JSON.parse(sessionStorage.getItem("saldo.session.v1")),
    );
    assert.equal(saved.value, "test-token");
    assert(!JSON.stringify(saved).includes(password));
    await page.reload();
    await signedIn(page);
    assert.equal(requests.at(-1).path, "/api/v1/users/me");
    await page.getByRole("button", { name: "Sair da conta" }).click();
    await page
      .getByRole("heading", { name: "Que bom ter você aqui" })
      .waitFor();
    assert.equal(
      await page.evaluate(() => sessionStorage.getItem("saldo.session.v1")),
      null,
    );
    await page.waitForFunction(
      () => document.getElementById("password").value === "",
    );
  } finally {
    await context.close();
  }
});
test("cadastro confirma senha localmente e retorna ao login sem persistir segredo", async () => {
  const { page, context } = await setup();
  try {
    await fill(page, { register: true });
    await submit(page, true);
    await page
      .getByRole("status")
      .filter({ hasText: "Conta criada com sucesso" })
      .waitFor();
    assert.deepEqual(
      requests.map((r) => [r.method, r.path, r.data]),
      [["POST", "/api/v1/users", { email: profile.email, password }]],
    );
    await page.waitForFunction(
      () => document.getElementById("password").value === "",
    );
    assert.equal(await page.evaluate(() => sessionStorage.length), 0);
    await fill(page);
    await submit(page);
    await signedIn(page);
  } finally {
    await context.close();
  }
});
test("campos inválidos e confirmação divergente não chegam à API", async () => {
  const { page, context } = await setup();
  try {
    await submit(page);
    await page
      .getByText("Informe um e-mail válido.", { exact: true })
      .waitFor();
    assert.equal(requests.length, 0);
    await fill(page, { register: true, pass: "fraca", confirmation: "outra" });
    await submit(page, true);
    await page.getByText("As senhas não coincidem.", { exact: true }).waitFor();
    await page
      .getByText("A senha precisa atender a todos os requisitos abaixo.")
      .waitFor();
    assert.equal(requests.length, 0);
    await page
      .getByRole("button", { name: "Mostrar senha", exact: true })
      .click();
    await page.waitForFunction(
      () => document.getElementById("password").type === "text",
    );
    await page.getByRole("button", { name: "Entrar", exact: true }).click();
    await page.waitForFunction(
      () => document.getElementById("password").value === "",
    );
  } finally {
    await context.close();
  }
});
for (const scenario of [
  {
    name: "credenciais incorretas",
    status: 401,
    code: "invalid_credentials",
    text: "E-mail ou senha incorretos.",
    register: false,
  },
  {
    name: "e-mail duplicado",
    status: 409,
    code: "email_taken",
    text: "Este e-mail já está cadastrado.",
    register: true,
  },
  {
    name: "e-mail recusado pelo servidor",
    status: 422,
    code: "invalid_email",
    text: "O e-mail informado não é válido.",
    register: true,
  },
  {
    name: "política Prolog",
    status: 422,
    code: "weak_password",
    reasons: ["no_symbol"],
    text: "Inclua um símbolo.",
    register: true,
  },
  {
    name: "limite de tentativas",
    status: 429,
    code: "too_many_requests",
    text: "Muitas tentativas.",
    register: false,
  },
  {
    name: "erro interno",
    status: 500,
    code: "internal_error",
    text: "O serviço está temporariamente indisponível.",
    register: false,
  },
  {
    name: "erros de campo",
    status: 422,
    code: "invalid_request",
    fields: [{ field: "email", problem: "invalid" }],
    text: "Confira os dados informados",
    register: true,
  },
])
  test(`apresenta ${scenario.name} e permite nova tentativa`, async () => {
    const { page, context } = await setup();
    try {
      behavior = () => ({
        status: scenario.status,
        body: {
          error: scenario.code,
          reasons: scenario.reasons || [],
          fields: scenario.fields || [],
        },
      });
      await fill(page, { register: scenario.register });
      await submit(page, scenario.register);
      await page
        .getByRole("alert")
        .filter({ hasText: scenario.text })
        .waitFor();
      assert.equal(
        await page
          .getByRole("button", {
            name: scenario.register
              ? "Criar minha conta"
              : "Entrar na minha conta",
          })
          .isEnabled(),
        true,
      );
      assert.equal(await page.evaluate(() => sessionStorage.length), 0);
    } finally {
      await context.close();
    }
  });
test("resposta inesperada não quebra a tela", async () => {
  const { page, context } = await setup();
  try {
    behavior = () => ({ status: 200, body: "<html>erro</html>" });
    await fill(page);
    await submit(page);
    await page
      .getByRole("alert")
      .filter({ hasText: "resposta inesperada" })
      .waitFor();
  } finally {
    await context.close();
  }
});
test("login não impõe a política de senha do cadastro", async () => {
  const { page, context } = await setup();
  try {
    await fill(page, { pass: "curta" });
    await submit(page);
    await signedIn(page);
    assert.equal(requests[0].data.password, "curta");
  } finally {
    await context.close();
  }
});
test("respostas antigas são ignoradas e envio duplicado é bloqueado", async () => {
  const { page, context } = await setup();
  try {
    behavior = () => ({
      status: 200,
      body: { access_token: "old", expires_in: 1800 },
      delay: 400,
    });
    await fill(page);
    await submit(page);
    assert.equal(
      await page.getByRole("button", { name: "Entrando…" }).isDisabled(),
      true,
    );
    await page
      .getByRole("button", { name: "Criar conta", exact: true })
      .click();
    await page.waitForTimeout(650);
    await page
      .getByRole("heading", { name: "Comece sua organização" })
      .waitFor();
    assert.equal(requests.length, 1);
    assert.equal(await page.evaluate(() => sessionStorage.length), 0);
  } finally {
    await context.close();
  }
});
test("token rejeitado por /me é descartado", async () => {
  const { page, context } = await setup();
  try {
    const previous = behavior;
    behavior = (req) =>
      req.url.endsWith("/me")
        ? { status: 401, body: { error: "invalid_token" } }
        : previous(req);
    await fill(page);
    await submit(page);
    await page
      .getByRole("status")
      .filter({ hasText: "não é mais válida" })
      .waitFor();
    assert.equal(await page.evaluate(() => sessionStorage.length), 0);
  } finally {
    await context.close();
  }
});
test("falha temporária em /me permite tentar novamente", async () => {
  const { page, context } = await setup();
  try {
    const previous = behavior;
    behavior = (req) =>
      req.url.endsWith("/me")
        ? { status: 503, body: { error: "internal_error" } }
        : previous(req);
    await fill(page);
    await submit(page);
    await page
      .getByRole("button", { name: "Tentar novamente", exact: true })
      .waitFor();
    behavior = previous;
    await page
      .getByRole("button", { name: "Tentar novamente", exact: true })
      .click();
    await signedIn(page);
  } finally {
    await context.close();
  }
});
test("sessão expira e armazenamento corrompido não impede o acesso", async () => {
  const { page, context } = await setup();
  try {
    await page.evaluate(() =>
      sessionStorage.setItem("saldo.session.v1", "{quebrado"),
    );
    await page.reload();
    await fill(page);
    const previous = behavior;
    behavior = (req) =>
      req.url.endsWith("/login")
        ? { status: 200, body: { access_token: "short", expires_in: 2 } }
        : previous(req);
    await submit(page);
    await signedIn(page);
    await page
      .getByRole("status")
      .filter({ hasText: "Sua sessão expirou" })
      .waitFor();
    assert.equal(await page.evaluate(() => sessionStorage.length), 0);
  } finally {
    await context.close();
  }
});
test("funciona sem armazenamento disponível", async () => {
  const { page, context } = await setup();
  try {
    await page.addInitScript(() => {
      Storage.prototype.setItem = () => {
        throw new Error("denied");
      };
    });
    await page.reload();
    await fill(page);
    await submit(page);
    await signedIn(page);
  } finally {
    await context.close();
  }
});
test("layout móvel não apresenta rolagem horizontal", async () => {
  const { page, context } = await setup({
    viewport: { width: 375, height: 812 },
  });
  try {
    await fill(page, { register: true });
    assert.equal(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
      true,
    );
    await page
      .getByRole("button", { name: "Criar minha conta" })
      .scrollIntoViewIfNeeded();
    assert.equal(
      await page
        .getByLabel("E-mail", { exact: true })
        .getAttribute("autocomplete"),
      "email",
    );
    assert.equal(
      await page
        .getByLabel("Senha", { exact: true })
        .getAttribute("autocomplete"),
      "new-password",
    );
    await page.screenshot({ path: "/tmp/saldo-mobile.png", fullPage: true });
  } finally {
    await context.close();
  }
});
test("sem conexão exibe mensagem recuperável", async () => {
  const { page, context } = await setup();
  try {
    await page.route("**/api/v1/auth/login", (route) => route.abort());
    await fill(page);
    await submit(page);
    await page
      .getByRole("alert")
      .filter({ hasText: "Não foi possível conectar" })
      .waitFor();
  } finally {
    await context.close();
  }
});
