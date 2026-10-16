import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "casa_decoracao" / "data" / "editorial_queue_100.json"

PRODUCTS = [
    ("Escorredor de Louças 2 Andares", "https://vt.tiktok.com/ZS9DVaKwB15qr-TEaTI/", "Cozinha", ["como escolher para cozinha pequena", "como organizar pratos e talheres na bancada", "o que medir antes de comprar", "como comparar modelos de 1 e 2 andares"]),
    ("Jogo de Toalhas de Banho 4 Peças", "https://vt.tiktok.com/ZS9DVme6ftpPw-mv1pz/", "Cama, Mesa e Banho", ["como escolher um jogo de toalhas para o dia a dia", "o que observar em gramatura, tamanho e acabamento", "como montar um enxoval de banho funcional", "como organizar toalhas em banheiro pequeno"]),
    ("Kit de Potes para Alimentos com Travas", "https://vt.tiktok.com/ZS9DVmNxuKAVr-oyWt7/", "Cozinha", ["como escolher potes para organizar a despensa", "potes com trava: o que observar antes da compra", "como organizar mantimentos em cozinha pequena", "como reduzir bagunça usando potes empilháveis"]),
    ("Varal de Chão 3 Andares Dobrável", "https://vt.tiktok.com/ZS9DVm2Jj9628-F23ko/", "Organização", ["como escolher varal de chão para apartamento", "o que medir antes de comprar um varal dobrável", "como otimizar a secagem de roupas em espaço pequeno", "varal vertical ou tradicional: qual faz mais sentido"]),
    ("Travesseiro Cervical Ortopédico", "https://vt.tiktok.com/ZS9DVmjhnuqCH-wfiUR/", "Quarto", ["o que observar antes de escolher um travesseiro cervical", "altura e posição de dormir: como avaliar um travesseiro", "como montar uma cama mais confortável sem exageros", "travesseiro cervical: para quem pode fazer sentido"]),
    ("Cortador de Legumes 16 em 1", "https://vt.tiktok.com/ZS9DVmMhpQGtP-U7HVG/", "Cozinha", ["como escolher um cortador de legumes multifuncional", "segurança e limpeza: o que conferir em cortadores com lâminas", "como ganhar praticidade no pré-preparo de legumes", "cortador manual ou faca: quando cada opção faz sentido"]),
    ("Percarbonato de Sódio", "https://vt.tiktok.com/ZS9DVmBWeeENt-CC5PO/", "Limpeza e Utilidades", ["percarbonato de sódio: o que é e o que conferir antes de usar", "como organizar produtos de lavanderia com segurança", "como evitar misturas inadequadas na limpeza doméstica", "cuidados gerais ao testar tira-manchas em tecidos"]),
    ("Kit com 5 Lençóis Queen", "https://vt.tiktok.com/ZS9DVmSaMgcv9-PZJbS/", "Cama, Mesa e Banho", ["como escolher lençol queen sem errar nas medidas", "como montar um enxoval de cama prático", "o que observar em lençóis com elástico", "como organizar jogos de cama no armário"]),
    ("Coberdrom Sherpa", "https://vt.tiktok.com/ZS9DVmPhvUArW-DxBkv/", "Cama, Mesa e Banho", ["como escolher cobertor para noites frias", "o que observar em coberdrom e mantas volumosas", "como guardar cobertores sem ocupar tanto espaço", "como combinar conforto e decoração na cama"]),
    ("Capa de Colchão Impermeável", "https://vt.tiktok.com/ZS9DoHck9jm2J-0ScOG/", "Cama, Mesa e Banho", ["como escolher capa de colchão com elástico", "o que medir antes de comprar proteção para colchão", "como proteger o colchão no uso diário", "capa ou protetor de colchão: diferenças práticas"]),
    ("Tábua de Corte em Aço Inoxidável", "https://vt.tiktok.com/ZS9DoHou58duP-PyzzS/", "Cozinha", ["como escolher uma tábua de corte para a cozinha", "aço, madeira ou plástico: o que considerar", "como organizar a bancada para preparo de alimentos", "o que conferir em tamanho e acabamento de uma tábua"]),
    ("Caminho de Mesa Bordado", "https://vt.tiktok.com/ZS9DoHEx2MBNK-eE4Sc/", "Decoração", ["como usar caminho de mesa na decoração", "como escolher medida de caminho de mesa", "ideias simples para valorizar a mesa posta", "como combinar caminho de mesa com louças neutras"]),
    ("Kit de Fronhas Percal", "https://vt.tiktok.com/ZS9Do9RDxoBD6-CA8wY/", "Cama, Mesa e Banho", ["como escolher fronhas para o uso diário", "o que conferir em medidas de fronhas", "como renovar a cama trocando apenas fronhas", "como organizar fronhas e jogos de cama"]),
    ("Kit Colcha Cobre Leito Luxo", "https://vt.tiktok.com/ZS9Do98TNANqs-VlrXA/", "Cama, Mesa e Banho", ["como escolher colcha cobre-leito para o quarto", "como combinar colcha com cabeceira e cortina", "o que medir antes de comprar uma colcha", "como criar uma cama visualmente organizada"]),
    ("Cobre Leito Piquet Premium", "https://vt.tiktok.com/ZS9Do9Ym1btGC-yNuAf/", "Cama, Mesa e Banho", ["cobre-leito piquet: o que observar antes de comprar", "como escolher cobre-leito para casal, queen ou king", "como usar textura na decoração do quarto", "como cuidar da aparência da cama no dia a dia"]),
    ("Petisqueiras Barquinha", "https://vt.tiktok.com/ZS9Do9BhQQg3o-sakHh/", "Cozinha", ["como montar uma mesa de petiscos simples", "como escolher petisqueiras para receber visitas", "petisqueiras pequenas: como organizar frios e acompanhamentos", "como guardar peças de servir sem bagunça"]),
    ("Escova de Limpeza Multiuso 4 em 1", "https://vt.tiktok.com/ZS9Do9ynBjQS2-fgGFD/", "Limpeza e Utilidades", ["como escolher escova multiuso para limpeza doméstica", "como separar escovas por área da casa", "como montar um kit compacto de limpeza", "o que observar em cabos, cerdas e encaixes"]),
    ("Jogo de Lençol de Malha Casal", "https://vt.tiktok.com/ZS9Do9fSkVphK-juoDG/", "Cama, Mesa e Banho", ["lençol de malha: o que observar antes de comprar", "como escolher jogo de cama para uso frequente", "como conferir medidas de lençol casal", "como manter jogos de cama organizados"]),
    ("Fatiador de Legumes Profissional", "https://vt.tiktok.com/ZS9Do9Pkh87Q7-E9gtN/", "Cozinha", ["como escolher fatiador de legumes sem comprar por impulso", "como avaliar estabilidade e proteção das lâminas", "como organizar utensílios de corte com segurança", "fatiador multifuncional: quando vale a pena"]),
    ("Protetor Impermeável de Colchão Matelado", "https://vt.tiktok.com/ZS9Do9mSCxrBa-2o155/", "Cama, Mesa e Banho", ["protetor matelado: o que observar antes de comprar", "como escolher proteção para diferentes tamanhos de colchão", "impermeável e confortável: o que conferir no anúncio", "como criar uma rotina simples de proteção do colchão"]),
    ("Manta Cobertor de Microfibra", "https://vt.tiktok.com/ZS9Do9m3p5V9w-jllKj/", "Cama, Mesa e Banho", ["como escolher manta para sofá ou cama", "microfibra: o que observar em mantas e cobertores", "como usar mantas na decoração sem pesar o ambiente", "como guardar mantas de uso diário"]),
    ("Mini Climatizador de Ar Portátil", "https://vt.tiktok.com/ZS9DVaKJ1umxE-UHx9W/", "Sala", ["mini climatizador: o que conferir antes de comprar", "como melhorar o conforto térmico em ambientes pequenos", "climatizador portátil ou ventilador: o que considerar", "onde posicionar um climatizador compacto"]),
    ("Câmera Lâmpada Wi-Fi 1080p", "https://vt.tiktok.com/ZS9DVmeakMLJH-8DAf9/", "Área Externa", ["câmera lâmpada Wi-Fi: o que conferir antes de comprar", "como planejar pontos de monitoramento residencial", "o que verificar em conexão, energia e posicionamento", "câmera interna ou externa: como diferenciar a necessidade"]),
    ("Escova Elétrica de Limpeza 9 em 1", "https://vt.tiktok.com/ZS9DVmJW3UMxg-1X2J5/", "Limpeza e Utilidades", ["escova elétrica de limpeza: o que observar", "como escolher acessórios para limpeza de banheiro e cozinha", "como montar uma rotina de limpeza por zonas", "o que conferir em autonomia, encaixes e reposição"]),
    ("Mop Giratório 360", "https://vt.tiktok.com/ZS9DVmFYNCQMH-LghoN/", "Limpeza e Utilidades", ["mop giratório: o que observar antes de comprar", "como escolher mop para apartamento", "como organizar o armário de limpeza", "refil e centrifugação: o que conferir no anúncio"])
]

items = []
item_id = 1
for product, affiliate_link, category, topics in PRODUCTS:
    for topic in topics:
        items.append({
            "id": item_id,
            "topic": topic,
            "product": product,
            "affiliate_link": affiliate_link,
            "category": category,
            "status": "PENDING",
            "intent": "informational_commercial",
            "rules": {
                "unique_search_intent": True,
                "avoid_keyword_cannibalization": True,
                "affiliate_rel": "nofollow sponsored",
                "no_invented_product_specs": True,
                "no_fake_physical_testing": True
            }
        })
        item_id += 1

assert len(items) == 100, len(items)
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({
    "version": 1,
    "project": "Casa e Decoração",
    "total": 100,
    "policy": "100 pautas únicas; intenção distinta; link afiliado somente quando contextual; sem especificações inventadas",
    "items": items
}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Fila editorial criada: {OUT} | itens={len(items)}")
