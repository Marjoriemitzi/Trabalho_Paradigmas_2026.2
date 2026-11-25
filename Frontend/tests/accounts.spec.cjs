const { test, expect } = require("@playwright/test");

const ACCOUNT_ID = "b74395ab-57ff-4add-8fba-b73729a80de0";
const ACCESS_TOKEN = "finance-test";
const PROFILE = {
  id: "c9fb9a7e-0ff1-4d8e-af53-ee69e629836a",
  email: "finance@example.com"
};
const EXISTING = {
  id: ACCOUNT_ID,
  name: "Conta principal",
  kind: "checking",
  balance_cents: -123456
};

async function openAccounts(page, handleAccounts) {
  await page.addInitScript((token) => {
    sessionStorage.setItem("finance.session", JSON.stringify({
      access_token: token,
      refresh_token: "finance-refresh"
    }));
  }, ACCESS_TOKEN);
  await page.route("**/api/v1/users/me", (route) => route.fulfill({ json: PROFILE }));
  await page.route(/\/api\/v1\/accounts(?:\/[^?]+)?$/, handleAccounts);
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Contas financeiras" })).toBeVisible();
}

test("lista as contas com o Bearer, o tipo e o saldo em reais", async ({ page }) => {
  await openAccounts(page, (route) => {
    expect(route.request().method()).toBe("GET");
    expect(route.request().headers().authorization).toBe(`Bearer ${ACCESS_TOKEN}`);
    return route.fulfill({ json: { accounts: [
      EXISTING,
      { ...EXISTING, id: "outro-id", name: "Cartão", kind: "credit_card", balance_cents: 5 },
      { ...EXISTING, id: "mais-um-id", name: "Reserva", kind: "wallet", balance_cents: 214748364899 }
    ] } });
  });

  const principal = page.getByRole("listitem").filter({ hasText: "Conta principal" });
  await expect(principal).toContainText("Conta corrente");
  await expect(principal).toContainText("-R$ 1.234,56");
  await expect(page.getByText("Cartão de crédito", { exact: true })).toBeVisible();
  await expect(page.getByText("R$ 0,05", { exact: false })).toBeVisible();
  await expect(page.getByText("R$ 2.147.483.648,99", { exact: false })).toBeVisible();
});

test("cria, renomeia e exclui uma conta, recarregando a lista após cada operação", async ({ page }) => {
  const calls = [];
  let accounts = [];

  await openAccounts(page, async (route) => {
    const request = route.request();
    const method = request.method();
    const path = new URL(request.url()).pathname;
    const payload = request.postDataJSON();
    calls.push({ method, path, payload });
    expect(request.headers().authorization).toBe(`Bearer ${ACCESS_TOKEN}`);

    if (method === "GET") return route.fulfill({ json: { accounts } });

    if (method === "POST") {
      const account = { id: ACCOUNT_ID, ...payload };
      accounts = [{ ...account, balance_cents: 250000 }];
      return route.fulfill({ status: 201, json: account });
    }

    if (method === "PATCH") {
      accounts[0].name = payload.name;
      return route.fulfill({ json: { id: ACCOUNT_ID, name: payload.name, kind: "credit_card" } });
    }

    accounts = [];
    return route.fulfill({ status: 204 });
  });

  const empty = page.getByText("Você ainda não tem contas cadastradas.");
  await expect(empty).toBeVisible();
  await page.getByRole("button", { name: "Nova conta" }).click();
  await page.getByLabel("Nome da conta").fill("  Viagens  ");
  await page.getByLabel("Tipo de conta").selectOption("credit_card");
  await page.getByRole("button", { name: "Salvar" }).click();
  await expect(page.getByRole("listitem")).toContainText("Viagens");
  await expect(page.getByRole("listitem")).toContainText("R$ 2.500,00");

  await page.getByRole("button", { name: "Renomear" }).click();
  await expect(page.getByLabel("Nome da conta")).toHaveValue("Viagens");
  await expect(page.getByLabel("Tipo de conta")).toHaveCount(0);
  await page.getByLabel("Nome da conta").fill("Férias");
  await page.getByRole("button", { name: "Salvar" }).click();
  await expect(page.getByRole("listitem")).toContainText("Férias");

  await page.getByRole("button", { name: "Excluir", exact: true }).click();
  await expect(page.getByText("Deseja excluir a conta “Férias”?")).toBeVisible();
  await page.getByRole("button", { name: "Confirmar exclusão" }).click();
  await expect(empty).toBeVisible();

  expect(calls.map((call) => call.method)).toEqual([
    "GET", "POST", "GET", "PATCH", "GET", "DELETE", "GET"
  ]);
  expect(calls[1]).toMatchObject({
    path: "/api/v1/accounts",
    payload: { name: "Viagens", kind: "credit_card" }
  });
  expect(calls[3]).toEqual({
    method: "PATCH",
    path: `/api/v1/accounts/${ACCOUNT_ID}`, payload: { name: "Férias" }
  });
  expect(calls[5]).toEqual({
    method: "DELETE",
    path: `/api/v1/accounts/${ACCOUNT_ID}`, payload: null
  });
});

test("mostra conflito de nome e mantém os dados preenchidos", async ({ page }) => {
  await openAccounts(page, (route) => route.request().method() === "GET"
    ? route.fulfill({ json: { accounts: [EXISTING] } })
    : route.fulfill({ status: 409, json: { error: "account_name_taken" } }));

  await page.getByRole("button", { name: "Nova conta" }).click();
  await page.getByLabel("Nome da conta").fill(EXISTING.name);
  await page.getByRole("button", { name: "Salvar" }).click();

  await expect(page.getByRole("alert")).toHaveText("Já existe uma conta com esse nome.");
  await expect(page.getByLabel("Nome da conta")).toHaveValue(EXISTING.name);
  await expect(page.getByRole("button", { name: "Salvar" })).toBeEnabled();
});

test("pede confirmação e trata exclusão de conta em uso", async ({ page }) => {
  let deleteCount = 0;
  await openAccounts(page, (route) => {
    if (route.request().method() === "GET") {
      return route.fulfill({ json: { accounts: [EXISTING] } });
    }

    expect(route.request().method()).toBe("DELETE");
    deleteCount += 1;
    return route.fulfill({ status: 409, json: { error: "account_in_use" } });
  });

  await page.getByRole("button", { name: "Excluir", exact: true }).click();
  await page.getByRole("button", { name: "Cancelar" }).click();
  expect(deleteCount).toBe(0);

  await page.getByRole("button", { name: "Excluir", exact: true }).click();
  await page.getByRole("button", { name: "Confirmar exclusão" }).click();
  await expect(page.getByRole("alert")).toHaveText(
    "Esta conta tem transações ou transferências e não pode ser excluída."
  );
  await page.getByRole("button", { name: "Cancelar" }).click();
  await expect(page.getByRole("listitem")).toContainText(EXISTING.name);
  expect(deleteCount).toBe(1);
});

test("permite recarregar a lista após erro do servidor", async ({ page }) => {
  let attempts = 0;

  await openAccounts(page, (route) => {
    attempts += 1;
    return attempts === 1
      ? route.fulfill({ status: 500, json: { error: "internal_error" } })
      : route.fulfill({ json: { accounts: [EXISTING] } });
  });

  await expect(page.getByRole("alert")).toHaveText("Não foi possível carregar as contas.");
  await page.getByRole("button", { name: "Tentar novamente" }).click();
  await expect(page.getByRole("listitem")).toContainText(EXISTING.name);
  expect(attempts).toBe(2);
});
