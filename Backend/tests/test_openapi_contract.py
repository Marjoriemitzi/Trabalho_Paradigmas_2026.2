from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import pytest
from pydantic import SecretStr

from app.main import create_app
from app.shared.infrastructure.config.settings import Settings

HTTP_METHODS = frozenset(
    {"get", "post", "put", "patch", "delete", "options", "head", "trace"}
)
SUBSTRINGS_MONETARIAS = (
    "amount_cents",
    "balance_cents",
    "limit_cents",
    "spent_cents",
    "remaining_cents",
    "total_cents",
    "average_cents",
)
ROTAS_ESTRITAMENTE_PUBLICAS = frozenset(
    {
        ("POST", "/api/v1/users"),
        ("POST", "/api/v1/auth/login"),
        ("POST", "/api/v1/auth/refresh"),
    }
)
ROTAS_PUBLICAS_OU_AUTH_OPCIONAL = ROTAS_ESTRITAMENTE_PUBLICAS | frozenset(
    {("POST", "/api/v1/auth/logout")}
)

SchemaDict = dict[str, Any]


@pytest.fixture(scope="module")
def openapi_schema() -> SchemaDict:
    settings = Settings(
        database_url=SecretStr("postgresql+asyncpg://u:s@localhost/finance"),
        prolog_rules_dir=Path("rules"),
        jwt_secret=SecretStr("s" * 32),
        enable_docs=False,
    )
    return create_app(settings).openapi()


def _resolver_ref(spec: SchemaDict, ref: str) -> SchemaDict:
    prefix = "#/"
    if not ref.startswith(prefix):
        return {}
    atual: Any = spec
    for parte in ref.removeprefix(prefix).split("/"):
        if not isinstance(atual, dict) or parte not in atual:
            return {}
        atual = atual[parte]
    return atual if isinstance(atual, dict) else {}


def _iterar_operacoes(spec: SchemaDict) -> Iterator[tuple[str, str, SchemaDict]]:
    paths = spec.get("paths", {})
    if not isinstance(paths, dict):
        return
    for path, item in sorted(paths.items()):
        if not isinstance(item, dict):
            continue
        for method, op in sorted(item.items()):
            if method.lower() in HTTP_METHODS and isinstance(op, dict):
                yield method.upper(), path, op


def _descer_no_schema(
    origem: str,
    schema: object,
    visitados: set[int],
) -> Iterator[tuple[str, str, SchemaDict]]:
    if not isinstance(schema, dict) or id(schema) in visitados:
        return
    visitados.add(id(schema))

    props = schema.get("properties")
    if isinstance(props, dict):
        for prop_nome, prop_schema in sorted(props.items()):
            if isinstance(prop_schema, dict):
                yield f"{origem}.{prop_nome}", prop_nome, prop_schema
                yield from _descer_no_schema(
                    f"{origem}.{prop_nome}", prop_schema, visitados
                )

    for chave in ("items", "additionalProperties", "not"):
        sub = schema.get(chave)
        if isinstance(sub, dict):
            yield from _descer_no_schema(f"{origem}.{chave}", sub, visitados)

    for chave in ("anyOf", "oneOf", "allOf", "prefixItems"):
        lista = schema.get(chave)
        if isinstance(lista, list):
            for idx, item in enumerate(lista):
                yield from _descer_no_schema(
                    f"{origem}.{chave}[{idx}]", item, visitados
                )

    defs = schema.get("$defs")
    if isinstance(defs, dict):
        for def_nome, def_schema in sorted(defs.items()):
            yield from _descer_no_schema(
                f"{origem}.$defs.{def_nome}", def_schema, visitados
            )


def _iterar_propriedades_do_conteudo(
    origem: str,
    conteudo: object,
    visitados: set[int],
) -> Iterator[tuple[str, str, SchemaDict]]:
    if not isinstance(conteudo, dict):
        return
    for media_type, media_spec in sorted(conteudo.items()):
        if isinstance(media_spec, dict) and "schema" in media_spec:
            yield from _descer_no_schema(
                f"{origem}[{media_type}]", media_spec["schema"], visitados
            )


def _iterar_parametros(spec: SchemaDict) -> Iterator[tuple[str, str, SchemaDict]]:
    paths = spec.get("paths", {})
    if not isinstance(paths, dict):
        return
    for path, item in sorted(paths.items()):
        if not isinstance(item, dict):
            continue
        for param in item.get("parameters", []):
            if isinstance(param, dict) and isinstance(param.get("schema"), dict):
                yield f"path:{path}", str(param.get("name", "")), param["schema"]
        for method, op in sorted(item.items()):
            if method.lower() not in HTTP_METHODS or not isinstance(op, dict):
                continue
            for param in op.get("parameters", []):
                if isinstance(param, dict) and isinstance(param.get("schema"), dict):
                    yield (
                        f"{method.upper()} {path}",
                        str(param.get("name", "")),
                        param["schema"],
                    )


def _iterar_propriedades(spec: SchemaDict) -> Iterator[tuple[str, str, SchemaDict]]:
    visitados: set[int] = set()
    schemas = spec.get("components", {}).get("schemas", {})
    if isinstance(schemas, dict):
        for nome, schema in sorted(schemas.items()):
            yield from _descer_no_schema(f"components.{nome}", schema, visitados)

    for method, path, op in _iterar_operacoes(spec):
        origem_op = f"{method} {path}"
        req_body = op.get("requestBody")
        if isinstance(req_body, dict):
            yield from _iterar_propriedades_do_conteudo(
                f"{origem_op}.requestBody", req_body.get("content"), visitados
            )
        for status_code, resp in sorted(op.get("responses", {}).items()):
            if isinstance(resp, dict):
                yield from _iterar_propriedades_do_conteudo(
                    f"{origem_op}.responses[{status_code}]",
                    resp.get("content"),
                    visitados,
                )

    for origem, param_nome, param_schema in _iterar_parametros(spec):
        yield f"{origem}.param[{param_nome}]", param_nome, param_schema
        yield from _descer_no_schema(
            f"{origem}.param[{param_nome}]", param_schema, visitados
        )


def _e_schema_nulo(schema: SchemaDict) -> bool:
    return schema.get("type") == "null"


def _tipos_nao_nulos(schema: SchemaDict) -> list[str]:
    tipo = schema.get("type")
    if isinstance(tipo, str):
        return [] if tipo == "null" else [tipo]
    if isinstance(tipo, list):
        return [t for t in tipo if isinstance(t, str) and t != "null"]
    return []


def _ramos_nao_nulos(schema: SchemaDict) -> list[SchemaDict] | None:
    for chave in ("anyOf", "oneOf"):
        ramos = schema.get(chave)
        if isinstance(ramos, list):
            nao_nulos = [
                r for r in ramos if isinstance(r, dict) and not _e_schema_nulo(r)
            ]
            return nao_nulos or None
    return None


def _schema_casa(
    schema: SchemaDict,
    spec: SchemaDict,
    predicado: Callable[[SchemaDict], bool],
    refs_ativos: frozenset[str] = frozenset(),
) -> bool:
    if isinstance(ref := schema.get("$ref"), str):
        return ref not in refs_ativos and _schema_casa(
            _resolver_ref(spec, ref), spec, predicado, refs_ativos | {ref}
        )
    if isinstance(all_of := schema.get("allOf"), list) and all_of:
        return any(
            isinstance(sub, dict) and _schema_casa(sub, spec, predicado, refs_ativos)
            for sub in all_of
        )
    if (ramos := _ramos_nao_nulos(schema)) is not None:
        return all(_schema_casa(r, spec, predicado, refs_ativos) for r in ramos)
    if "anyOf" in schema or "oneOf" in schema:
        return False
    return predicado(schema)


def _schema_e_inteiro(schema: SchemaDict, spec: SchemaDict) -> bool:
    return _schema_casa(
        schema,
        spec,
        lambda s: bool(tipos := _tipos_nao_nulos(s))
        and all(t == "integer" for t in tipos),
    )


def _schema_tem_formato_string(
    schema: SchemaDict, spec: SchemaDict, formatos_aceitos: frozenset[str]
) -> bool:
    return _schema_casa(
        schema,
        spec,
        lambda s: bool(tipos := _tipos_nao_nulos(s))
        and all(t == "string" for t in tipos)
        and s.get("format") in formatos_aceitos,
    )


def _eh_campo_monetario(nome: str) -> bool:
    return nome.endswith("_cents") or any(sub in nome for sub in SUBSTRINGS_MONETARIAS)


def test_campos_monetarios_no_openapi_sao_sempre_integer(
    openapi_schema: SchemaDict,
) -> None:
    campos_monetarios: list[str] = []
    violacoes: list[str] = []

    for origem, nome, prop_schema in _iterar_propriedades(openapi_schema):
        if not _eh_campo_monetario(nome):
            continue
        campos_monetarios.append(origem)
        if not _schema_e_inteiro(prop_schema, openapi_schema):
            violacoes.append(f"{origem}: {prop_schema!r}")

    assert campos_monetarios, "Nenhum campo *_cents encontrado no OpenAPI"
    assert violacoes == [], f"Campos monetários não inteiros: {violacoes}"


def test_rotas_privadas_exigem_http_bearer_e_documentam_401(
    openapi_schema: SchemaDict,
) -> None:
    schemes = openapi_schema.get("components", {}).get("securitySchemes", {})
    assert "HTTPBearer" in schemes

    seguranca_raiz = openapi_schema.get("security")
    rotas_v1: set[tuple[str, str]] = set()
    violacoes: list[str] = []

    for method, path, op in _iterar_operacoes(openapi_schema):
        if not path.startswith("/api/v1/"):
            continue
        chave = (method, path)
        rotas_v1.add(chave)
        seguranca = op.get("security", seguranca_raiz) or []
        if chave in ROTAS_PUBLICAS_OU_AUTH_OPCIONAL:
            if chave in ROTAS_ESTRITAMENTE_PUBLICAS and seguranca:
                violacoes.append(
                    f"{method} {path} pública declara security={seguranca}"
                )
            continue

        tem_bearer = any(
            isinstance(req, dict) and "HTTPBearer" in req for req in seguranca
        )
        tem_bypass_vazio = any(req == {} for req in seguranca)
        if not tem_bearer or tem_bypass_vazio:
            violacoes.append(f"{method} {path} sem HTTPBearer obrigatório: {seguranca}")
        if "401" not in op.get("responses", {}):
            violacoes.append(f"{method} {path} não documenta resposta 401")

    assert rotas_v1, "Nenhuma rota /api/v1/ encontrada no OpenAPI"
    assert rotas_v1 >= ROTAS_PUBLICAS_OU_AUTH_OPCIONAL, (
        "Rotas ausentes da allowlist: "
        f"{sorted(ROTAS_PUBLICAS_OU_AUTH_OPCIONAL - rotas_v1)}"
    )
    assert violacoes == [], f"Violações de segurança no OpenAPI: {violacoes}"


def test_respostas_de_sucesso_tem_contrato_explicito(
    openapi_schema: SchemaDict,
) -> None:
    violacoes: list[str] = []
    sucessos_verificados = 0

    for method, path, op in _iterar_operacoes(openapi_schema):
        responses = op.get("responses", {})
        for code in ("200", "201"):
            if code not in responses:
                continue
            sucessos_verificados += 1
            schema = (
                responses[code]
                .get("content", {})
                .get("application/json", {})
                .get("schema")
            )
            if not isinstance(schema, dict) or not schema:
                violacoes.append(f"{method} {path} ({code}) sem JSON schema explícito")
                continue
            if isinstance(ref := schema.get("$ref"), str) and not _resolver_ref(
                openapi_schema, ref
            ):
                violacoes.append(f"{method} {path} ({code}) com $ref inválido: {ref}")

        if "204" in responses and "content" in responses["204"]:
            violacoes.append(f"{method} {path} (204) não pode declarar content")

    assert sucessos_verificados > 0
    assert violacoes == [], f"Contratos de resposta inválidos: {violacoes}"


def test_operation_ids_sao_unicos_e_rotas_e_respostas_tem_descricao(
    openapi_schema: SchemaDict,
) -> None:
    vistos: dict[str, str] = {}
    violacoes: list[str] = []

    for method, path, op in _iterar_operacoes(openapi_schema):
        rota = f"{method} {path}"
        op_id = op.get("operationId")
        if not isinstance(op_id, str) or not op_id.strip():
            violacoes.append(f"{rota} sem operationId")
        elif op_id in vistos:
            violacoes.append(
                f"operationId duplicado {op_id!r} em {vistos[op_id]} e {rota}"
            )
        else:
            vistos[op_id] = rota

        summary = str(op.get("summary") or "").strip()
        description = str(op.get("description") or "").strip()
        if not summary and not description:
            violacoes.append(f"{rota} sem summary nem description")

        for code, resp in sorted(op.get("responses", {}).items()):
            resp_desc = str(resp.get("description") or "").strip()
            if not resp_desc:
                violacoes.append(f"{rota} resposta {code} sem description")

    assert vistos, "Nenhuma operação encontrada no OpenAPI"
    assert violacoes == [], f"Inconsistências de metadados: {violacoes}"


def test_campos_uuid_e_temporais_declaram_formatos_consistentes(
    openapi_schema: SchemaDict,
) -> None:
    uuids_verificados = 0
    datas_verificadas = 0
    violacoes: list[str] = []

    for origem, nome, prop_schema in _iterar_propriedades(openapi_schema):
        if nome == "id" or nome.endswith("_id"):
            uuids_verificados += 1
            if not _schema_tem_formato_string(
                prop_schema, openapi_schema, frozenset({"uuid"})
            ):
                violacoes.append(f"{origem} (UUID esperado): {prop_schema!r}")
        elif nome in {"from", "to"} or nome.endswith(("_on", "_date")):
            datas_verificadas += 1
            if not _schema_tem_formato_string(
                prop_schema, openapi_schema, frozenset({"date"})
            ):
                violacoes.append(f"{origem} (date esperado): {prop_schema!r}")
        elif nome.endswith("_at"):
            datas_verificadas += 1
            if not _schema_tem_formato_string(
                prop_schema, openapi_schema, frozenset({"date-time"})
            ):
                violacoes.append(f"{origem} (date-time esperado): {prop_schema!r}")

    assert uuids_verificados > 0
    assert datas_verificadas > 0
    assert violacoes == [], f"Formatos inconsistentes no OpenAPI: {violacoes}"
