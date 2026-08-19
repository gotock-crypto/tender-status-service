const $ = (id) => document.getElementById(id);
const STATUS_LABELS = { draft: "Черновик", active: "Активен", won: "Выигран", lost: "Проигран" };
const ALLOWED_TRANSITIONS = { draft: ["active"], active: ["won", "lost"], won: [], lost: [] };
const state = { tenders: [], currentTender: null };

function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (ch) => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#039;"}[ch]));
}
function money(value) { return new Intl.NumberFormat("ru-RU", { style:"currency", currency:"RUB", maximumFractionDigits:0 }).format(Number(value)); }
function date(value) { return new Date(value).toLocaleDateString("ru-RU"); }

async function api(url, options = {}) {
  const response = await fetch(url, { headers: { "Content-Type":"application/json", ...(options.headers || {}) }, ...options });
  if (response.status === 204) return null;
  const text = await response.text();
  let payload = null;
  try { payload = text ? JSON.parse(text) : null; } catch { payload = text; }
  if (!response.ok) {
    const message = typeof payload === "object" ? (payload.detail || JSON.stringify(payload)) : String(payload || `HTTP ${response.status}`);
    throw new Error(message);
  }
  return payload;
}

function toast(message, type = "ok") {
  const node = $("toast"); node.textContent = message; node.className = `toast show ${type === "error" ? "error" : ""}`;
  clearTimeout(toast.timer); toast.timer = setTimeout(() => node.className = "toast", 2500);
}
function showModal(html) { $("modal-content").innerHTML = html; $("modal").classList.remove("hidden"); }
function closeModal() { $("modal").classList.add("hidden"); $("modal-content").innerHTML = ""; }

function formHtml(tender = null) {
  return `<div class="modal-title"><div><div class="eyebrow">${tender ? "EDIT TENDER" : "NEW TENDER"}</div><h2>${tender ? "Редактировать тендер" : "Новый тендер"}</h2></div><button type="button" class="close" data-action="close">×</button></div>
  <form id="tender-form" class="form">
    <label>Название тендера<input name="title" required maxlength="500" value="${esc(tender?.title || "")}" placeholder="Например, Поставка серверного оборудования"></label>
    <label>Заказчик<input name="customer" required maxlength="300" value="${esc(tender?.customer || "")}" placeholder="Наименование заказчика"></label>
    <div class="two"><label>Номер контракта<input name="contract_number" maxlength="100" value="${esc(tender?.contract_number || "")}" placeholder="T-2026-001"></label><label>Начальная цена, ₽<input name="initial_price" required type="number" min="1" step="0.01" value="${tender ? Number(tender.initial_price) : ""}"></label></div>
    <div class="form-actions"><button type="button" class="btn ghost" data-action="close">Отмена</button><button type="submit" class="btn primary">${tender ? "Сохранить изменения" : "Создать тендер"}</button></div>
  </form>`;
}

async function load() {
  try {
    const status = $("filter").value; const data = await api(`/api/v1/tenders${status ? `?status=${status}` : ""}`);
    state.tenders = data || []; render();
  } catch (error) { toast(error.message, "error"); }
}

function render() {
  const query = $("search").value.toLowerCase().trim();
  const visible = state.tenders.filter((t) => `${t.title} ${t.customer} ${t.contract_number || ""}`.toLowerCase().includes(query));
  $("count-label").textContent = `${visible.length} ${visible.length === 1 ? "запись" : visible.length < 5 ? "записи" : "записей"}`;
  $("rows").innerHTML = visible.map((t) => `<tr><td><div class="title">${esc(t.title)}</div><div class="muted">${esc(t.contract_number || "Без номера")}</div></td><td>${esc(t.customer)}</td><td class="price">${money(t.initial_price)}</td><td><span class="badge ${t.status}">${STATUS_LABELS[t.status]}</span></td><td class="muted">${date(t.updated_at)}</td><td><button class="icon-btn" data-action="details" data-id="${t.id}">→</button></td></tr>`).join("");
  $("empty").classList.toggle("hidden", visible.length > 0);
  const total = state.tenders.length, active = state.tenders.filter((t) => t.status === "active").length, won = state.tenders.filter((t) => t.status === "won").length, volume = state.tenders.reduce((sum, t) => sum + Number(t.initial_price), 0);
  $("stats").innerHTML = [["Всего тендеров",total,"в системе"],["Активные",active,"в работе"],["Выиграны",won,"успешных"],["Объём закупок",money(volume),"начальная цена"]].map(([a,b,c]) => `<div class="stat"><span>${a}</span><strong>${b}</strong><small>${c}</small></div>`).join("");
}

function openCreate() {
  showModal(formHtml());
  $("tender-form").addEventListener("submit", createTender);
}
async function createTender(event) {
  event.preventDefault(); const form = event.currentTarget; const button = form.querySelector('button[type="submit"]'); button.disabled = true; button.textContent = "Создаём…";
  const data = Object.fromEntries(new FormData(form));
  try { await api("/api/v1/tenders", { method:"POST", body:JSON.stringify({ title:data.title.trim(), customer:data.customer.trim(), contract_number:data.contract_number.trim() || null, initial_price:Number(data.initial_price) }) }); closeModal(); await load(); toast("Тендер создан"); }
  catch (error) { button.disabled = false; button.textContent = "Создать тендер"; toast(error.message,"error"); }
}

async function openDetails(id) {
  try {
    const tender = await api(`/api/v1/tenders/${id}`); state.currentTender = tender;
    const allowedStatuses = ALLOWED_TRANSITIONS[tender.status] || [];
    const statusControl = allowedStatuses.length
      ? `<div class="two"><label>Новый статус<select name="status">${allowedStatuses.map((key)=>`<option value="${key}">${STATUS_LABELS[key]}</option>`).join("")}</select></label><label>Кто изменил<input name="changed_by" required maxlength="200" placeholder="Иван Иванов"></label></div><label>Причина<textarea name="reason" required maxlength="2000" placeholder="Укажите основание изменения статуса"></textarea></label><button type="submit" class="btn primary">Сохранить статус</button>`
      : `<div class="terminal-state"><strong>Статус завершён</strong><span>Тендер находится в финальном состоянии и больше не может быть переведён в другой статус.</span></div>`;
    showModal(`<div class="modal-title"><div><span class="badge ${tender.status}">${STATUS_LABELS[tender.status]}</span><h2>${esc(tender.title)}</h2><div class="muted">${esc(tender.customer)} · ${esc(tender.contract_number || "Без номера")}</div></div><button type="button" class="close" data-action="close">×</button></div>
      <div class="detail-grid"><div><span>Начальная цена</span><b>${money(tender.initial_price)}</b></div><div><span>Создан</span><b>${date(tender.created_at)}</b></div><div><span>Обновлён</span><b>${date(tender.updated_at)}</b></div></div>
      <div class="detail-actions"><button class="btn secondary" data-action="edit" data-id="${tender.id}">✎ Редактировать</button><button class="btn danger" data-action="delete" data-id="${tender.id}">Удалить</button></div>
      <div class="section"><h3>Изменить статус</h3><form id="status-form" class="form">${statusControl}</form></div>
      <div class="section"><h3>История статусов</h3><div class="timeline">${tender.history.length ? tender.history.map((item)=>`<div class="event"><span class="dot"></span><div><b>${STATUS_LABELS[item.old_status]} → ${STATUS_LABELS[item.new_status]}</b><p>${esc(item.reason)}</p><small>${esc(item.changed_by)} · ${new Date(item.changed_at).toLocaleString("ru-RU")}</small></div></div>`).join("") : "<p class='muted'>История изменений пока пуста.</p>"}</div></div>`);
    if (allowedStatuses.length) $("status-form").addEventListener("submit", (event)=>changeStatus(event,tender.id));
  } catch(error) { toast(error.message,"error"); }
}

async function editTender(id) {
  try { const tender=await api(`/api/v1/tenders/${id}`); showModal(formHtml(tender)); $("tender-form").addEventListener("submit", (event)=>saveTender(event,id)); }
  catch(error){ toast(error.message,"error"); }
}
async function saveTender(event,id){
  event.preventDefault(); const form=event.currentTarget; const button=form.querySelector('button[type="submit"]'); button.disabled=true; button.textContent="Сохраняем…"; const data=Object.fromEntries(new FormData(form));
  try { await api(`/api/v1/tenders/${id}`,{method:"PUT",body:JSON.stringify({title:data.title.trim(),customer:data.customer.trim(),contract_number:data.contract_number.trim()||null,initial_price:Number(data.initial_price)})}); closeModal(); await load(); toast("Изменения сохранены"); }
  catch(error){ button.disabled=false; button.textContent="Сохранить изменения"; toast(error.message,"error"); }
}
async function deleteTender(id){
  try { const tender=await api(`/api/v1/tenders/${id}`); if(!window.confirm(`Удалить тендер «${tender.title}»?\nЭто действие нельзя отменить.`)) return; await api(`/api/v1/tenders/${id}`,{method:"DELETE"}); closeModal(); await load(); toast("Тендер удалён"); }
  catch(error){ toast(error.message,"error"); }
}
async function changeStatus(event,id){
  event.preventDefault(); const form=event.currentTarget; const button=form.querySelector('button[type="submit"]'); button.disabled=true; button.textContent="Сохраняем…"; const payload=Object.fromEntries(new FormData(form));
  try { await api(`/api/v1/tenders/${id}/status`,{method:"PATCH",body:JSON.stringify(payload)}); closeModal(); await load(); toast("Статус обновлён"); }
  catch(error){ button.disabled=false; button.textContent="Сохранить статус"; toast(error.message,"error"); }
}

function bindEvents(){
  $("create-btn").addEventListener("click",openCreate);
  $("filter").addEventListener("change",load);
  $("refresh").addEventListener("click",load);
  $("search").addEventListener("input",render);
  $("modal").addEventListener("click",(event)=>{
    if(event.target.id==="modal" || event.target.closest('[data-action="close"]')) closeModal();
    const button=event.target.closest("[data-action]"); if(!button) return; const id=Number(button.dataset.id);
    if(button.dataset.action==="details") openDetails(id); if(button.dataset.action==="edit") editTender(id); if(button.dataset.action==="delete") deleteTender(id);
  });
  $("rows").addEventListener("click",(event)=>{ const button=event.target.closest('[data-action="details"]'); if(button) openDetails(Number(button.dataset.id)); });
}
window.addEventListener("DOMContentLoaded",()=>{bindEvents();load();});
