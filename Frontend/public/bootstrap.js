const sessionKey = "finance.token";

let savedToken = null;

try {
  savedToken = sessionStorage.getItem(sessionKey);
} catch {
  // Se o armazenamento estiver bloqueado, funciona apenas em memória.
}

const app = Elm.Main.init({
  node: document.getElementById("app"),
  flags: savedToken
});

app.ports.saveToken.subscribe(function (token) {
  try {
    sessionStorage.setItem(sessionKey, token);
  } catch {
    // O usuário continua conectado enquanto a página estiver aberta.
  }
});

app.ports.clearToken.subscribe(function () {
  try {
    sessionStorage.removeItem(sessionKey);
  } catch {
    // A sessão em memória já foi removida pelo Elm.
  }
});