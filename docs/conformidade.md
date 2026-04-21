# Conformidade e privacidade — nota LGPD

> **Status:** 🟡 rascunho pré-preenchido. **Vanderson Darriba revisa e aprova (ticket T11).**
>
> **Dono final:** Vanderson Darriba
> **Prazo:** 10/05/2026
> **Escopo:** confirmar que o módulo de recomendação do `biblioteca_mvp` está conforme a LGPD (Lei 13.709/2018) no contexto acadêmico do trabalho.

---

## 1. Dados pessoais tratados pelo sistema

| Dado | Origem | Categoria LGPD | Finalidade |
|---|---|---|---|
| Nome do leitor | Cadastro | Dado pessoal comum | Identificação no empréstimo |
| Email | Cadastro | Dado pessoal comum | Login + contato |
| Celular | Cadastro | Dado pessoal comum | Contato opcional |
| Data de nascimento | Cadastro | Dado pessoal comum | Opcional, sem uso obrigatório |
| Histórico de empréstimos | Gerado | Dado pessoal comum | Operacional + recomendação personalizada |

**Nenhum dado sensível** (saúde, origem racial, orientação política, biometria etc.) é coletado.

---

## 2. Dados usados pelo módulo de recomendação

O módulo **`recomendador/`** trabalha exclusivamente com:

1. **Metadados públicos das obras** — título, autor, tipo de obra. Estes já seriam publicamente catalogáveis em qualquer biblioteca acadêmica; não são dados pessoais.
2. **Histórico agregado de empréstimos** — IDs de livros lidos por um leitor, sem nome ou demais PII expostos na camada de IA.

**O que NÃO vai para o modelo de embeddings:**
- Nome do leitor
- Email, celular, data de nascimento
- Qualquer texto escrito pelo usuário (ex: comentários — que nem existem no MVP)

---

## 3. Bases legais aplicáveis (Art. 7º LGPD)

| Tratamento | Base legal |
|---|---|
| Cadastro de leitor | Execução de contrato (empréstimo) / consentimento |
| Armazenamento do histórico | Execução de contrato |
| Uso do histórico para recomendar | **Legítimo interesse** (Art. 7º IX) ou consentimento explícito, a confirmar com o professor |
| Embeddings de metadados | N/A (não são dados pessoais) |

---

## 4. Direitos do titular (leitor)

O sistema deve permitir:

- [ ] **Consulta** dos seus dados (campo `pessoa` → já disponível via admin)
- [ ] **Correção** (via edit na view `pessoa_update`)
- [ ] **Exclusão** — ao deletar um `pessoa`, cascata apaga embeddings derivados do histórico *(a implementar: hoje `emprestimo.leitor` tem `on_delete=PROTECT`; decidir se muda pra CASCADE ou pseudonimiza)*
- [ ] **Exportação** dos dados em formato legível — fora do escopo do MVP, documentar como tarefa futura
- [ ] **Opt-out da recomendação personalizada** — adicionar checkbox `pessoa.opt_in_recomendacao_personalizada` (default=False), exigir opt-in explícito antes de `recomendar_para_leitor()` rodar

---

## 5. Retenção de dados

- **Cadastros ativos:** mantidos enquanto o leitor usar o sistema
- **Histórico de empréstimos:** mantido por 2 anos após a última atividade (prazo alinhado com bibliotecas universitárias)
- **Embeddings de obras:** sem prazo — são metadados públicos
- **Logs de acesso:** 6 meses (Django default)

---

## 6. Pontos a implementar antes de apresentar o trabalho

1. [ ] Adicionar campo `opt_in_recomendacao_personalizada` em `pessoa` (boolean, default False) e condicionar `recomendar_para_leitor` a esse flag
2. [ ] Adicionar aviso de privacidade no rodapé do template `base.html` linkando para esta página
3. [ ] Documentar no README como exportar dados de um leitor (comando shell ou exportar JSON)
4. [ ] Revisar `on_delete` em `emprestimo.leitor` (hoje PROTECT) — se ficar PROTECT, implementar exclusão lógica via `ativo=False`

---

## 7. Limites do escopo acadêmico

- O sistema **não vai para produção real** — é um MVP didático
- **Dados são fictícios** (seed com nomes inventados)
- Não há integração com sistemas externos, APIs de terceiros ou coleta passiva
- Não há uso de cookies de tracking nem analytics externos

Isto **reduz significativamente** a superfície LGPD do trabalho, mas o grupo ainda implementa as práticas acima para demonstrar conhecimento da norma na apresentação.

---

## 8. Aprovação

- [ ] Vanderson Darriba revisou e aprovou em: _____________________
- [ ] Antonio Jansen (líder) revisou em: _____________________
