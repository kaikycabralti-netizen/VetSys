import requests
import json

# Configuração da API Key (Fornecida pelo usuário)
API_KEY = "AIzaSyBZtSZviMm2yuFAAIuiO0othSCKA01oqY8"
MODEL_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"

# Instruções do Sistema (Mantidas e Refinadas)
INSTRUCOES_SISTEMA = (
    "Você é um chatbot veterinário chamado VetSys. Extremamente qualificado, científico e profissional; "
    "mas com um linguajar e idioma local, para geração de empatia na experiência dos principais usuários (donos de PETs). "
    "Seu papel é ajudar usuários com dúvidas sobre a saúde e o comportamento de seus animais. "
    "Responda perguntas simples como 'meu cachorro não quer comer' ou 'meu gato está dormindo muito', "
    "de forma clara, empática e educativa. "
    "Evite dar diagnósticos exatos e sempre recomende que o tutor procure um veterinário quando necessário. "
    "Você faz parte de um futuro aplicativo que permitirá ver clínicas e marcar consultas, "
    "mas no momento apenas responde dúvidas básicas. "
    "P.S.: Seja extremamente profissional. Em suas respostas, baseie-se em dados reais e consistentes. "
    "NÃO alucine dados e nem informações; tudo deve ser consistente, validado e profissional. "
    "Faça respostas bem resumidas, no máximo 5 linhas e básicas."
)

class VetSysAI:
    def __init__(self):
        self.history = []

    def obter_resposta(self, pergunta: str) -> str:
        try:
            # Adiciona a pergunta do usuário ao histórico (temporário para a requisição)
            # Nota: Para um chat real, deveríamos persistir o histórico, mas aqui faremos acumulativo na sessão da memória
            
            # Constrói o payload
            contents = []
            
            # Adiciona histórico anterior (limitado aos últimos 10 turnos para não estourar contexto/tokens)
            for msg in self.history[-10:]:
                contents.append(msg)
            
            # Adiciona a mensagem atual
            user_msg = {"role": "user", "parts": [{"text": pergunta}]}
            contents.append(user_msg)

            payload = {
                "contents": contents,
                "system_instruction": {
                    "parts": [{"text": INSTRUCOES_SISTEMA}]
                }
            }

            headers = {
                'Content-Type': 'application/json'
            }

            response = requests.post(MODEL_URL, headers=headers, data=json.dumps(payload))
            
            if response.status_code == 200:
                result = response.json()
                try:
                    texto_resposta = result['candidates'][0]['content']['parts'][0]['text']
                    
                    # Atualiza histórico
                    self.history.append(user_msg)
                    self.history.append({"role": "model", "parts": [{"text": texto_resposta}]})
                    
                    return texto_resposta
                except (KeyError, IndexError) as e:
                    print(f"Erro ao parsear resposta da IA: {e} - Payload: {result}")
                    return "Desculpe, recebi uma resposta inválida da central de inteligência."
            else:
                print(f"Erro na API Gemini: {response.status_code} - {response.text}")
                return "Desculpe, estou com dificuldades de conexão com meu cérebro digital no momento."

        except Exception as e:
            print(f"Erro geral na IA: {e}")
            return "Desculpe, ocorreu um erro interno ao processar sua solicitação."

# Instância global para ser importada
vetsys_ai = VetSysAI()
