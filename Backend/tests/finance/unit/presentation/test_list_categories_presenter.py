import json

import pytest

from app.finance.application.dtos.list_categories import CategoryOutput
from app.finance.presentation.api.v1.presenters.list_categories_presenter import (
    ListCategoriesHttpPresenter,
)


def test_lista_de_categorias_vira_200_dentro_de_um_objeto() -> None:
    presenter = ListCategoriesHttpPresenter()

    presenter.present_categories(
        (CategoryOutput(kind="expense", name="saude", label="Saúde"),)
    )

    resposta = presenter.response()
    assert resposta.status_code == 200
    assert json.loads(bytes(resposta.body)) == {
        "categories": [{"kind": "expense", "name": "saude", "label": "Saúde"}]
    }


def test_sem_nenhum_resultado_e_um_erro_claro() -> None:
    with pytest.raises(RuntimeError, match="sem apresentar"):
        ListCategoriesHttpPresenter().response()
