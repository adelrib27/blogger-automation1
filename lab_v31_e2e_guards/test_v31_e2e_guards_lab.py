"""LAB isolated regression tests: no real Browser, network or Blogger writes."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import browser_provision as bp
import provision_new_blog_v31 as prov

class Page:
    def __init__(self, url, visibility='hidden'):
        self.url=url
        self.visibility=visibility
    def evaluate(self, js):
        assert js=='() => document.visibilityState'
        return self.visibility

class Context:
    def __init__(self, pages):
        self.pages=pages
        self.new_page_called=False
    def new_page(self):
        self.new_page_called=True
        return Page('about:blank')

class V31E2EGuardsTests(unittest.TestCase):
    def test_selection_prefers_visible_blogger_tab(self):
        stale=Page('https://draft.blogger.com/blog/posts/100', 'hidden')
        active=Page('https://draft.blogger.com/blog/posts/200', 'visible')
        self.assertIs(bp.select_page(Context([stale, active])), active)

    def test_selection_ignores_lookalike_domain(self):
        fake=Page('https://blogger.com.attacker.example/blog/posts/100','visible')
        valid=Page('https://draft.blogger.com/blog/posts/200', 'hidden')
        self.assertIs(bp.select_page(Context([fake,valid])),valid)

    def test_selection_empty_context_creates_single_page(self):
        ctx=Context([])
        self.assertEqual(bp.select_page(ctx).url, 'about:blank')
        self.assertTrue(ctx.new_page_called)

    def _run_provision(self, create):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            with (patch.object(prov,'ROOT',root),
                  patch.object(prov,'_page_manifest',return_value=[]),
                  patch.object(prov.settings,'_validate_inputs',return_value=None),
                  patch.object(prov.settings,'execute_configure_settings',return_value={'status':'SETTINGS_PROFILE_VALIDATED'}),
                  patch.object(prov.adopter.renderer,'strict_target',return_value=None),
                  patch.object(prov.adopter,'execute_adoption',return_value={'status':'V31_R52_APPLIED_AND_PUBLICLY_VALIDATED'}),
                  patch.object(bp,'execute_create',side_effect=create)):
                try:
                    result=prov.execute_provision('LAB V31','lab-v31-exato', 'Descrição laboratório','Descrição SEO laboratório',confirm=prov.CONFIRM)
                    error=None
                except prov.ProvisionV31Error as e:
                    result=None
                    error=e
                cp=root/'logs'/'provisioning'/'v31'/'lab-v31-exato.json'
                state=json.loads(cp.read_text(encoding='utf8'))
                return result,error,state

    def test_provision_never_attempts_alternative_address(self):
        calls=[]
        def create(title,address,**kwargs):
            calls.append(address)
            raise bp.SafeAutomationError('Endereço indisponível. Nenhum clique em SALVAR foi executado.')
        result,error,state=self._run_provision(create)
        self.assertIsNone(result)
        self.assertIsNotNone(error)
        self.assertEqual(calls,['lab-v31-exato'])
        self.assertEqual(state['status'],'PROVISION_V31_PARTIAL_STOP')
        self.assertFalse(state['created'])

    def test_provision_exact_slug_success_offline(self):
        calls=[]
        def create(title,address,**kwargs):
            calls.append(address)
            return {'blog_id':'321321321','expected_url':f'https://{address}.blogspot.com/'}
        result,error,state=self._run_provision(create)
        self.assertIsNone(error)
        self.assertEqual(calls,['lab-v31-exato'])
        self.assertEqual(state['status'],'V31_THEME_VALIDATED_AWAIT_PAGES')
        self.assertTrue(state['created'])
        self.assertTrue(state['settings_validated'])
        self.assertEqual(result['status'],'BLOGGER_NEW_BLOG_V31_CORE_PROVISIONED')
        self.assertEqual(result['publication_status'],'NOT_PUBLISHED')

if __name__=='__main__':
    unittest.main()
