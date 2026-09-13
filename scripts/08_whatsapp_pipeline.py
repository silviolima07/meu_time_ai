from pathlib import Path
import os
import time
import json

import requests
from dotenv import load_dotenv

from rag_core import (
    busca_hibrida,
    montar_contexto,
    perguntar_llm,
    salvar_log,
)


# ============================================================
# CONFIGURAÇÃO
# ============================================================

ROOT = Path(__file__).resolve().parent.parent

load_dotenv(
    ROOT / ".env"
)


EVO_BASE_URL = os.getenv(
    "EVO_BASE_URL"
)

EVO_API_KEY = os.getenv(
    "EVO_API_KEY"
)

EVO_INSTANCE_NAME = os.getenv(
    "EVO_INSTANCE_NAME"
)


# Intervalo entre verificações
POLL_INTERVAL = 3


# Arquivo para evitar responder
# novamente a mesma mensagem
PASTA_ESTADO = (
    ROOT
    / "dados_processados"
    / "whatsapp"
)

PASTA_ESTADO.mkdir(
    parents=True,
    exist_ok=True
)

ARQUIVO_ESTADO = (
    PASTA_ESTADO
    / "mensagens_processadas.json"
)


# ============================================================
# VALIDAÇÃO
# ============================================================

if not EVO_BASE_URL:
    raise RuntimeError(
        "EVO_BASE_URL não definida."
    )

if not EVO_API_KEY:
    raise RuntimeError(
        "EVO_API_KEY não definida."
    )

if not EVO_INSTANCE_NAME:
    raise RuntimeError(
        "EVO_INSTANCE_NAME não definida."
    )


HEADERS = {
    "apikey": EVO_API_KEY,
    "Content-Type": "application/json"
}


# ============================================================
# ESTADO DAS MENSAGENS
# ============================================================

def carregar_processadas():

    if not ARQUIVO_ESTADO.exists():

        return set()

    with open(
        ARQUIVO_ESTADO,
        "r",
        encoding="utf-8"
    ) as arquivo:

        dados = json.load(
            arquivo
        )

    return set(
        dados
    )


def salvar_processadas(
    mensagens
):

    with open(
        ARQUIVO_ESTADO,
        "w",
        encoding="utf-8"
    ) as arquivo:

        json.dump(
            list(mensagens),
            arquivo,
            ensure_ascii=False,
            indent=2
        )


# ============================================================
# EXTRAIR TEXTO
# ============================================================

def extrair_texto(
    mensagem
):

    conteudo = mensagem.get(
        "message",
        {}
    )

    # Mensagem normal
    texto = conteudo.get(
        "conversation"
    )

    if texto:

        return texto


    # Extended text
    extended = conteudo.get(
        "extendedTextMessage",
        {}
    )

    texto = extended.get(
        "text"
    )

    if texto:

        return texto


    return None


# ============================================================
# EXTRAIR NÚMERO
# ============================================================

#def extrair_numero(
#    mensagem
#):

#    key = mensagem.get(
#        "key",
#        {}
#    )

#    remote_jid = key.get(
#        "remoteJid",
#        ""
#    )

#    remote_jid_alt = key.get(
#        "remoteJidAlt",
#        ""
#    )


    # ========================================================
    # Caso 1
    # remoteJid é um LID interno do WhatsApp
    #
    # Exemplo:
    # 240681511592026@lid
    #
    # Nesse caso usamos remoteJidAlt,
    # que normalmente contém o telefone real.

    # ========================================================
    # Caso 2
    # remoteJid já contém o número normal
    #
    # Exemplo:
    # 5512XXXXXXXX@s.whatsapp.net
    # ========================================================


    # Retira o domínio do WhatsApp

def extrair_numero(mensagem):

    key = mensagem.get(
        "key",
        {}
    )

    remote_jid = key.get(
        "remoteJid",
        ""
    )

    remote_jid_alt = key.get(
        "remoteJidAlt",
        ""
    )


    # --------------------------------------------------------
    # DEBUG TEMPORÁRIO
    # --------------------------------------------------------

    #print(
    #    f"[DEBUG] remoteJid: {remote_jid}"
    #)

    #print(
    #    f"[DEBUG] remoteJidAlt: {remote_jid_alt}"
    #)


    # --------------------------------------------------------
    # Preferir identificador que NÃO seja LID
    # --------------------------------------------------------

    candidatos = [
        remote_jid,
        remote_jid_alt
    ]


    for jid in candidatos:

        if (
            jid
            and not jid.endswith("@lid")
            and "@" in jid
        ):

            return jid.split("@")[0]


    # --------------------------------------------------------
    # Se só existir LID, não usar como telefone
    # --------------------------------------------------------

    return None

# ============================================================
# BUSCAR MENSAGENS
# ============================================================

def buscar_mensagens():

    url = (
        f"{EVO_BASE_URL}"
        f"/chat/findMessages/"
        f"{EVO_INSTANCE_NAME}"
    )

    payload = {
        "where": {
            "key": {
                "fromMe": False
            }
        }
    }

    response = requests.post(
        url,
        headers=HEADERS,
        json=payload,
        timeout=30
    )

    response.raise_for_status()

    dados = response.json()


    # ========================================================
    # Caso 1
    # Evolution retorna diretamente uma lista
    # ========================================================

    if isinstance(
        dados,
        list
    ):

        return dados


    # ========================================================
    # Caso 2
    # Evolution retorna um dicionário
    # ========================================================

    if isinstance(
        dados,
        dict
    ):

        messages = dados.get(
            "messages"
        )


        # ----------------------------------------------------
        # messages já é uma lista
        # ----------------------------------------------------

        if isinstance(
            messages,
            list
        ):

            return messages


        # ----------------------------------------------------
        # messages contém records
        # ----------------------------------------------------

        if isinstance(
            messages,
            dict
        ):

            records = messages.get(
                "records"
            )

            if isinstance(
                records,
                list
            ):

                return records


        # ----------------------------------------------------
        # records diretamente na raiz
        # ----------------------------------------------------

        records = dados.get(
            "records"
        )

        if isinstance(
            records,
            list
        ):

            return records


    return []

# ============================================================
# ENVIAR WHATSAPP
# ============================================================

def enviar_mensagem(
    numero,
    texto
):

    url = (
        f"{EVO_BASE_URL}"
        f"/message/sendText/"
        f"{EVO_INSTANCE_NAME}"
    )


    payload = {
        "number": numero,
        "text": texto
    }


    print(
        f"\nEnviando para: {numero}"
    )


    response = requests.post(
        url,
        headers=HEADERS,
        json=payload,
        timeout=30
    )


    # --------------------------------------------
    # Mostrar erro detalhado da Evolution
    # --------------------------------------------

    if not response.ok:

        print(
            "\n[ERRO EVOLUTION]"
        )

        print(
            f"Status: {response.status_code}"
        )

        print(
            f"Resposta: {response.text}"
        )

        response.raise_for_status()


    return response.json()


# ============================================================
# PROCESSAR PERGUNTA
# ============================================================

def processar_pergunta(
    pergunta
):

    print(
        f"\nPergunta recebida:"
        f"\n{pergunta}"
    )


    # --------------------------------------------
    # Retrieval
    # --------------------------------------------

    resultados = busca_hibrida(
        pergunta
    )


    # --------------------------------------------
    # Contexto
    # --------------------------------------------

    contexto = montar_contexto(
        resultados
    )


    # --------------------------------------------
    # LLM
    # --------------------------------------------

    resposta = perguntar_llm(
        pergunta,
        contexto
    )


    # --------------------------------------------
    # Auditoria
    # --------------------------------------------

    salvar_log(
        pergunta,
        resposta,
        resultados
    )


    return resposta


# ============================================================
# LOOP PRINCIPAL
# ============================================================

def main():

    print(
        "=" * 70
    )

    print(
        "MEU TIME IA - WHATSAPP"
    )

    print(
        "=" * 70
    )


    processadas = carregar_processadas()


    print(
        "\nEvolution:"
        f" {EVO_BASE_URL}"
    )

    print(
        "Instância:"
        f" {EVO_INSTANCE_NAME}"
    )

    print(
        "\nAguardando mensagens..."
    )


    while True:

        try:

            mensagens = buscar_mensagens()
            #print(
            #  f"[DEBUG] Mensagens recebidas da Evolution: {len(mensagens)}"
            #)


            # Mais antigas primeiro
            mensagens = reversed(
                mensagens
            )


            for mensagem in mensagens:
                
                #print("\n[DEBUG] -----------------------------")
                #print(
                #   "[DEBUG] tipo:",
                #     type(mensagem)
                #)
                # -------------------------------
                # Garantir que é um dicionário  
                # -------------------------------

                if not isinstance(
                    mensagem,
                    dict
                    ):

                        print(
                        "[AVISO] Registro ignorado:",
                        type(mensagem),
                        mensagem
                       )

                        continue
               
                # -------------------------------
                # Extrair identificador da mensagem
                # -------------------------------
                key = mensagem.get(
                  "key",
                   {}
                )

                # -------------------------------
                # Garantir que key seja um dicionário
                # -------------------------------
                
                if not isinstance(
                    key,
                    dict
                    ):
                    print(
                        "[AVISO] key invalido:",
                        key
                    )
                    continue
                
                #print("\n[DEBUG] Mensagem encontrada")

                key = mensagem.get(
                    "key",
                    {}
                )

                #print(
                #    f"[DEBUG] id: {key.get('id')}"
                #)

                #print(
                #    f"[DEBUG] fromMe: {key.get('fromMe')}"
                #)

                #print(
                #    f"[DEBUG] remoteJid: {key.get('remoteJid')}"
                #)

                #print(
                #    f"[DEBUG] remoteJidAlt: {key.get('remoteJidAlt')}"
                #)
                
                    
                # --------------------------------
                # Ignorar mensagens enviadas
                # pelo próprio bot
                # --------------------------------

                if key.get(
                    "fromMe"
                ):

                    continue


                message_id = key.get(
                    "id"
                )


                if not message_id:

                    continue


                # --------------------------------
                # Já processada
                # --------------------------------

                if message_id in processadas:

                    continue

                if message_id in processadas:

                #    print(
                #      f"[DEBUG] Já processada: {message_id}"
                #    )

                    continue

                texto = extrair_texto(
                    mensagem
                )
                #print(
                #    f"[DEBUG] texto: {texto}"
                #)


                if not texto:

                    processadas.add(
                        message_id
                    )

                    continue


                numero = extrair_numero(
                    mensagem
                )


                if not numero:

                    continue
                
                
                #print(
                #  f"[DEBUG] numero extraído: {numero}"
                #)

                print(
                    "\n" + "-" * 70
                )

                print(
                    f"Mensagem de:"
                    f" {numero}"
                )

                print(
                    f"Pergunta:"
                    f" {texto}"
                )


                # ================================
                # RAG
                # ================================

                resposta = processar_pergunta(
                    texto
                )


                print(
                    f"\nResposta:"
                    f"\n{resposta}"
                )


                # ================================
                # WHATSAPP
                # ================================
                resposta_whatsapp = (
                 "⚽ *Meu Time IA*\n\n"
                 f"{resposta}"
                )
                
                enviar_mensagem(
                    numero,
                    resposta_whatsapp
                )


                print(
                    "\n[OK] Resposta enviada."
                )


                # Somente agora consideramos
                # a mensagem processada
                processadas.add(
                    message_id
                )


                salvar_processadas(
                    processadas
                )


        except KeyboardInterrupt:

            print(
                "\n\nEncerrando..."
            )

            break


        except Exception as erro:

            print(
                "\n[ERRO]"
            )

            print(
                erro
            )


        time.sleep(
            POLL_INTERVAL
        )


if __name__ == "__main__":

    main()