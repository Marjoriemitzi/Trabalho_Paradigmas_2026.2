const { test, expect } = require("@playwright/test");

const accountId = "15369e71-f990-489f-b0c4-343e01c44c2b";
const targetId = "7445a82d-9981-4faf-bf71-714220e503b3";
const entryId = "f676a96f-0e0c-4b03-b879-92df8e3ff8a7";
const day = "2026-11-23";
const market = { kind: "expense", name: "mercado", label: "Mercado" };
const salary = { kind: "income", name: "salario", label: "Salário" };

async function mock(page, options = {}) {
  const calls = [];
  let entry = null;
  await page.addInitScript(() => {
    sessionStorage.setItem("finance.session", JSON.stringify({
      access_token: "statement-test",
      refresh_token: "statement-refresh"
    }));
  });
  await page.route("**/api/v1/**", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const method = request.method();
    const payload = request.postDataJSON();
    calls.push({ method, url, payload });
    expect(request.headers().authorization).toBe("Bearer statement-test");

    if (url.pathname.endsWith("/users/me")) {
      return route.fulfill({ json: { id: "user-1", email: "user@example.com" } });
    }
    if (url.pathname.endsWith("/accounts")) {
      const balance = entry ? (entry.kind === "income" ? entry.amount_cents : -entry.amount_cents) : 0;
      return route.fulfill({ json: { accounts: [
        { id: accountId, name: "Principal", kind: "checking", balance_cents: balance },
        { id: targetId, name: "Reserva", kind: "wallet", balance_cents: 0 }
      ] } });
    }
    if (url.pathname.endsWith("/categories")) {
      return route.fulfill({ json: { categories: [market, salary] } });
    }
    if (!url.pathname.includes("/transactions")) {
      return route.fulfill({ status: 404, json: { error: "not_found" } });
    }
    if (method === "GET") {
      const from = url.searchParams.get("from");
      const to = url.searchParams.get("to");
      const account = url.searchParams.get("account_id");
      if (options.rejectPeriod && from === "2024-01-01") {
        return route.fulfill({
          status: 422,
          json: { error: "invalid_period", fields: [{ field: "to", problem: "too_long" }] }
        });
      }
      const expense = entry?.kind === "expense" ? entry.amount_cents : 0;
      const income = entry?.kind === "income" ? entry.amount_cents : 0;
      const transfers = account && options.withTransfer ? [{
        id: "transfer-1", from_account_id: targetId, to_account_id: accountId,
        occurred_on: day, description: "Reforço da reserva", amount_cents: 3000
      }] : [];
      return route.fulfill({ json: {
        from, to, account_id: account,
        opening_balance_cents: 20000, income_cents: income, expense_cents: expense,
        transfers_in_cents: transfers.length ? 3000 : 0, transfers_out_cents: 0,
        closing_balance_cents: 20000 + income - expense + (transfers.length ? 3000 : 0),
        transactions: entry ? [entry] : [], transfers
      } });
    }
    if (method === "DELETE") {
      entry = null;
      return route.fulfill({ status: 204 });
    }
    entry = {
      ...payload, id: entryId, category: payload.category ?? market.name, recurrence_id: null
    };
    return route.fulfill({ status: method === "POST" ? 201 : 200, json: { ...entry, warnings: [] } });
  });
  await page.goto("/");
  const statement = page.getByRole("region", { name: "Extrato e lançamentos" });
  await expect(statement.getByRole("button", { name: "Novo lançamento" })).toBeEnabled();

  return { calls, statement };
}

async function applyPeriod(statement, from = "2026-11-01", to = "2026-11-30") {
  await statement.getByLabel("Data inicial").fill(from);
  await statement.getByLabel("Data final").fill(to);
  await statement.getByRole("button", { name: "Consultar extrato" }).click();
}

test("consulta o período consolidado e exibe transferências apenas ao filtrar por conta", async ({ page }) => {
  const { calls, statement } = await mock(page, { withTransfer: true });

  await applyPeriod(statement);
  await expect(statement.getByRole("heading", { name: "Extrato de 01/11/2026 a 30/11/2026" })).toBeVisible();
  await expect(statement.getByText("Transferências recebidas")).toHaveCount(0);
  const first = calls.find(({ url }) => url.pathname.endsWith("/transactions"));
  expect(Object.fromEntries(first.url.searchParams)).toEqual({
    from: "2026-11-01", to: "2026-11-30"
  });

  await statement.getByLabel("Filtrar por conta").selectOption(accountId);
  await statement.getByRole("button", { name: "Consultar extrato" }).click();
  await expect(statement.getByRole("heading", { name: "Transferências do período" })).toBeVisible();
  await expect(statement.getByText("Reserva → Principal", { exact: false })).toBeVisible();
  await expect(statement.getByText("Transferências recebidas")).toBeVisible();
  await expect(statement.getByText("R$ 230,00")).toBeVisible();
  expect(calls.at(-1).url.searchParams.get("account_id")).toBe(accountId);
});

test("cria, edita e exclui lançamento, atualizando o extrato e o saldo da conta", async ({ page }) => {
  const { calls, statement } = await mock(page);
  const accounts = page.getByRole("region", { name: "Contas financeiras" });

  await statement.getByRole("button", { name: "Novo lançamento" }).click();
  await statement.getByLabel("Valor em reais").fill("10,09");
  await statement.getByLabel("Descrição").fill("Supermercado local");
  await statement.getByLabel("Data do lançamento").fill(day);
  await expect(statement.getByLabel("Categoria")).toHaveValue("");
  await statement.getByRole("button", { name: "Salvar lançamento" }).click();

  await expect(statement.getByRole("heading", { name: "Supermercado local" })).toBeVisible();
  await expect(statement.getByRole("heading", { name: "Extrato de 23/11/2026 a 23/11/2026" })).toBeVisible();
  await expect(statement.getByText("Principal · Mercado", { exact: false })).toBeVisible();
  await expect(accounts.getByRole("listitem").filter({ hasText: "Principal" })).toContainText("-R$ 10,09");
  const created = calls.find(({ method }) => method === "POST");
  expect(created.payload).toEqual({
    account_id: accountId, kind: "expense", amount_cents: 1009,
    description: "Supermercado local", occurred_on: day, category: null
  });

  await statement.getByRole("button", { name: "Editar lançamento" }).click();
  await expect(statement.getByLabel("Valor em reais")).toHaveValue("10,09");
  await expect(statement.getByLabel("Categoria")).toHaveValue("mercado");
  await statement.getByLabel("Tipo de lançamento").selectOption("income");
  await expect(statement.getByLabel("Categoria")).toHaveValue("");
  await expect(statement.getByLabel("Categoria").locator('option[value="mercado"]')).toHaveCount(0);
  await statement.getByLabel("Categoria").selectOption("salario");
  await statement.getByLabel("Descrição").fill("Pagamento");
  await statement.getByRole("button", { name: "Salvar lançamento" }).click();
  await expect(statement.getByRole("heading", { name: "Pagamento" })).toBeVisible();
  await expect(statement.getByText("Salário", { exact: false })).toBeVisible();
  await expect(accounts.getByRole("listitem").filter({ hasText: "Principal" })).toContainText("R$ 10,09");
  expect(calls.find(({ method }) => method === "PUT")).toMatchObject({
    payload: { kind: "income", category: "salario", amount_cents: 1009 }
  });
  expect(calls.find(({ method }) => method === "PUT").url.pathname).toBe(`/api/v1/transactions/${entryId}`);

  await statement.getByRole("button", { name: "Excluir lançamento" }).click();
  await statement.getByRole("button", { name: "Cancelar" }).click();
  expect(calls.some(({ method }) => method === "DELETE")).toBe(false);
  await statement.getByRole("button", { name: "Excluir lançamento" }).click();
  await statement.getByRole("button", { name: "Confirmar exclusão" }).click();

  await expect(statement.getByText("Nenhum lançamento no período.")).toBeVisible();
  await expect(accounts.getByRole("listitem").filter({ hasText: "Principal" })).toContainText("R$ 0,00");
  expect(calls.find(({ method }) => method === "DELETE").url.pathname).toBe(`/api/v1/transactions/${entryId}`);
});

test("orienta sobre datas invertidas e sobre o limite de 366 dias", async ({ page }) => {
  const { calls, statement } = await mock(page, { rejectPeriod: true });
  await applyPeriod(statement, "2026-11-30", "2026-11-01");
  await expect(statement.getByRole("alert")).toHaveText("A data inicial deve ser anterior ou igual à final.");
  expect(calls.some(({ url }) => url.pathname.endsWith("/transactions"))).toBe(false);

  await applyPeriod(statement, "2024-01-01", "2026-11-30");
  await expect(statement.getByRole("alert")).toContainText("até 366 dias");
});

test("recusa valor com mais de duas casas sem enviar o lançamento", async ({ page }) => {
  const { calls, statement } = await mock(page);
  await statement.getByRole("button", { name: "Novo lançamento" }).click();
  await statement.getByLabel("Valor em reais").fill("10,001");
  await statement.getByLabel("Descrição").fill("Compra");
  await statement.getByLabel("Data do lançamento").fill(day);
  await statement.getByRole("button", { name: "Salvar lançamento" }).click();

  await expect(statement.getByRole("alert")).toContainText("até duas casas decimais");
  expect(calls.some(({ method }) => method === "POST")).toBe(false);
});
