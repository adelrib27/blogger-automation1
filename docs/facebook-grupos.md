# Facebook Grupos — fila assistida

Este módulo distribui artigos do blog para grupos do Facebook em modo assistido. Ele **não publica automaticamente em grupos** e não usa automação de navegador, sessão, cookie ou API não oficial.

## Fluxo

1. O Blogger publica um artigo.
2. O workflow `Facebook Grupos — Preparar Fila` roda às 09:20 e 18:20 (horário de Brasília/Recife) e também pode ser executado manualmente.
3. O sistema seleciona grupos ativos compatíveis com o tema do artigo.
4. São criadas até 3 tarefas por artigo por dia, respeitando o limite de 3 pendências por artigo.
5. Cada grupo recebe uma variação de texto diferente.
6. O painel HTML permite abrir o grupo, abrir o artigo, abrir a imagem, copiar o texto e copiar o Queue ID.
7. Depois da postagem manual, o workflow `Facebook Grupos — Marcar Resultado` move a tarefa da fila para o histórico.
8. O histórico impede que o mesmo artigo seja reenviado ao mesmo grupo.

## Cadastro de grupos

Arquivo: `data/facebook_grupos.json`

Exemplo:

```json
[
  {
    "id": "casa-decoracao-01",
    "nome": "Dicas para Casa e Decoração",
    "url": "https://www.facebook.com/groups/SEU_GRUPO",
    "temas": ["Casa e Decoração", "Organização"],
    "ativo": true,
    "prioridade": 1
  },
  {
    "id": "achadinhos-01",
    "nome": "Achadinhos para Casa",
    "url": "https://www.facebook.com/groups/OUTRO_GRUPO",
    "temas": ["todos"],
    "ativo": true,
    "prioridade": 2
  }
]
```

### Temas

- Use temas específicos, como `Cozinha`, `Quarto`, `Banheiro`, `Organização` ou `Casa e Decoração`, para distribuir somente artigos compatíveis.
- Use `todos`, `geral`, `casa`, `casa e decoracao` ou `achadinhos` para um grupo que pode receber qualquer conteúdo do blog.
- Se `temas` estiver vazio, o grupo é tratado como genérico por padrão.

## Rodízio e proteção contra repetição

A configuração está em `config/facebook_grupos.json`.

- `max_groups_per_article_per_day`: máximo de grupos por artigo em um dia.
- `max_pending_per_article`: máximo de tarefas pendentes do mesmo artigo.
- `default_variations`: quantidade de variações de texto disponíveis.
- O sistema prioriza grupos com prioridade menor, menos publicações anteriores e uso mais antigo.
- Um par `artigo + grupo` publicado nunca volta para a fila.

## Arquivos de estado

- `data/facebook_grupos.json`: cadastro dos grupos.
- `data/facebook_fila_grupos.json`: tarefas pendentes.
- `data/facebook_grupos_publicados.json`: histórico de tarefas concluídas ou ignoradas.

## Painel

O workflow de preparação gera o artefato `facebook-grupos-fila`, contendo `facebook_grupos_painel.html`.

No painel:

- **Abrir grupo** abre o destino no Facebook.
- **Abrir artigo** abre o post do blog.
- **Abrir imagem** abre a imagem destacada.
- **Copiar texto** copia a versão preparada para aquele grupo.
- **Copiar Queue ID** copia o identificador da tarefa.
- **Marcar como publicado** copia o Queue ID e abre o workflow de registro no GitHub.

## Segurança

O modo é permanentemente `assisted_only` com `publish_external: false`. Qualquer alteração que tente habilitar publicação automática em grupos faz o gerador abortar.
