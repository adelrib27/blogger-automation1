#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

MARKER_OLD = "emporio-revisao-visual-09-wide-footer"
MARKER_NEW = "emporio-revisao-visual-10-square-contact"

CSS = r'''
/* V10 — HOME square cards + native Blogger ContactForm on /p/contato.html */

/* HOME: mantém a largura dos 3 cards e aumenta a imagem para 1:1. */
body.feed-view:not(.item-view) #Blog1 .post-wrapper.not-hero .snippet-thumbnail-container,
body.feed-view:not(.item-view) #Blog1 .post-wrapper.not-hero .snippet-thumbnail{
  aspect-ratio:1 / 1!important;
  height:auto!important;
  min-height:0!important;
  max-height:none!important;
  overflow:hidden!important;
  width:100%!important;
}
body.feed-view:not(.item-view) #Blog1 .post-wrapper.not-hero .snippet-thumbnail{
  background-position:center center!important;
  background-repeat:no-repeat!important;
  background-size:cover!important;
}

/* O gadget nativo fica invisível fora da página Contato. */
#ContactForm1,
.ga-contact-native{display:none!important}

body.ga-contact-page #comments{display:none!important}
body.ga-contact-page #ga-contact-form-slot{margin:28px 0 24px!important}
body.ga-contact-page #ga-contact-form-slot #ContactForm1{
  background:#f8fbff!important;
  border:1px solid #dce4ee!important;
  border-radius:16px!important;
  box-sizing:border-box!important;
  display:block!important;
  margin:0!important;
  max-width:680px!important;
  padding:22px!important;
  width:100%!important;
}
body.ga-contact-page #ga-contact-form-slot #ContactForm1>.title,
body.ga-contact-page #ga-contact-form-slot #ContactForm1 h2,
body.ga-contact-page #ga-contact-form-slot #ContactForm1 h3.title{display:none!important}
body.ga-contact-page #ga-contact-form-slot .contact-form-widget,
body.ga-contact-page #ga-contact-form-slot .contact-form-widget form{
  display:block!important;margin:0!important;max-width:none!important;width:100%!important
}
body.ga-contact-page #ga-contact-form-slot .contact-form-name,
body.ga-contact-page #ga-contact-form-slot .contact-form-email,
body.ga-contact-page #ga-contact-form-slot .contact-form-email-message{
  background:#fff!important;
  border:1px solid #cfd9e5!important;
  border-radius:10px!important;
  box-sizing:border-box!important;
  color:#172033!important;
  display:block!important;
  font:400 15px/1.45 Ubuntu,Arial,sans-serif!important;
  margin:6px 0 16px!important;
  max-width:none!important;
  outline:none!important;
  padding:12px 13px!important;
  width:100%!important;
}
body.ga-contact-page #ga-contact-form-slot .contact-form-email-message{min-height:170px!important;resize:vertical!important}
body.ga-contact-page #ga-contact-form-slot .contact-form-name:focus,
body.ga-contact-page #ga-contact-form-slot .contact-form-email:focus,
body.ga-contact-page #ga-contact-form-slot .contact-form-email-message:focus{
  border-color:#175cd3!important;box-shadow:0 0 0 3px rgba(23,92,211,.10)!important
}
body.ga-contact-page #ga-contact-form-slot .contact-form-button-submit{
  background:#175cd3!important;
  background-image:none!important;
  border:0!important;
  border-radius:10px!important;
  box-shadow:0 8px 20px rgba(23,92,211,.16)!important;
  color:#fff!important;
  cursor:pointer!important;
  font:800 14px/1 Ubuntu,Arial,sans-serif!important;
  height:auto!important;
  margin:4px 0 0!important;
  max-width:none!important;
  padding:13px 18px!important;
  width:auto!important;
}
body.ga-contact-page #ga-contact-form-slot .contact-form-button-submit:hover{background:#0f46a3!important}
body.ga-contact-page #ga-contact-form-slot .contact-form-error-message,
body.ga-contact-page #ga-contact-form-slot .contact-form-success-message{
  display:block!important;font:700 13px/1.45 Ubuntu,Arial,sans-serif!important;margin:12px 0 0!important;max-width:none!important;text-align:left!important;width:100%!important
}
body.ga-contact-page #ga-contact-form-slot .contact-form-error-message{color:#b42318!important}
body.ga-contact-page #ga-contact-form-slot .contact-form-success-message{color:#15803d!important}
@media screen and (max-width:700px){
  body.ga-contact-page #ga-contact-form-slot #ContactForm1{border-radius:12px!important;padding:16px!important}
}
'''

JS = r'''
<script type='text/javascript'>
//<![CDATA[
(function(){
  if(location.pathname!=='/p/contato.html') return;
  document.body.classList.add('ga-contact-page');

  function mount(){
    var slot=document.getElementById('ga-contact-form-slot');
    var widget=document.getElementById('ContactForm1');
    if(!slot || !widget) return false;
    if(widget.parentElement!==slot) slot.appendChild(widget);
    widget.style.setProperty('display','block','important');
    widget.classList.add('ga-contact-live');
    return true;
  }

  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',mount,{once:true});
  else mount();
  setTimeout(mount,250);setTimeout(mount,900);setTimeout(mount,1800);
  var until=Date.now()+5000;
  var ob=new MutationObserver(function(){if(mount()||Date.now()>until)ob.disconnect();});
  ob.observe(document.documentElement,{childList:true,subtree:true});
  setTimeout(function(){ob.disconnect();mount();},5200);
})();
//]]>
</script>
'''

CONTACT_SECTION = r'''
<b:section class='ga-contact-native' id='ga_contact_native' maxwidgets='1' name='Contato nativo' showaddelement='no'>
  <b:widget id='ContactForm1' locked='true' title='Contato' type='ContactForm' version='2' visible='true'/>
</b:section>
'''


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def ensure_contact_widget(text: str) -> tuple[str, bool]:
    # Reaproveita ContactForm1 antigo se existir; caso contrário adiciona o gadget nativo.
    m = re.search(r"<b:widget\b[^>]*\bid=(['\"])ContactForm1\1[^>]*>", text, flags=re.I)
    if m:
        tag = m.group(0)
        if re.search(r"\bvisible=(['\"]).*?\1", tag, flags=re.I):
            tag2 = re.sub(r"\bvisible=(['\"]).*?\1", "visible='true'", tag, count=1, flags=re.I)
        elif tag.endswith('/>'):
            tag2 = tag[:-2] + " visible='true'/>"
        else:
            tag2 = tag[:-1] + " visible='true'>"
        return text[:m.start()] + tag2 + text[m.end():], False

    if '</body>' not in text:
        raise SystemExit('Elemento </body> não encontrado para inserir ContactForm1.')
    return text.replace('</body>', CONTACT_SECTION + '\n</body>', 1), True


def main() -> int:
    p=argparse.ArgumentParser(description='V10: miniaturas quadradas na home + formulário nativo em Contato.')
    p.add_argument('--theme-path',required=True)
    args=p.parse_args()
    path=Path(args.theme_path).resolve()
    if not path.exists() or path.name.lower()!='theme.xml':
        raise SystemExit('theme.xml não encontrado no caminho informado.')

    text=path.read_text(encoding='utf-8')
    if MARKER_NEW in text:
        ET.parse(path)
        print(json.dumps({'status':'THEME_REVISION_10_ALREADY_BUILT','path':str(path),'size_bytes':path.stat().st_size,'sha256':sha256(path),'xml_valid':True,'public_marker':MARKER_NEW},ensure_ascii=False,indent=2))
        return 0
    if MARKER_OLD not in text:
        raise SystemExit(f'A V9 validada não foi localizada. Marcador ausente: {MARKER_OLD}')

    text=text.replace(MARKER_OLD,MARKER_NEW)
    marker='/* Mobile */'
    if marker not in text: raise SystemExit('Marcador CSS Mobile não encontrado.')
    text=text.replace(marker,CSS+'\n'+marker,1)
    text,inserted=ensure_contact_widget(text)
    if '</body>' not in text: raise SystemExit('Elemento </body> não encontrado para inserir script.')
    text=text.replace('</body>',JS+'\n</body>',1)

    path.write_text(text,encoding='utf-8')
    ET.parse(path)
    print(json.dumps({
      'status':'THEME_REVISION_10_SQUARE_CONTACT_BUILT','path':str(path),'size_bytes':path.stat().st_size,'sha256':sha256(path),'xml_valid':True,
      'public_marker':MARKER_NEW,'home_card_aspect_ratio':'1:1','featured_post_changed':False,'post_item_view_changed':False,
      'contact_form_native_blogger':True,'contact_widget_inserted':inserted,'contact_comments_hidden':True,'header_changed':False,'footer_changed':False
    },ensure_ascii=False,indent=2))
    return 0

if __name__=='__main__':
    raise SystemExit(main())
