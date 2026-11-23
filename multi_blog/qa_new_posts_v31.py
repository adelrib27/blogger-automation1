#!/usr/bin/env python3
"""SAFE, somente HTTP GET dos 26 posts; nenhuma escrita Blogger."""
import urllib.request,urllib.error,time,html,sys
BLOGS={
"pedal-leve-mobilidade-urbana":"bomba-de-ar-para-bicicleta-como",
"mala-pronta-viagem-pratica":"cadeado-de-mala-com-senha-o-que",
"atelie-criativo-em-casa":"base-de-corte-para-artesanato-medidas",
"jardim-e-horta-na-pratica":"regador-de-plantas-como-escolher-bico",
"achados-da-rotina":"suporte-dobravel-para-tablet-na-mesa",
"casa-leve-e-funcional":"cesto-organizador-dobravel-quando-ajuda",
"achadosparacasa2026":"clipes-adesivos-para-cabos-como",
"vida-pet-pratica":"tapete-coletor-de-areia-para-gatos",
"casa-pratica-lab-20261102":"potes-hermeticos-na-cozinha-como",
"eletroportateis-na-cozinha":"sanduicheira-eletrica-o-que-avaliar-em",
"cabelos-em-foco":"mascara-morte-subita-lola-450g-como",
"ventiladores-em-foco":"ventilador-mondial-vsp-40-b-checklist",
"air-fryers-em-foco":"air-fryer-elgin-quad-fry-42-l-como",
"limpeza-inteligente":"wap-robot-w90-em-casa-com-pets-tapetes",
"conectaachados":"hub-usb-c-para-notebook-como-conferir",
"estilo-no-dia-a-dia-0071220800-2":"bolsa-transversal-feminina-como-medir",
"casa-em-ordem-pratica":"colmeia-organizadora-de-gavetas-como",
"escolha-certa-online":"sapateira-desmontavel-compare-andares",
"achados-que-valem":"luminaria-led-recarregavel-quando-o",
"guia-de-achados-e-ofertas":"balanca-digital-de-cozinha-como",
"vitrine-pratica":"cabide-de-porta-com-ganchos-quando",
"moda-ofertas":"bolsa-sacola-feminina-grande-como",
"canal-attitude":"escova-facial-de-silicone-como-avaliar",
"portalradartechbr":"teclado-e-mouse-bluetooth-cuidados-de",
"cozinha-sem-complicacao":"tabua-de-corte-de-aco-inox-cuidados",
"liquidificadores-em-foco":"acoplamento-do-liquidificador-philips"
}
def scan(domain,slug):
 url=f"https://{domain}.blogspot.com/2026/11/{slug}.html"
 for attempt in range(1,9):
  try:
   req=urllib.request.Request(url+f"?v31_safe_audit={attempt}",headers={"User-Agent":"Mozilla/5.0"})
   with urllib.request.urlopen(req,timeout=23) as resp:
    status=resp.status
    text=resp.read().decode("utf-8","replace")
   if status!=200:raise RuntimeError("HTTP_NON_200")
   checks={
    "affiliate":'s.shopee.com.br/' in text,
    "sponsored":'nofollow sponsored noopener' in text,
    "disclosure":'Transparência:' in text or 'Transparência' in text,
    "post_identity":slug.split("-")[0] in text.lower(),
   }
   if not all(checks.values()):raise RuntimeError("CONTENT_GUARD:"+str(checks))
   print("PUBLIC_POST_PASS",domain,slug,flush=True)
   return
  except (urllib.error.HTTPError,urllib.error.URLError,TimeoutError) as e:
   print("PUBLIC_POST_HTTP_RETRY",domain,attempt,type(e).__name__,getattr(e,"code",""),flush=True)
   if attempt<8:time.sleep(6)
  except RuntimeError as e:
   raise SystemExit(f"FAIL_CLOSED:{domain}:{e}")
 raise SystemExit("FAIL_CLOSED_PUBLIC_UNAVAILABLE:"+domain)
def main():
 for domain,slug in BLOGS.items():scan(domain,slug)
 print("ALL_26_PUBLIC_POSTS_PASS",flush=True)
if __name__=="__main__":main()
