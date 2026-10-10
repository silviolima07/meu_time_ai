
export default {
  async fetch(request, env, ctx) {
    if (request.method !== "POST") {
      return new Response("Meu Time IA - Gateway ativo");
    }

    const secret = request.headers.get(
      "X-Telegram-Bot-Api-Secret-Token"
    );

    if (!env.WEBHOOK_SECRET || secret !== env.WEBHOOK_SECRET) {
      return new Response("Unauthorized", { status: 401 });
    }

    let update;

    try {
      update = await request.json();
    } catch {
      return new Response("Invalid JSON", { status: 400 });
    }

    const mensagem = update.message;
    const chatId = mensagem?.chat?.id;
    const pergunta = mensagem?.text?.trim();

    if (!chatId || !pergunta) {
      return new Response("OK");
    }

    ctx.waitUntil(processarMensagem(chatId, pergunta, env));

    return new Response("OK", { status: 200 });
  }
};

async function processarMensagem(chatId, pergunta, env) {
  const comando = pergunta.split(/\s+/)[0].split("@")[0].toLowerCase();
  const chaveModo = `modo:${chatId}`;

  try {
    if (comando === "/audio" || comando === "/texto") {
      const modo = comando === "/audio" ? "audio" : "texto";

      await env.MODOS_KV.put(chaveModo, modo);

      const confirmacao = modo === "audio"
        ? "🔊 Modo áudio ativado! Suas próximas respostas serão enviadas por voz."
        : "📝 Modo texto ativado! Suas próximas respostas serão enviadas por escrito.";

      await enviarTexto(chatId, confirmacao, env);
      return;
    }

    if (comando === "/start") {
      await enviarTexto(
        chatId,
        "⚽ Bem-vindo ao Meu Time IA!\n\n" +
        "Pergunte sobre o Flamengo.\n\n" +
        "📝 /texto — respostas em texto\n" +
        "🔊 /audio — respostas em áudio",
        env
      );
      return;
    }

    const modoSalvo = await env.MODOS_KV.get(chaveModo);
    const modo = modoSalvo === "audio" ? "audio" : "texto";

    if (modo === "audio") {
      await responderAudio(chatId, pergunta, env);
    } else {
      await responderTexto(chatId, pergunta, env);
    }

  } catch (erro) {
    console.log("Erro no processamento:", String(erro));

    try {
      await enviarTexto(
        chatId,
        "⚽ Meu Time IA\n\n" +
        "Nosso assistente está temporariamente indisponível. " +
        "Por favor, tente novamente mais tarde.",
        env
      );
    } catch (erroTelegram) {
      console.log("Erro Telegram:", String(erroTelegram));
    }
  }
}

async function consultarBackend(pergunta, modo, env) {
  const endpoint = modo === "audio"
    ? "/perguntar/audio"
    : "/perguntar";

  const resposta = await fetch(`${env.BACKEND_URL}${endpoint}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Backend-API-Key": env.BACKEND_API_KEY
    },
    body: JSON.stringify({ pergunta, modo }),
    signal: AbortSignal.timeout(90000)
  });

  if (!resposta.ok) {
    throw new Error(`Backend HTTP ${resposta.status}`);
  }

  return resposta;
}

async function responderTexto(chatId, pergunta, env) {
  const resposta = await consultarBackend(pergunta, "texto", env);
  const dados = await resposta.json();

  if (typeof dados.resposta !== "string" || !dados.resposta.trim()) {
    throw new Error("Resposta vazia do RAG");
  }

  await enviarTexto(chatId, dados.resposta, env);
}

async function responderAudio(chatId, pergunta, env) {
  const resposta = await consultarBackend(pergunta, "audio", env);

  const tipo = resposta.headers.get("Content-Type") || "";

  if (!tipo.includes("audio/ogg")) {
    throw new Error(`Formato de áudio inesperado: ${tipo}`);
  }

  const audio = await resposta.blob();

  if (audio.size === 0) {
    throw new Error("Áudio vazio");
  }

  const formulario = new FormData();
  formulario.append("chat_id", String(chatId));
  formulario.append(
    "voice",
    new File([audio], "resposta.ogg", { type: "audio/ogg" })
  );

  const respostaTelegram = await fetch(
    `https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/sendVoice`,
    {
      method: "POST",
      body: formulario,
      signal: AbortSignal.timeout(30000)
    }
  );

  if (!respostaTelegram.ok) {
    const detalhe = await respostaTelegram.text();
    throw new Error(
      `Telegram sendVoice HTTP ${respostaTelegram.status}: ${detalhe}`
    );
  }
}

async function enviarTexto(chatId, texto, env) {
  const respostaTelegram = await fetch(
    `https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/sendMessage`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        chat_id: chatId,
        text: texto.slice(0, 4000)
      }),
      signal: AbortSignal.timeout(30000)
    }
  );

  if (!respostaTelegram.ok) {
    throw new Error(
      `Telegram sendMessage HTTP ${respostaTelegram.status}`
    );
  }
}
