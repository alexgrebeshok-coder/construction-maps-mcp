# Yandex Maps API Key — подготовка к ротации

**Инцидент:** ключ Yandex Maps попал в committed docs (git history)  
**Redact в docs:** ✅ 05.07.2026 (commit `17f6157` v1.0.1 — ключ → `YOUR_YANDEX_KEY` / `your_api_key_here`)  
**Решение Саши:** 05.07.2026 — ротацию **отложить** («на потом, не забыть»)

> Агенты могут готовить redact в docs. **Не** ротировать ключ в Yandex Developer Console, **не** делать purge git history до явного «да» от Саши.

---

## Статус

| Элемент | Redact | Ротация |
|---------|--------|---------|
| Yandex Maps API key в tracked-файлах | ✅ 05.07.2026 | ⏸ **ждёт ротации** |
| Локальный `.env` (рабочий ключ) | — (не в git) | ⏸ **ждёт ротации** |
| Purge из git history | — | ⏸ после ротации |

---

## Где был ключ (до redact)

- `INSTALL.md`, `SUCCESS.md`, `TEST_REPORT.md`, `QUICKSTART.md`, `ГОТОВО.txt`
- `BUGFIX_REPORT.md` (фрагменты ключа в отчёте)
- Возможно другие markdown-файлы в истории

После v1.0.1 — плейсхолдеры `YOUR_YANDEX_KEY` / `your_api_key_here`.

---

## 📋 Чеклист: когда Саша говорит «да»

### 1. Ротация в Yandex Developer Console

- [ ] https://developer.tech.yandex.ru/ → API Keys
- [ ] Отозвать / удалить скомпрометированный ключ
- [ ] Создать новый ключ (ограничить по HTTP Referrer / IP при возможности)
- [ ] Обновить **только** локальный `.env`:

```bash
YANDEX_MAPS_API_KEY=новый_ключ_здесь
```

- [ ] **Не** коммитить `.env` (в `.gitignore`)

### 2. Smoke-test

```bash
cd ~/construction-maps-mcp
python test_simple.py
python test_functional.py   # опционально — реальные API-вызовы
```

- [ ] Геокодирование адреса OK
- [ ] MCP server стартует без `YANDEX_MAPS_API_KEY not set`

### 3. Purge из git history (после ротации)

> ⚠️ Force push. Только после нового ключа в `.env` и smoke-test.

- [ ] Backup репозитория
- [ ] `git filter-repo` по файлам, где был ключ (или BFG по паттерну)
- [ ] `git push origin main --force` (согласовать с Сашей)
- [ ] Обновить статус в штабе `ФОКУС_НЕДЕЛИ.md`

---

## Связанные файлы

- `.env.example` — шаблон с плейсхолдером
- `construction_maps_mcp/config.py` — валидация `YANDEX_MAPS_API_KEY`
- Claude MCP config: `claude-mcp-config.json` (ключ через env, не inline)

---

**Источник:** внутренний обзор репозиториев от 05.07.2026 (закрытый документ, не публикуется)
