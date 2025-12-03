// ../public/js/script.js
// Versão Profissional — Integração Completa com Backend + Estoque

document.addEventListener('DOMContentLoaded', () => {
  // -------------- CONFIG ----------------
  // Se estiver rodando na mesma origem (FastAPI servindo HTML), use string vazia ou relativa.
  // Se estiver separado, use http://127.0.0.1:8000
  const API_URL = 'http://127.0.0.1:8000'; // Forçando URL absoluta para garantir funcionamento local
  const SKELETON_DELAY = 600;
  const ACTIVE_PAGE_KEY = 'vetsysActivePageId';
  const ACTIVE_TITLE_KEY = 'vetsysActivePageTitle';

  // -------------- SELECTORS -------------
  const sidebarNavItems = document.querySelectorAll('.sidebar-nav a, .nav-item');
  const navItems = document.querySelectorAll('.nav-item');
  const pageContents = document.querySelectorAll('.page-content');
  const pageTitleElement = document.getElementById('page-title');
  const dashboardContent = document.getElementById('dashboard-content');
  const skeletonLoader = document.getElementById('skeleton-loader');

  // Elements specific to pages
  const patientsTableBody = document.querySelector('#page-pacientes .data-table tbody');
  const patientsTotalEl = document.querySelector('#page-pacientes .table-footer p');
  const pacienteSelect = document.getElementById('paciente-consulta');
  const consultaForm = document.getElementById('form-nova-consulta');
  const consultListEl = document.querySelector('.consult-list');
  const especieInputConsulta = document.getElementById('consulta-especie-input');

  // Paciente Form Elements
  const btnAddPatient = document.getElementById('btn-add-patient');
  const formNovoPacienteContainer = document.getElementById('form-novo-paciente-container');
  const formNovoPaciente = document.getElementById('form-novo-paciente');
  const btnCancelPaciente = document.getElementById('btn-cancel-paciente');

  // Estoque Elements
  const stockTableBody = document.querySelector('#page-estoque .data-table tbody');
  const btnAddItem = document.getElementById('btn-add-item');
  const btnCancelItem = document.getElementById('btn-cancel-item');
  const formNovoItemContainer = document.getElementById('form-novo-item-container');
  const formNovoItem = document.getElementById('form-novo-item');
  const estoqueSearch = document.getElementById('estoque-search');
  const estoqueFilterCat = document.getElementById('estoque-filter-categoria');

  // Dashboard Elements
  const dashTotalPacientes = document.querySelector('.total-pacientes p');
  const dashConsultasHoje = document.querySelector('.consultas-hoje p');
  const dashProcedimentosMes = document.querySelector('.procedimentos-mes p');
  const dashTotalEstoque = document.querySelector('.total-estoque p');

  // Chat Elements
  const chatIcon = document.getElementById('chat-icon');
  const chatWindow = document.getElementById('chat-window');
  const chatBody = document.getElementById('chat-body');
  const chatInput = document.getElementById('chat-input');

  // Calendar
  let calendar = null;
  // Cache para filtro local
  let allStockItems = [];

  // -------------- TOAST NOTIFICATIONS ----
  function showToast(message, type = 'info') {
    let container = document.querySelector('.toast-container');
    if (!container) {
      container = document.createElement('div');
      container.className = 'toast-container';
      document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    let icon = '';
    if (type === 'success') icon = '<i class="fas fa-check-circle"></i>';
    if (type === 'error') icon = '<i class="fas fa-exclamation-circle"></i>';
    if (type === 'info') icon = '<i class="fas fa-info-circle"></i>';

    toast.innerHTML = `${icon} <span>${message}</span>`;
    container.appendChild(toast);

    // Remove after animation (3s total as per CSS)
    setTimeout(() => {
      toast.remove();
    }, 3000);
  }

  // -------------- HELPERS ----------------
  function setActiveNavItem(pageId) {
    navItems.forEach(i => i.classList.remove('active'));
    const target = document.querySelector(`.sidebar-nav a[data-page="${pageId}"], .nav-item[data-page="${pageId}"]`);
    if (target) target.classList.add('active');
  }

  function hideAllPages() {
    pageContents.forEach(c => {
      c.classList.remove('active-page');
      c.classList.add('hidden');
    });
  }

  function showPageDOM(pageId, title) {
    hideAllPages();
    const target = document.getElementById('page-' + pageId);
    if (target) {
      target.classList.remove('hidden');
      target.classList.add('active-page');
      pageTitleElement.textContent = title || pageTitleElement.textContent;

      // Resize calendar if visible
      if (pageId === 'agendamento' && calendar) {
        setTimeout(() => calendar.updateSize(), 200);
      }
    }
    sessionStorage.setItem(ACTIVE_PAGE_KEY, pageId);
    sessionStorage.setItem(ACTIVE_TITLE_KEY, title || '');
  }

  function mapStatusClass(status) {
    if (!status) return 'inactive';
    const s = String(status).toLowerCase();
    if (s.includes('ativo')) return 'active';
    if (s.includes('inativo')) return 'inactive';
    if (s.includes('baixo')) return 'low-stock-alert';
    if (s.includes('ok')) return 'active';
    return '';
  }

  function formatDate(dateStr) {
    if (!dateStr) return '';
    const [year, month, day] = dateStr.split('-');
    return `${day}/${month}/${year}`;
  }

  // -------------- API CALLS --------------
  async function fetchJson(endpoint) {
    const res = await fetch(`${API_URL}${endpoint}`);
    if (!res.ok) throw new Error(`Erro em ${endpoint}: ${res.status}`);
    return await res.json();
  }

  async function postJson(endpoint, data) {
    const res = await fetch(`${API_URL}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    return res;
  }

  async function deleteJson(endpoint) {
    const res = await fetch(`${API_URL}${endpoint}`, {
      method: 'DELETE'
    });
    return res;
  }

  // -------------- RENDERERS --------------

  // 1. Dashboard
  async function loadDashboard() {
    try {
      const stats = await fetchJson('/api/dashboard');
      if (dashTotalPacientes) dashTotalPacientes.textContent = stats.total_pacientes;
      if (dashConsultasHoje) dashConsultasHoje.textContent = stats.consultas_hoje;
      if (dashProcedimentosMes) dashProcedimentosMes.textContent = stats.procedimentos_mes;
      if (dashTotalEstoque) dashTotalEstoque.textContent = stats.total_estoque;

      // Carregar próximas consultas
      const consultas = await fetchJson('/api/consultas');
      const nextApptList = document.querySelector('.next-appointments-card ul');
      if (nextApptList) {
        nextApptList.innerHTML = '';
        consultas.slice(0, 3).forEach(c => {
          const li = document.createElement('li');
          li.innerHTML = `<strong>${c.hora.slice(0, 5)}</strong> - ${c.paciente_nome} (${c.paciente_especie}) - ${c.motivo}`;
          nextApptList.appendChild(li);
        });
      }

    } catch (err) {
      console.error('Erro dashboard:', err);
    }
  }

  // 2. Pacientes
  async function loadPacientes() {
    try {
      // Ensure we are targeting the correct tbody
      const tbody = document.querySelector('#page-pacientes .data-table tbody');
      if (!tbody) return;

      tbody.innerHTML = '';
      const pacientes = await fetchJson('/api/pacientes');

      if (pacientes.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; padding: 20px;">Nenhum paciente encontrado.</td></tr>';
      }

      pacientes.forEach(p => {
        const statusClass = mapStatusClass(p.status);
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td>${escapeHtml(p.nome)}</td>
          <td>${escapeHtml(p.tutor)}</td>
          <td>${escapeHtml(p.especie)}</td>
          <td>${escapeHtml(p.raca)}</td>
          <td>—</td>
          <td><span class="status-badge ${statusClass}">${escapeHtml(p.status)}</span></td>
          <td>
            <button class="action-btn delete" data-id="${p.id}" title="Excluir"><i class="fas fa-trash"></i></button>
          </td>
        `;
        tbody.appendChild(tr);
      });

      if (patientsTotalEl) patientsTotalEl.textContent = `Total de Pacientes: ${pacientes.length}`;

      // Attach events (Delegation or direct attachment)
      attachDeleteListeners();

    } catch (err) {
      console.error('Erro pacientes:', err);
      showToast('Erro ao carregar pacientes.', 'error');
    }
  }

  function attachDeleteListeners() {
    document.querySelectorAll('.action-btn.delete').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        if (confirm('Tem certeza que deseja excluir este paciente?')) {
          const id = btn.dataset.id;
          try {
            await deleteJson(`/api/pacientes/${id}`);
            loadPacientes(); // reload
            loadDashboard(); // update stats
          } catch (err) {
            showToast('Erro ao excluir paciente.', 'error');
          }
        }
      });
    });
  }

  // 3. Consultas (Histórico e Form)
  async function loadConsultasPage() {
    // Carregar select de pacientes
    try {
      const pacientes = await fetchJson('/api/pacientes');
      if (pacienteSelect) {
        // Manter a opção selecionada se houver, senão resetar
        const currentVal = pacienteSelect.value;
        pacienteSelect.innerHTML = '<option value="">Selecione um paciente</option>';

        pacientes.forEach(p => {
          if ((p.status || '').toLowerCase() === 'ativo') {
            const opt = document.createElement('option');
            opt.value = p.id;
            opt.textContent = `${p.nome} (${p.especie})`;
            pacienteSelect.appendChild(opt);
          }
        });

        if (currentVal) pacienteSelect.value = currentVal;
      }
    } catch (err) { console.error("Erro ao carregar pacientes para select:", err); }

    // Carregar histórico
    try {
      const consultas = await fetchJson('/api/consultas');
      if (consultListEl) {
        consultListEl.innerHTML = ''; // Limpar lista atual

        if (consultas.length === 0) {
          consultListEl.innerHTML = '<li style="text-align:center; color:#888;">Nenhuma consulta registrada.</li>';
          return;
        }

        consultas.forEach(c => {
          const li = document.createElement('li');
          // Ícone baseado no motivo (simples heurística)
          let iconClass = 'fa-file-medical';
          const motivo = (c.motivo || '').toLowerCase();
          if (motivo.includes('vacina')) iconClass = 'fa-syringe';
          else if (motivo.includes('exame')) iconClass = 'fa-microscope';
          else if (motivo.includes('cirurgia')) iconClass = 'fa-procedures';

          li.innerHTML = `
            <div style="display:flex; align-items:center; gap:10px; width:100%;">
                <div style="background:#eef2f7; padding:8px; border-radius:50%; color:var(--primary-color);">
                    <i class="fas ${iconClass}"></i>
                </div>
                <div style="flex-grow:1;">
                    <strong>${formatDate(c.data)} às ${c.hora.slice(0, 5)}</strong><br>
                    <span style="color:#555;">${c.paciente_nome} (${c.paciente_especie} - ${c.paciente_raca || 'Raça N/A'})</span>
                    <div style="font-size:0.85rem; color:#777; margin-top:2px;">${c.motivo}</div>
                </div>
                <div style="text-align:right; font-size:0.8rem; color:#999;">
                    Dr(a). ${c.veterinario}
                </div>
            </div>
          `;
          consultListEl.appendChild(li);
        });
      }
    } catch (err) {
      console.error("Erro ao carregar histórico de consultas:", err);
      if (consultListEl) consultListEl.innerHTML = '<li style="color:red;">Erro ao carregar histórico.</li>';
    }
  }

  // 4. Estoque
  async function loadEstoque() {
    try {
      allStockItems = await fetchJson('/api/estoque');
      renderEstoqueTable(allStockItems);
    } catch (err) { console.error(err); }
  }

  function renderEstoqueTable(items) {
    if (!stockTableBody) return;
    stockTableBody.innerHTML = '';

    items.forEach(item => {
      const statusClass = mapStatusClass(item.status);
      const tr = document.createElement('tr');
      tr.innerHTML = `
            <td>${escapeHtml(item.item)}</td>
            <td>${escapeHtml(item.categoria)}</td>
            <td>${item.quantidade}</td>
            <td>${formatDate(item.validade)}</td>
            <td><span class="status-badge ${statusClass}">${escapeHtml(item.status)}</span></td>
            <td><button class="action-btn edit"><i class="fas fa-edit"></i></button></td>
        `;
      stockTableBody.appendChild(tr);
    });

    // Update summary cards
    const total = items.length;
    const low = items.filter(i => i.quantidade < 10).length;
    const expired = items.filter(i => new Date(i.validade) < new Date()).length;

    const totalEl = document.querySelector('.total-items p');
    if (totalEl) totalEl.textContent = total;

    const lowEl = document.querySelector('.low-stock .warning-count');
    if (lowEl) lowEl.textContent = low;

    const expEl = document.querySelector('.expired p');
    if (expEl) expEl.textContent = expired;
  }

  function filterEstoque() {
    const term = estoqueSearch.value.toLowerCase();
    const cat = estoqueFilterCat.value;

    const filtered = allStockItems.filter(item => {
      const matchesTerm = item.item.toLowerCase().includes(term);
      const matchesCat = cat === '' || item.categoria === cat;
      return matchesTerm && matchesCat;
    });
    renderEstoqueTable(filtered);
  }

  // 5. Financeiro
  let financeChartInstance = null;

  async function loadFinanceiro() {
    // 1. Resumo (Cards)
    try {
      const resumo = await fetchJson('/api/financeiro/resumo');
      document.querySelector('.summary-card.revenue p').textContent = `R$ ${resumo.receita_total.toFixed(2)}`;
      document.querySelector('.summary-card.expenses p').textContent = `R$ ${resumo.despesa_total.toFixed(2)}`;
      document.querySelector('.summary-card.profit p').textContent = `R$ ${resumo.lucro.toFixed(2)}`;
    } catch (e) { console.error("Erro resumo financeiro", e); }

    // 2. Lista de Transações
    try {
      const transacoes = await fetchJson('/api/financeiro/transacoes');
      const listEl = document.querySelector('.transaction-list');
      if (listEl) {
        listEl.innerHTML = '';
        if (transacoes.length === 0) {
          listEl.innerHTML = '<li style="text-align:center; color:#888;">Nenhuma transação recente.</li>';
        } else {
          transacoes.forEach(t => {
            const li = document.createElement('li');
            const isReceita = t.tipo === 'receita';
            const colorClass = isReceita ? 'income' : 'expense';
            const signal = isReceita ? '+' : '-';

            // Ícone baseado na origem
            let icon = '<i class="fas fa-exchange-alt"></i>';
            if (t.origem === 'consulta') icon = '<i class="fas fa-stethoscope"></i>';
            if (t.origem === 'estoque') icon = '<i class="fas fa-box"></i>';

            li.innerHTML = `
                        <div style="display:flex; align-items:center; gap:10px;">
                            <div style="background:#f0f2f5; padding:8px; border-radius:50%; color:#555;">${icon}</div>
                            <div style="display:flex; flex-direction:column;">
                                <span style="font-weight:600;">${escapeHtml(t.descricao)}</span>
                                <span style="font-size:0.8rem; color:#777;">${formatDate(t.data)} • ${t.categoria}</span>
                            </div>
                        </div>
                        <span class="${colorClass}" style="font-weight:bold;">${signal} R$ ${t.valor.toFixed(2)}</span>
                      `;
            listEl.appendChild(li);
          });
        }
      }
    } catch (e) { console.error("Erro lista transações", e); }

    // 3. Gráfico (Python Matplotlib)
    const imgChart = document.getElementById('financeChartImg');
    if (imgChart) {
      // Adiciona timestamp para evitar cache do navegador
      imgChart.src = `/api/financeiro/grafico_img?t=${new Date().getTime()}`;
    }
  }

  // Função renderFinanceChart removida pois agora usamos imagem do backend
  function renderFinanceChart(data) {
    // Placeholder vazio
  }

  // Lógica do Formulário Financeiro
  const finOrigemSelect = document.getElementById('fin-origem');
  const divFinReferencia = document.getElementById('div-fin-referencia');
  const finReferenciaSelect = document.getElementById('fin-referencia');
  const formNovaTransacao = document.getElementById('form-nova-transacao');

  if (finOrigemSelect) {
    finOrigemSelect.addEventListener('change', async (e) => {
      const val = e.target.value;
      if (val === 'consulta' || val === 'estoque') {
        divFinReferencia.classList.remove('hidden');
        finReferenciaSelect.innerHTML = '<option>Carregando...</option>';

        try {
          let items = [];
          if (val === 'consulta') {
            // Buscar consultas recentes
            const res = await fetchJson('/api/consultas');
            items = res.map(c => ({ id: c.id, label: `${formatDate(c.data)} - ${c.paciente_nome} (${c.motivo})` }));
          } else {
            // Buscar estoque
            const res = await fetchJson('/api/estoque');
            items = res.map(i => ({ id: i.id, label: `${i.item} (Qtd: ${i.quantidade})` }));
          }

          finReferenciaSelect.innerHTML = '<option value="">Selecione...</option>';
          items.forEach(i => {
            const opt = document.createElement('option');
            opt.value = i.id;
            opt.textContent = i.label;
            // Guardar texto extra para auto-preencher
            opt.dataset.text = i.label;
            finReferenciaSelect.appendChild(opt);
          });

        } catch (err) {
          console.error("Erro ao carregar referencias", err);
          finReferenciaSelect.innerHTML = '<option value="">Erro ao carregar</option>';
        }
      } else {
        divFinReferencia.classList.add('hidden');
        finReferenciaSelect.innerHTML = '';
      }
    });

    // Auto-preencher descrição ao selecionar referência
    finReferenciaSelect.addEventListener('change', (e) => {
      const selectedOpt = finReferenciaSelect.options[finReferenciaSelect.selectedIndex];
      const descInput = document.getElementById('fin-descricao');
      const origem = finOrigemSelect.value;

      if (selectedOpt && selectedOpt.value && descInput) {
        if (origem === 'consulta') {
          descInput.value = `Pagamento: ${selectedOpt.dataset.text}`;
        } else if (origem === 'estoque') {
          descInput.value = `Compra: ${selectedOpt.dataset.text}`;
        }
      }
    });
  }

  if (formNovaTransacao) {
    formNovaTransacao.addEventListener('submit', async (e) => {
      e.preventDefault();

      const tipo = document.getElementById('fin-tipo').value;
      const valor = parseFloat(document.getElementById('fin-valor').value);
      const origem = document.getElementById('fin-origem').value;
      const refId = document.getElementById('fin-referencia').value;
      const descricao = document.getElementById('fin-descricao').value;
      const categoria = document.getElementById('fin-categoria').value;
      const data = document.getElementById('fin-data').value;

      if (!valor || !descricao || !data || !categoria) {
        showToast("Preencha os campos obrigatórios.", "error");
        return;
      }

      try {
        const payload = {
          tipo, valor, data, descricao, categoria,
          origem: origem !== 'outro' ? origem : null,
          referencia_id: refId ? parseInt(refId) : null
        };

        const res = await postJson('/api/financeiro/transacao', payload);
        if (res.ok) {
          showToast("Transação registrada!", "success");
          formNovaTransacao.reset();
          divFinReferencia.classList.add('hidden');
          loadFinanceiro(); // Atualiza gráficos e listas
        } else {
          showToast("Erro ao registrar.", "error");
        }
      } catch (err) {
        console.error(err);
        showToast("Erro de conexão.", "error");
      }
    });
  }

  // 5. FullCalendar
  async function initCalendar() {
    const calendarEl = document.getElementById('fullcalendar-container');
    if (!calendarEl) return;

    // Destroy existing calendar to prevent duplication/conflicts
    if (calendar) {
      calendar.destroy();
      calendar = null;
    }

    // Fetch fresh events from API
    let events = [];
    try {
      const consultas = await fetchJson('/api/consultas');
      events = consultas.map(c => ({
        title: `${c.paciente_nome} - ${c.motivo}`,
        start: `${c.data}T${c.hora}`,
        allDay: false,
        color: '#4e73df',
        extendedProps: {
          veterinario: c.veterinario,
          especie: c.paciente_especie,
          raca: c.paciente_raca
        }
      }));
    } catch (err) {
      console.error("Erro ao carregar agenda:", err);
      showToast("Erro ao atualizar agenda.", "error");
    }

    calendar = new FullCalendar.Calendar(calendarEl, {
      initialView: 'dayGridMonth',
      locale: 'pt-br',
      headerToolbar: {
        left: 'prev,next today',
        center: 'title',
        right: 'dayGridMonth,timeGridWeek,timeGridDay'
      },
      navLinks: true,
      dayMaxEvents: true,
      events: events,
      height: 'auto',
      eventClick: function (info) {
        const props = info.event.extendedProps;
        const msg = `Consulta: ${info.event.title}\nVeterinário: ${props.veterinario}\nRaça: ${props.raca || 'N/A'}\nData: ${info.event.start.toLocaleString()}`;
        alert(msg);
      }
    });
    calendar.render();
  }

  async function handlePacienteSubmit(event) {
    event.preventDefault();
    const nome = document.getElementById('paciente-nome').value;
    const tutor = document.getElementById('paciente-tutor').value;
    const especie = document.getElementById('paciente-especie').value;
    const raca = document.getElementById('paciente-raca').value;
    const status = document.getElementById('paciente-status').value;

    if (!nome || !tutor || !especie || !raca) {
      showToast('Preencha todos os campos obrigatórios.', 'error');
      return;
    }

    try {
      const res = await postJson('/api/pacientes', { nome, tutor, especie, raca, status });
      if (res.ok) {
        showToast('Paciente registrado com sucesso!', 'success');
        formNovoPaciente.reset();
        formNovoPacienteContainer.classList.add('hidden');
        loadPacientes();
        loadDashboard();
      } else {
        showToast('Erro ao registrar paciente.', 'error');
      }
    } catch (err) {
      console.error(err);
      showToast('Erro de conexão.', 'error');
    }
  }

  async function handleConsultaSubmit(event) {
    event.preventDefault();

    // Captura valores e remove espaços extras
    const nome = document.getElementById('paciente-nome-input').value.trim();
    const tutor = document.getElementById('paciente-tutor-input').value.trim();
    const raca = document.getElementById('consulta-raca-input').value.trim();
    const especie = document.getElementById('consulta-especie-input').value.trim();
    const veterinario = document.getElementById('veterinario-consulta').value;
    const data = document.getElementById('data-consulta').value;
    const hora = document.getElementById('hora-consulta').value;
    const motivo = document.getElementById('motivo-consulta').value.trim();

    // Validação de campos obrigatórios
    if (!nome || !tutor || !raca || !especie || !veterinario || !data || !hora || !motivo) {
      showToast('Por favor, preencha todos os campos para agendar.', 'error');
      return;
    }

    // Feedback visual no botão
    const submitBtn = event.target.querySelector('button[type="submit"]');
    const originalBtnText = submitBtn ? submitBtn.textContent : 'Salvar';
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.textContent = 'Processando...';
    }

    try {
      console.log("Iniciando fluxo de agendamento...");

      // 1. Verificar se o paciente já existe ou criar um novo
      // Busca todos os pacientes (para MVP ok, em prod seria busca filtrada no backend)
      let pacienteId = null;

      try {
        const pacientes = await fetchJson('/api/pacientes');

        // Busca insensível a maiúsculas/minúsculas
        const pacienteExistente = pacientes.find(p =>
          p.nome.toLowerCase() === nome.toLowerCase() &&
          p.tutor.toLowerCase() === tutor.toLowerCase()
        );

        if (pacienteExistente) {
          console.log(`Paciente encontrado: ID ${pacienteExistente.id}`);
          pacienteId = pacienteExistente.id;
        } else {
          console.log("Paciente não encontrado. Criando novo...");
          const novoPacientePayload = {
            nome: nome,
            tutor: tutor,
            especie: especie,
            raca: raca,
            status: 'Ativo'
          };

          const resPac = await postJson('/api/pacientes', novoPacientePayload);

          if (!resPac.ok) {
            const errData = await resPac.json();
            throw new Error(`Falha ao criar paciente: ${errData.detail || 'Erro desconhecido'}`);
          }

          const newPac = await resPac.json();
          pacienteId = newPac.id;
          console.log(`Novo paciente criado com sucesso: ID ${pacienteId}`);
        }
      } catch (errPac) {
        throw new Error(`Erro na etapa de paciente: ${errPac.message}`);
      }

      if (!pacienteId) throw new Error("ID do paciente não pôde ser determinado.");

      // 2. Criar a Consulta vinculada ao ID do paciente
      const consultaPayload = {
        paciente_id: pacienteId,
        veterinario: veterinario,
        data: data,
        hora: hora,
        motivo: motivo
      };

      const resCons = await postJson('/api/consultas', consultaPayload);

      if (resCons.ok) {
        showToast('Agendamento realizado com sucesso!', 'success');
        event.target.reset(); // Limpa o formulário

        // Atualiza todas as visualizações relevantes
        console.log("Atualizando interfaces...");
        await loadPacientes();      // Atualiza tabela de pacientes
        await loadConsultasPage();  // Atualiza histórico de consultas
        await loadDashboard();      // Atualiza contadores
        await initCalendar();       // Atualiza calendário

      } else {
        const errData = await resCons.json();
        throw new Error(`Erro ao salvar consulta: ${errData.detail || 'Erro desconhecido'}`);
      }

    } catch (err) {
      console.error("Erro CRÍTICO no agendamento:", err);
      showToast(`Erro: ${err.message}`, 'error');
    } finally {
      // Restaura o botão
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.textContent = originalBtnText;
      }
    }
  }

  async function handleEstoqueSubmit(event) {
    event.preventDefault();
    const nome = document.getElementById('item-nome').value;
    const cat = document.getElementById('item-categoria').value;
    const qtd = parseInt(document.getElementById('item-qtd').value, 10);
    const validade = document.getElementById('item-validade').value;
    const status = document.getElementById('item-status').value;

    if (!nome || !cat || !validade) {
      showToast("Preencha todos os campos obrigatórios.", 'error');
      return;
    }

    try {
      const res = await postJson('/api/estoque', {
        item: nome,
        categoria: cat,
        quantidade: qtd,
        validade: validade,
        status: status
      });
      if (res.ok) {
        showToast("Item registrado com sucesso!", 'success');
        formNovoItem.reset();
        formNovoItemContainer.classList.add('hidden');
        loadEstoque();
        loadDashboard(); // update total items on dashboard
      } else {
        showToast("Erro ao registrar item.", 'error');
      }
    } catch (err) {
      console.error(err);
      showToast("Erro de conexão.", 'error');
    }
  }

  // -------------- NAVIGATION -------------
  sidebarNavItems.forEach(item => {
    item.addEventListener('click', async (e) => {
      e.preventDefault();
      const pageId = item.dataset.page;
      const pageTitle = item.dataset.title || item.textContent.trim();
      setActiveNavItem(pageId);

      await loadPageData(pageId);
      showPageDOM(pageId, pageTitle);
    });
  });

  async function loadPageData(pageId) {
    switch (pageId) {
      case 'inicio':
        await loadDashboard();
        break;
      case 'pacientes':
        await loadPacientes();
        break;
      case 'consultas':
        await loadConsultasPage();
        break;
      case 'agendamento':
        // Delay init to ensure DOM is visible
        setTimeout(initCalendar, 100);
        break;
      case 'estoque':
        await loadEstoque();
        break;
      case 'financeiro':
        await loadFinanceiro();
        break;
    }
  }

  // -------------- INITIAL LOAD -----------
  const savedPage = sessionStorage.getItem(ACTIVE_PAGE_KEY) || 'inicio';
  const savedTitle = sessionStorage.getItem(ACTIVE_TITLE_KEY) || 'Início';

  setActiveNavItem(savedPage);

  setTimeout(async () => {
    if (skeletonLoader) {
      skeletonLoader.classList.remove('skeleton-active');
      skeletonLoader.classList.add('hidden');
    }
    if (dashboardContent) dashboardContent.classList.remove('hidden');

    await loadPageData(savedPage);
    showPageDOM(savedPage, savedTitle);
  }, SKELETON_DELAY);

  // Event Listeners
  if (consultaForm) {
    consultaForm.addEventListener('submit', handleConsultaSubmit);
  }

  if (btnAddPatient) {
    // Listener removido para evitar conflito com o redirecionamento para Consultas
    // O botão agora é controlado pelo listener no final do arquivo
  }
  if (btnCancelPaciente) {
    btnCancelPaciente.addEventListener('click', () => {
      formNovoPacienteContainer.classList.add('hidden');
    });
  }
  if (formNovoPaciente) {
    formNovoPaciente.addEventListener('submit', handlePacienteSubmit);
  }

  if (btnAddItem) {
    btnAddItem.addEventListener('click', () => {
      formNovoItemContainer.classList.remove('hidden');
    });
  }
  if (btnCancelItem) {
    btnCancelItem.addEventListener('click', () => {
      formNovoItemContainer.classList.add('hidden');
    });
  }
  if (formNovoItem) {
    formNovoItem.addEventListener('submit', handleEstoqueSubmit);
  }
  if (estoqueSearch) {
    estoqueSearch.addEventListener('input', filterEstoque);
  }
  if (estoqueFilterCat) {
    estoqueFilterCat.addEventListener('change', filterEstoque);
  }

  // Chat Logic
  if (chatIcon && chatWindow) {
    chatIcon.addEventListener('click', () => {
      const isFlex = chatWindow.style.display === 'flex';
      chatWindow.style.display = isFlex ? 'none' : 'flex';
      if (!isFlex && chatInput) setTimeout(() => chatInput.focus(), 100);
    });
  }

  if (chatInput) {
    chatInput.addEventListener('keypress', async (e) => {
      if (e.key === 'Enter') {
        const msg = chatInput.value.trim();
        if (!msg) return;

        // User Message
        appendMessage(msg, 'user');
        chatInput.value = '';

        // Loading
        const loadingId = appendMessage('Digitando...', 'bot', true);

        try {
          const res = await postJson('/api/chat', { message: msg });
          removeMessage(loadingId);
          if (res.response) {
            appendMessage(res.response, 'bot');
          } else {
            appendMessage('Não entendi, pode repetir?', 'bot');
          }
        } catch (err) {
          removeMessage(loadingId);
          appendMessage('Erro de conexão com a IA.', 'bot');
        }
      }
    });
  }

  function appendMessage(text, sender, isLoading = false) {
    if (!chatBody) return;
    const div = document.createElement('div');
    div.className = `chat-message ${sender} ${isLoading ? 'loading-msg' : ''}`;
    div.id = isLoading ? `msg-${Date.now()}` : '';

    // Markdown simple parser for bold
    const formatted = text.replace(/\*\*(.*?)\*\*/g, '<b>$1</b>');
    div.innerHTML = formatted;

    chatBody.appendChild(div);
    chatBody.scrollTop = chatBody.scrollHeight;
    return div.id;
  }

  function removeMessage(id) {
    if (!id) return;
    const el = document.getElementById(id);
    if (el) el.remove();
  }

  // Utils
  function escapeHtml(str) {
    if (!str) return '';
    return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }
});


// Localiza os elementos
const btnNovoPaciente = document.getElementById('btn-add-patient');
const linkConsultas = document.querySelector('.nav-item[data-page="consultas"]');

// Verifica se os elementos existem antes de adicionar o listener
if (btnNovoPaciente && linkConsultas) {
  btnNovoPaciente.addEventListener('click', function (event) {
    event.preventDefault(); // Impede qualquer ação padrão do botão

    // Simula o clique no link de navegação da aba "Consultas"
    linkConsultas.click();

    // Opcional: Se você quiser que o formulário de Nova Consulta já esteja preenchido
    // ou em foco, você faria a lógica aqui.

    // Opcional: Se quiser que o título da aba mude imediatamente
    document.getElementById('page-title').textContent = 'Consultas';
  });
}