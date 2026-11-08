#!/usr/bin/env python3
"""Validação de envio no formulário próprio do Pedal Leve; envio de teste único.
Não contorna CAPTCHA e não afirma recebimento em Gmail.
"""
import asyncio, json, urllib.parse
from playwright.async_api import async_playwright

CONTACT="https://pedal-leve-mobilidade-urbana.blogspot.com/p/contato.html"
THANKS="https://pedal-leve-mobilidade-urbana.blogspot.com/p/mensagem-enviada.html"
MARKER="PEDAL_V31_FORM_E2E_20261108_0725"

async def main():
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True,args=["--no-sandbox"])
        page=await browser.new_page(locale="pt-BR")
        success=False
        for i in range(7):
            try:
                resp=await page.goto(CONTACT+"?safe_form_test="+str(i),wait_until="domcontentloaded",timeout=25000)
                if resp and resp.status==200: success=True;break
                print("CONTACT_HTTP_RETRY",i+1,resp.status if resp else None,flush=True)
            except Exception as e:
                print("CONTACT_HTTP_RETRY",i+1,type(e).__name__,flush=True)
            await asyncio.sleep(6)
        if not success: raise RuntimeError("CONTACT_PUBLIC_HTTP_NOT_200")
        form=page.locator("form.pedal-contact-form")
        if await form.count()!=1: raise RuntimeError("CONTACT_FORM_MISSING")
        action=await form.get_attribute("action")
        parsed=urllib.parse.urlparse(action or "")
        if parsed.scheme!="https" or parsed.netloc!="formsubmit.co" or not parsed.path.startswith("/"):
            raise RuntimeError("CONTACT_ACTION_NOT_EXPECTED")
        destination=urllib.parse.unquote(parsed.path.strip("/"))
        if "@" not in destination: raise RuntimeError("CONTACT_DESTINATION_MISSING")
        if await form.locator('input[name="_next"]').get_attribute("value")!=THANKS:
            raise RuntimeError("CONTACT_RETURN_URL_MISMATCH")
        await form.locator('input[name="name"]').fill("Teste tecnico de formulario")
        await form.locator('input[name="email"]').fill(destination)
        await form.locator('textarea[name="message"]').fill(MARKER+" - Validacao automatica de um envio do blog; nao responder.")
        # Um clique: não repetir/envios duplicados em falha de rede.
        await form.locator('button[type="submit"]').click(timeout=30000)
        await page.wait_for_timeout(7500)
        target=page.url
        print("PEDAL_CONTACT_SEND_ATTEMPTED_ONE_TIME",flush=True)
        print("PEDAL_CONTACT_RESULT",json.dumps({
            "returned_to_own_page":target.startswith(THANKS),
            "redirect_host":urllib.parse.urlparse(target).hostname,
            "captcha_or_activation_possible":("formsubmit.co" in target),
            "marker":MARKER,
        },ensure_ascii=False),flush=True)
        await browser.close()
        if not target.startswith(THANKS):
            raise RuntimeError("CONTACT_E2E_NOT_CONFIRMED: retorno nao ocorreu; nao contornar protecoes")
        print("PEDAL_CONTACT_REDIRECT_PASS_RECEIPT_NOT_PROVEN",flush=True)

if __name__=="__main__":
    asyncio.run(main())
