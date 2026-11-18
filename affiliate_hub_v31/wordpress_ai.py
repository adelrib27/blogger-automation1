"""Workers AI compartilhado por WordPress (qualquer site registrado no V31).

Plan/CTA recebem JSON Schema; corpo recebe HTML sem inventar dados do
produto. O gate de qualidade específico do publicador continua obrigatório.
Nenhuma mutação WordPress/Blogger/Shopee/R2 aqui.
"""
from __future__ import annotations

import json
import re
import time
import urllib.request


DEFAULT_MODEL="@cf/meta/llama-3.3-70b-instruct-fp8-fast"

PLAN_SCHEMA={
    "type":"object",
    "properties":{
        "title":{"type":"string"},
        "keyword":{"type":"string"},
        "reader_need":{"type":"string"},
        "product_connection":{"type":"string"},
    },
    "required":["title","keyword","reader_need","product_connection"],
}
CTA_SCHEMA={
    "type":"object",
    "properties":{"lead":{"type":"string"}},
    "required":["lead"],
}
SCHEMA_BY_KIND={"plan":PLAN_SCHEMA,"cta":CTA_SCHEMA}


class WordPressAIError(ValueError):
    pass


def _to_text(value) -> str:
    if isinstance(value,str):
        return value.strip()
    if isinstance(value,dict):
        # JSON mode do Cloudflare pode retornar um objeto já parseado.
        if ("title" in value and "keyword" in value) or "lead" in value:
            return json.dumps(value,ensure_ascii=False)
        for key in ("response","text","content","output_text"):
            if key in value:
                r=_to_text(value[key])
                if r: return r
        if "message" in value:
            r=_to_text(value["message"])
            if r: return r
    if isinstance(value,list):
        for entry in value:
            r=_to_text(entry)
            if r: return r
    return ""


def extract_response(payload:dict) -> str:
    if not isinstance(payload,dict) or payload.get("success") is False:
        raise WordPressAIError("workers_ai_response_unsuccessful")
    result=payload.get("result")
    if isinstance(result,dict):
        for key in ("response","text","output_text"):
            data=_to_text(result.get(key))
            if data: return data
        for entry in result.get("choices") or []:
            result=_to_text(entry)
            if result:return result
    raise WordPressAIError("workers_ai_response_empty")


def build_payload(prompt:str,*,kind:str="html")->dict:
    if (not isinstance(prompt,str) or not 10<=len(prompt.strip())<=70000
        or kind not in ("plan","cta","html")):
        raise WordPressAIError("workers_ai_prompt_invalid")
    payload={
        "messages":[
            {"role":"system","content":(
                "Você escreve em português do Brasil. "
                "Nunca invente especificações, preço, disponibilidade, "
                "testes de produto, certificações ou benefícios não demonstrados. "
                "Siga estritamente o formato solicitado pelo usuário.")},
            {"role":"user","content":prompt.strip()},
        ],
        "max_tokens":8192,
        "temperature":0.2,
    }
    if kind in SCHEMA_BY_KIND:
        payload["response_format"]={
            "type":"json_schema",
            "json_schema":SCHEMA_BY_KIND[kind],
        }
    return payload


def request_workers_text(*,prompt:str,account_id:str,api_token:str,
                         model:str=DEFAULT_MODEL,kind:str="html",
                         retries:int=3)->str:
    if (not isinstance(account_id,str) or
        not re.fullmatch(r"[a-fA-F0-9]{32}",account_id) or
        not isinstance(api_token,str) or len(api_token.strip())<16):
        raise WordPressAIError("workers_ai_credentials_unavailable")
    if (not isinstance(model,str) or
        not re.fullmatch(r"@cf/[a-zA-Z0-9._/-]{6,110}",model)):
        raise WordPressAIError("workers_ai_model_invalid")
    if type(retries)is not int or not 1<=retries<=3:
        raise WordPressAIError("workers_ai_retries_invalid")
    data=json.dumps(build_payload(prompt,kind=kind),
        ensure_ascii=False).encode("utf-8")
    url=("https://api.cloudflare.com/client/v4/accounts/"+
         account_id+"/ai/run/"+model)
    last_error="workers_ai_unknown"
    for n in range(retries):
        request=urllib.request.Request(
            url,data=data,method="POST",headers={
                "Authorization":"Bearer "+api_token,
                "Content-Type":"application/json",
                "Accept":"application/json",
                "User-Agent":"V31-Universal-WordPress-Editorial/1.0",
            })
        try:
            with urllib.request.urlopen(request,timeout=140) as resp:
                payload=json.loads(resp.read().decode("utf-8","replace"))
            answer=extract_response(payload)
            if answer:
                return answer
            last_error="workers_ai_response_empty"
        except Exception as error:
            # Não imprimir o payload, request/headers ou token.
            last_error="workers_ai_request_"+type(error).__name__
        if n+1<retries:
            time.sleep(3*(n+1))
    raise WordPressAIError(last_error)
