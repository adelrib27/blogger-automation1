# C65 — proposta de revisão LIVE (NÃO é aprovação)

**Status:** `AWAITING_OWNER_APPROVAL` · **NÃO autoriza publicar**. Documento somente para encaminhar revisão individual de um post real. Nenhum manifesto `live_approvals.d/*.json` aprovado foi criado.

| Campo | Valor validado pela API + gate C65 |
|---|---|
| Plataforma | WordPress, blog real Casa e Decoração |
| Rota V31 | `wordpress_casa_decoracao` |
| Post ID | `305` |
| Status remoto verificado | `draft` |
| Título | Guia prático: Vaso Decorativo Rômulo Âmbar 30cm – Design Moderno e Elegante |
| Slug | `v31-31856a8a43a1-58259898640` |
| SHA256 de HTML bruto | `d4da2df9095fe9a560c3d7cfb9bfb0ea3d55f161b8dbc2bcb4c0f1acb2d8584a` |
| Gate comercial C65 | SKU aprovado R2, campanha exata, imagem real, CTA, disclosure |
| Gate editorial técnico | 8 seções, regras conservadoras aplicadas |
| Publicações realizadas pelo teste | **0** |
| Manifesto de aprovação | **Ausente** |

Evidências: [DRAFT real da C65](https://github.com/adelrib27/blogger-automation1/actions/runs/44563725746) e [auditoria LIVE somente leitura C65](https://github.com/adelrib27/blogger-automation1/actions/runs/44564287283).

## Revisão necessária antes de qualquer LIVE

- **Editorial/factual:** conferir texto integral, título, acentuação, coerência do tema, gramática, repetição, medidas, material, propriedades/benefícios, linguagem sobre avaliações/testes e promessas não comprovadas. A aprovação técnica NÃO garante a veracidade de cada afirmação.
- **Oferta/afiliado:** conferir que o SKU fotografado corresponde ao anúncio atual, campanha exata, URL afiliada funcional, disponibilidade e características somente conforme anúncio; revalidar caso o produto ou campanha mudem.
- **Conteúdo no CMS:** verificar renderização móvel, imagem, CTA patrocinado, aviso de comissão e os dois URLs internos do mesmo domínio. Validar conformidade com política do blog e regras aplicáveis.
- **Proprietário:** autorizar expressamente **este post ID 305 e seu conteúdo específico**, não o sistema inteiro; qualquer edição exige novo SHA256 e reaprovação.

**Somente após revisão real:** criar um manifesto de aprovação individual conforme [live_approvals.d/README.md](live_approvals.d/README.md) e usar o workflow manual [v31_manual_live_release.yml](../.github/workflows/v31_manual_live_release.yml) com confirmação exata. **Não preencher `owner_authorized:true` por inferência ou autonomia do operador.**

Recomendação operacional: manter o DRAFT #305 intacto até aprovação. Não reexecutar writer nem tentar publicar automaticamente a partir deste relatório.
