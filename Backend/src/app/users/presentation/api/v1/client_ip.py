from fastapi import Request


def client_ip(request: Request) -> str:
    """O IP do cliente é sempre `request.client.host`.

    Atrás de proxy, o uvicorn só o troca pelo de `X-Forwarded-For` quando o proxy
    está em `--forwarded-allow-ips`. A aplicação nunca lê esse cabeçalho.
    """
    return request.client.host if request.client else "unknown"
