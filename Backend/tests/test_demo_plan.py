from datetime import date

from app.demo_plan import CARTAO, CARTEIRA, CORRENTE, build_plan

HOJE = date(2026, 11, 20)


def test_cria_as_tres_contas() -> None:
    plano = build_plan(HOJE)

    assert [(c.name, c.kind) for c in plano.accounts] == [
        (CARTEIRA, "wallet"),
        (CORRENTE, "checking"),
        (CARTAO, "credit_card"),
    ]


def test_cobre_os_tres_meses_anteriores_e_o_atual_sem_passar_de_hoje() -> None:
    plano = build_plan(HOJE)

    datas = [t.occurred_on for t in plano.transactions]
    assert min(datas) >= date(2026, 8, 1)
    assert max(datas) <= HOJE
    meses = {(d.year, d.month) for d in datas}
    assert meses == {(2026, 8), (2026, 9), (2026, 10), (2026, 11)}


def test_tem_salario_mensal_aluguel_e_um_freelance() -> None:
    plano = build_plan(HOJE)

    salarios = [t for t in plano.transactions if t.description == "Salário"]
    alugueis = [t for t in plano.transactions if t.description == "Aluguel"]
    freelances = [t for t in plano.transactions if "Freelance" in t.description]
    assert len(salarios) == len(alugueis) == 4
    assert len(freelances) == 1
    assert all(t.kind == "income" for t in salarios + freelances)


def test_algumas_despesas_ficam_sem_categoria_para_mostrar_o_categorizador() -> None:
    plano = build_plan(HOJE)

    sem_categoria = [t for t in plano.transactions if t.category is None]
    com_categoria = [t for t in plano.transactions if t.category is not None]
    assert sem_categoria
    assert com_categoria


def test_tem_uma_transferencia_por_mes_da_corrente_para_a_carteira() -> None:
    plano = build_plan(HOJE)

    assert len(plano.transfers) == 4
    assert {(t.source, t.destination) for t in plano.transfers} == {
        (CORRENTE, CARTEIRA)
    }


def test_tem_uma_recorrencia_mensal_e_uma_semanal_a_partir_de_hoje() -> None:
    plano = build_plan(HOJE)

    assert {r.frequency for r in plano.recurrences} == {"monthly", "weekly"}
    assert all(r.starts_on == HOJE for r in plano.recurrences)


def test_e_deterministico() -> None:
    assert build_plan(HOJE) == build_plan(HOJE)


def test_no_inicio_do_mes_so_inclui_o_que_ja_aconteceu() -> None:
    plano = build_plan(date(2026, 11, 1))

    assert max(t.occurred_on for t in plano.transactions) <= date(2026, 11, 1)


def test_dia_28_em_fevereiro_e_ajustado_sem_quebrar() -> None:
    plano = build_plan(date(2027, 2, 28))

    assert all(t.occurred_on.month in {11, 12, 1, 2} for t in plano.transactions)
