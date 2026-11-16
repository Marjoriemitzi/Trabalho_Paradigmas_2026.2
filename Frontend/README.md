# Frontend — Saldo

Interface em **Elm 0.19.1**, com login, cadastro e uma área de confirmação do usuário autenticado. Segue os contratos existentes da API; nenhuma alteração de backend é necessária.

## Executar com Docker

Na raiz do projeto, depois de configurar o `.env` conforme o README principal:

```bash
docker compose up -d --build
docker compose exec app alembic upgrade head
```

Abra **http://127.0.0.1:5173**. O Nginx serve os arquivos e encaminha `/api/` à API. Como ambos usam a mesma origem no navegador, não é necessário habilitar CORS. Depois de editar o frontend, reconstrua com `docker compose up -d --build frontend`.

## Desenvolver localmente

Requisitos: Node.js 22 e npm. O backend continua no Docker.

```bash
# Na raiz
docker compose up -d app db
docker compose exec app alembic upgrade head

# Em Frontend/
npm ci
npm start
```

Acesse http://127.0.0.1:5173. O servidor recompila alterações dos arquivos Elm; atualize a página para vê-las. Encaminha `/api/` para `http://127.0.0.1:8000`.

Variáveis opcionais: `BACKEND_URL`, `PORT` e `HOST`. Por exemplo, no Linux/WSL: `BACKEND_URL=http://127.0.0.1:8001 npm start`.

## Comportamentos

- Login: `POST /api/v1/auth/login`, seguido de `GET /api/v1/users/me` com Bearer token.
- Cadastro: `POST /api/v1/users`, usando apenas `email` e `password`; depois retorna ao login com confirmação. A confirmação de senha é validada só na interface.
- A senha de cadastro exige 12 caracteres, maiúscula, minúscula, número e símbolo. A política Prolog é a autoridade final. O login permite qualquer senha não vazia, sem impor a política de cadastro.
- Trata credenciais incorretas, e-mail duplicado/inválido, senha fraca, erros por campo, indisponibilidade e timeout. Nunca exibe respostas técnicas cruas do servidor.
- Bloqueia submissões duplicadas, permite mostrar/ocultar senha e descarta respostas antigas ao trocar de formulário.
- Sessão em `sessionStorage`, restrita à aba. Senhas não são persistidas. O token só é salvo depois de `/users/me` confirmar o usuário; é revalidado ao recarregar e apagado ao sair ou expirar. Sem acesso ao armazenamento, funciona em memória.
- Não há renovação de token, recuperação de senha ou revogação no servidor porque a API não oferece esses endpoints. Sair limpa a sessão deste cliente.
- A área autenticada confirma o usuário real e permite sair. Não simula funcionalidades financeiras ainda não implementadas no frontend.
- Layout responsivo, rótulos, autocomplete, foco nos campos inválidos, mensagens acessíveis e preferência por movimento reduzido.

## Organização

| Arquivo | Responsabilidade |
| --- | --- |
| `src/Main.elm` | Estado, formulários, sessão e interface |
| `src/Api.elm` | Requests, decoders e erros da API |
| `src/Validation.elm` | Validações dos formulários |
| `public/bootstrap.js` | Inicialização, armazenamento e foco via ports |
| `public/styles.css` | Layout responsivo sem dependências externas |
| `scripts/dev.mjs` | Servidor local, compilação e proxy |
| `nginx.conf` | Arquivos estáticos e proxy no Docker |
| `tests/auth.test.cjs` | Testes de interface com API simulada |

## Verificações

```bash
npm run format:check
npm run build
npx playwright install chromium
npm test
```

Os testes usam um servidor HTTP de API simulado e o frontend compilado em um navegador real. Cobrem contratos HTTP, validação, erros, sessão, expiração e navegação. Eles não substituem a verificação com FastAPI + PostgreSQL + SWI-Prolog.

Não versione `node_modules/`, `elm-stuff/` ou `public/elm.js`. O Docker e `npm run build` geram o bundle a partir de `src/`.
