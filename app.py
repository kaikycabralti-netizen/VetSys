import uvicorn
import sqlite3
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import date, time, datetime

# --- Configuração do Banco de Dados ---
DB_NAME = "vetsys.db"

def get_db_connection():
    """Cria e retorna uma conexão com o banco de dados SQLite."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Inicializa o banco de dados com as tabelas necessárias."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Tabela de Pacientes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pacientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            tutor TEXT NOT NULL,
            especie TEXT NOT NULL,
            raca TEXT NOT NULL,
            status TEXT NOT NULL
        )
    ''')

    # Tabela de Consultas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS consultas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            paciente_id INTEGER NOT NULL,
            veterinario TEXT NOT NULL,
            data TEXT NOT NULL,
            hora TEXT NOT NULL,
            motivo TEXT NOT NULL,
            FOREIGN KEY (paciente_id) REFERENCES pacientes (id)
        )
    ''')

    # Tabela de Estoque
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS estoque (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item TEXT NOT NULL,
            categoria TEXT NOT NULL,
            quantidade INTEGER NOT NULL,
            validade TEXT NOT NULL,
            status TEXT NOT NULL
        )
    ''')

    # Tabela Financeira
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS financeiro (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descricao TEXT NOT NULL,
            tipo TEXT NOT NULL, -- 'receita' ou 'despesa'
            valor REAL NOT NULL,
            data TEXT NOT NULL,
            categoria TEXT NOT NULL
        )
    ''')
    
    # Migração de Schema: Adicionar colunas novas se não existirem
    cursor.execute("PRAGMA table_info(financeiro)")
    columns = [info[1] for info in cursor.fetchall()]
    
    if 'origem' not in columns:
        print("Migrando BD: Adicionando coluna 'origem' em 'financeiro'...")
        cursor.execute("ALTER TABLE financeiro ADD COLUMN origem TEXT")
        
    if 'referencia_id' not in columns:
        print("Migrando BD: Adicionando coluna 'referencia_id' em 'financeiro'...")
        cursor.execute("ALTER TABLE financeiro ADD COLUMN referencia_id INTEGER")
    
    conn.commit()
    conn.close()
    print("Banco de dados inicializado e verificado com sucesso.")

# --- Funções de Acesso a Dados (DAO) ---

# ... (Pacientes e Consultas mantidos e melhorados) ...

def db_add_paciente(paciente: Dict[str, Any]) -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO pacientes (nome, tutor, especie, raca, status)
        VALUES (?, ?, ?, ?, ?)
    ''', (paciente['nome'], paciente['tutor'], paciente['especie'], paciente['raca'], paciente['status']))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id

def db_get_pacientes() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM pacientes ORDER BY id DESC')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def db_update_paciente(paciente_id: int, dados: Dict[str, Any]) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE pacientes 
        SET nome = ?, tutor = ?, especie = ?, raca = ?, status = ?
        WHERE id = ?
    ''', (dados['nome'], dados['tutor'], dados['especie'], dados['raca'], dados['status'], paciente_id))
    conn.commit()
    rows_affected = cursor.rowcount
    conn.close()
    return rows_affected > 0

def db_delete_paciente(paciente_id: int) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    # Opcional: Verificar se há consultas antes de deletar
    cursor.execute('DELETE FROM pacientes WHERE id = ?', (paciente_id,))
    conn.commit()
    rows_affected = cursor.rowcount
    conn.close()
    return rows_affected > 0

def db_add_consulta(consulta: Dict[str, Any]) -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO consultas (paciente_id, veterinario, data, hora, motivo)
        VALUES (?, ?, ?, ?, ?)
    ''', (consulta['paciente_id'], consulta['veterinario'], str(consulta['data']), str(consulta['hora']), consulta['motivo']))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id

def db_get_consultas() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    # JOIN para trazer dados do paciente (Nome, Espécie, Raça)
    cursor.execute('''
        SELECT c.*, p.nome as paciente_nome, p.especie as paciente_especie, p.raca as paciente_raca
        FROM consultas c
        JOIN pacientes p ON c.paciente_id = p.id
        ORDER BY c.data DESC, c.hora DESC
    ''')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# --- Novos DAOs (Estoque, Financeiro, Dashboard) ---

def db_get_estoque() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM estoque ORDER BY validade ASC')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def db_add_item_estoque(item: Dict[str, Any]) -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO estoque (item, categoria, quantidade, validade, status)
        VALUES (?, ?, ?, ?, ?)
    ''', (item['item'], item['categoria'], item['quantidade'], str(item['validade']), item['status']))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id

def db_get_financeiro_resumo() -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Receita Total
    cursor.execute("SELECT SUM(valor) FROM financeiro WHERE tipo = 'receita'")
    receita = cursor.fetchone()[0] or 0.0
    
    # Despesa Total
    cursor.execute("SELECT SUM(valor) FROM financeiro WHERE tipo = 'despesa'")
    despesa = cursor.fetchone()[0] or 0.0
    
    conn.close()
    return {
        "receita_total": receita,
        "despesa_total": despesa,
        "lucro": receita - despesa
    }

def db_add_transacao(transacao: Dict[str, Any]) -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO financeiro (descricao, tipo, valor, data, categoria, origem, referencia_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        transacao['descricao'], 
        transacao['tipo'], 
        transacao['valor'], 
        transacao['data'], 
        transacao['categoria'],
        transacao.get('origem'),
        transacao.get('referencia_id')
    ))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id

def db_get_transacoes(limit: int = 10) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM financeiro ORDER BY data DESC, id DESC LIMIT ?', (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def db_get_financeiro_grafico() -> Dict[str, Any]:
    """Retorna dados agregados por mês para gráficos."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Agrupar por mês (YYYY-MM) e tipo
    # SQLite strftime('%Y-%m', data)
    cursor.execute('''
        SELECT strftime('%Y-%m', data) as mes, tipo, SUM(valor) as total
        FROM financeiro
        GROUP BY mes, tipo
        ORDER BY mes ASC
    ''')
    rows = cursor.fetchall()
    conn.close()
    
    # Processar dados para formato fácil de gráfico
    dados = {}
    for row in rows:
        mes = row['mes']
        tipo = row['tipo']
        total = row['total']
        
        if mes not in dados:
            dados[mes] = {'receita': 0.0, 'despesa': 0.0}
        dados[mes][tipo] = total
        
    # Converter para listas ordenadas
    meses = sorted(dados.keys())
    receitas = [dados[m]['receita'] for m in meses]
    despesas = [dados[m]['despesa'] for m in meses]
    
    return {
        "labels": meses,
        "receitas": receitas,
        "despesas": despesas
    }

def db_get_dashboard_stats() -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Total Pacientes
    cursor.execute("SELECT COUNT(*) FROM pacientes")
    total_pacientes = cursor.fetchone()[0]
    
    # Consultas Hoje
    hoje = date.today().isoformat()
    cursor.execute("SELECT COUNT(*) FROM consultas WHERE data = ?", (hoje,))
    consultas_hoje = cursor.fetchone()[0]
    
    # Procedimentos Mês (Simplificado: Consultas do mês atual)
    mes_atual = date.today().strftime("%Y-%m")
    cursor.execute("SELECT COUNT(*) FROM consultas WHERE data LIKE ?", (f"{mes_atual}%",))
    procedimentos_mes = cursor.fetchone()[0]

    # Total Itens Estoque
    cursor.execute("SELECT COUNT(*) FROM estoque")
    total_estoque = cursor.fetchone()[0]
    
    conn.close()
    return {
        "total_pacientes": total_pacientes,
        "consultas_hoje": consultas_hoje,
        "procedimentos_mes": procedimentos_mes,
        "total_estoque": total_estoque
    }

# --- Modelos Pydantic ---

class Paciente(BaseModel):
    id: Optional[int] = None
    nome: str
    tutor: str
    especie: str
    raca: str
    status: str = Field(..., description="Ex: 'Ativo' ou 'Inativo'")

class Consulta(BaseModel):
    id: Optional[int] = None
    paciente_id: int
    veterinario: str
    data: date
    hora: time
    motivo: str

class ConsultaResponse(Consulta):
    paciente_nome: Optional[str] = None
    paciente_especie: Optional[str] = None
    paciente_raca: Optional[str] = None

class ItemEstoque(BaseModel):
    id: Optional[int] = None
    item: str
    categoria: str
    quantidade: int
    validade: date
    status: str # OK, Baixo, Vencido

class FinanceiroResumo(BaseModel):
    receita_total: float
    despesa_total: float
    lucro: float

class Transacao(BaseModel):
    id: Optional[int] = None
    descricao: str
    tipo: str = Field(..., description="'receita' ou 'despesa'")
    valor: float
    data: str # YYYY-MM-DD
    categoria: str
    origem: Optional[str] = None # 'consulta', 'estoque', 'outro'
    referencia_id: Optional[int] = None

class FinanceiroGrafico(BaseModel):
    labels: List[str]
    receitas: List[float]
    despesas: List[float]

class DashboardStats(BaseModel):
    total_pacientes: int
    consultas_hoje: int
    procedimentos_mes: int
    total_estoque: int

# --- Aplicação FastAPI ---

from contextlib import asynccontextmanager
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

# ... (imports anteriores)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Inicializar BD
    init_db()
    yield
    # Shutdown: (Opcional) Fechar conexões, etc.

app = FastAPI(
    title="VetSys API",
    description="Backend profissional para o sistema de gerenciamento veterinário VetSys.",
    version="2.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar arquivos estáticos (CSS, JS, Imagens)
# Ajuste o caminho conforme a estrutura real: app.py está na raiz, src/public está em ./src/public
app.mount("/public", StaticFiles(directory="src/public"), name="public")

@app.get("/", tags=["Frontend"])
async def read_root():
    # Serve o arquivo HTML principal
    return FileResponse("src/views/index.html")

@app.get("/api/status", tags=["Root"])
def read_api_status():
    return {"Sistema": "VetSys API", "Status": "Online", "Version": "2.1.0"}

# --- Rotas de Dashboard ---

@app.get("/api/dashboard", response_model=DashboardStats, tags=["Dashboard"])
def get_dashboard():
    """ Retorna estatísticas para o dashboard principal. """
    try:
        return db_get_dashboard_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar stats: {str(e)}")

# --- Rotas de Pacientes ---

@app.get("/api/pacientes", response_model=List[Paciente], tags=["Pacientes"])
def get_pacientes():
    return db_get_pacientes()

@app.post("/api/pacientes", response_model=Paciente, status_code=201, tags=["Pacientes"])
def create_paciente(paciente: Paciente):
    try:
        paciente_dict = paciente.dict()
        new_id = db_add_paciente(paciente_dict)
        paciente.id = new_id
        return paciente
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao criar paciente: {str(e)}")

@app.put("/api/pacientes/{paciente_id}", response_model=Paciente, tags=["Pacientes"])
def update_paciente(paciente_id: int, paciente: Paciente):
    try:
        paciente_dict = paciente.dict()
        updated = db_update_paciente(paciente_id, paciente_dict)
        if not updated:
            raise HTTPException(status_code=404, detail="Paciente não encontrado")
        paciente.id = paciente_id
        return paciente
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar paciente: {str(e)}")

@app.delete("/api/pacientes/{paciente_id}", status_code=204, tags=["Pacientes"])
def delete_paciente(paciente_id: int):
    try:
        deleted = db_delete_paciente(paciente_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Paciente não encontrado")
        return
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao excluir paciente: {str(e)}")

# --- Rotas de Consultas ---

@app.get("/api/consultas", response_model=List[ConsultaResponse], tags=["Consultas"])
def get_consultas():
    return db_get_consultas()

@app.post("/api/consultas", response_model=Consulta, status_code=201, tags=["Consultas"])
def create_consulta(consulta: Consulta):
    try:
        # Validar se paciente existe
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM pacientes WHERE id = ?", (consulta.paciente_id,))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail="Paciente não encontrado")
        conn.close()

        consulta_dict = consulta.dict()
        new_id = db_add_consulta(consulta_dict)
        consulta.id = new_id
        return consulta
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao criar consulta: {str(e)}")

# --- Rotas de Estoque ---

@app.get("/api/estoque", response_model=List[ItemEstoque], tags=["Estoque"])
def get_estoque():
    return db_get_estoque()

@app.post("/api/estoque", response_model=ItemEstoque, status_code=201, tags=["Estoque"])
def create_item_estoque(item: ItemEstoque):
    try:
        item_dict = item.dict()
        new_id = db_add_item_estoque(item_dict)
        item.id = new_id
        return item
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao adicionar item: {str(e)}")

# --- Rotas Financeiras ---

@app.get("/api/financeiro/resumo", response_model=FinanceiroResumo, tags=["Financeiro"])
def get_financeiro_resumo():
    return db_get_financeiro_resumo()

@app.get("/api/financeiro/transacoes", response_model=List[Transacao], tags=["Financeiro"])
def get_transacoes():
    return db_get_transacoes()

@app.post("/api/financeiro/transacao", response_model=Transacao, status_code=201, tags=["Financeiro"])
def create_transacao(transacao: Transacao):
    try:
        t_dict = transacao.dict()
        new_id = db_add_transacao(t_dict)
        transacao.id = new_id
        return transacao
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao criar transação: {str(e)}")

@app.get("/api/financeiro/grafico", response_model=FinanceiroGrafico, tags=["Financeiro"])
def get_financeiro_grafico():
    return db_get_financeiro_grafico()

# --- Gráfico Python (Matplotlib) ---
import matplotlib
matplotlib.use('Agg') # Backend não-interativo para servidor
import matplotlib.pyplot as plt
import io
from fastapi.responses import StreamingResponse

@app.get("/api/financeiro/grafico_img", tags=["Financeiro"])
def get_financeiro_grafico_img():
    """Gera um gráfico financeiro profissional usando Matplotlib e retorna como imagem."""
    dados = db_get_financeiro_grafico()
    
    # Configuração do Gráfico
    plt.figure(figsize=(10, 6))
    meses = dados['labels']
    receitas = dados['receitas']
    despesas = dados['despesas']
    
    # Largura das barras e posições
    bar_width = 0.35
    index = range(len(meses))
    r1 = index
    r2 = [x + bar_width for x in r1]
    
    # Cores Profissionais
    color_receita = '#28a745' # Verde Sucesso
    color_despesa = '#dc3545' # Vermelho Perigo
    
    # Plotar barras
    bars1 = plt.bar(r1, receitas, color=color_receita, width=bar_width, edgecolor='white', label='Receitas')
    bars2 = plt.bar(r2, despesas, color=color_despesa, width=bar_width, edgecolor='white', label='Despesas')
    
    # Adicionar valores acima das barras
    def add_labels(bars):
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                plt.text(bar.get_x() + bar.get_width()/2., height,
                        f'R${int(height)}',
                        ha='center', va='bottom', fontsize=9, fontweight='bold', color='#444')

    add_labels(bars1)
    add_labels(bars2)
    
    # Estilização
    plt.xlabel('Mês', fontweight='bold')
    plt.ylabel('Valor (R$)', fontweight='bold')
    plt.title('Fluxo de Caixa Mensal: Receitas vs Despesas', fontweight='bold', pad=20)
    plt.xticks([r + bar_width/2 for r in range(len(meses))], meses)
    plt.legend()
    
    # Grid suave apenas no eixo Y
    plt.grid(axis='y', linestyle='--', alpha=0.3)
    
    # Remover bordas desnecessárias (spines)
    plt.gca().spines['top'].set_visible(False)
    plt.gca().spines['right'].set_visible(False)
    
    # Salvar em buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=100)
    buf.seek(0)
    plt.close()
    
    return StreamingResponse(buf, media_type="image/png")

# --- Rotas de Chat IA ---
from vetsys.vetsys_IA import vetsys_ai

class ChatRequest(BaseModel):
    message: str

@app.post("/api/chat", tags=["Chat IA"])
def chat_endpoint(request: ChatRequest):
    """ Envia uma mensagem para o chatbot e retorna a resposta. """
    try:
        response = vetsys_ai.obter_resposta(request.message)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no chat: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
