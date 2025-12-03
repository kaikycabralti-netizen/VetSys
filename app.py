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
    
    conn.commit()
    conn.close()
    print("Banco de dados inicializado com sucesso (Pacientes, Consultas, Estoque, Financeiro).")

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
