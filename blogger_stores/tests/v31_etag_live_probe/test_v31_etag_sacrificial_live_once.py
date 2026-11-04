import importlib.util
from unittest.mock import patch
import os
import unittest
from pathlib import Path

file=Path(__file__).with_name('v31_etag_sacrificial_live_once.py')
spec=importlib.util.spec_from_file_location('v31_live_once',file)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class LiveProbeGuardTest(unittest.TestCase):
    def setUp(self):
        self.env=patch.dict(os.environ,{
            'GITHUB_REPOSITORY':m.REPO,'GITHUB_REF':m.BRANCH,
            'GITHUB_EVENT_NAME':'push','GITHUB_RUN_ATTEMPT':'1',
            'V31_SACRIFICIAL_PROBE_ONLY':'YES_SINGLE_PAGE_SINGLE_PUT'
        });self.env.start();self.addCleanup(self.env.stop)

    def test_wrong_branch_fails_before_oauth(self):
        with patch.dict(os.environ,{'GITHUB_REF':'refs/heads/main'}),patch.object(m,'oauth_access_token',side_effect=AssertionError('should not refresh')):
            with self.assertRaises(m.FailClosed):m.run()

    def test_rerun_fails_before_oauth(self):
        with patch.dict(os.environ,{'GITHUB_RUN_ATTEMPT':'2'}),patch.object(m,'oauth_access_token',side_effect=AssertionError('should not refresh')):
            with self.assertRaises(m.FailClosed):m.run()

    def test_created_page_id_must_not_be_loja(self):
        calls=[]
        def fake(url,method,*,token=None,obj=None,headers=None):
            calls.append(method)
            if method=='POST':return 201,{'id':m.LAB_LOJA_PAGE if hasattr(m,'LAB_LOJA_PAGE') else '2446067640331732447'}
            raise AssertionError('must not attempt PUT')
        with patch.object(m,'oauth_access_token',return_value='token'),patch.object(m,'list_pages',side_effect=[[{'id':i} for i in m.EXPECTED_LIVE],[]]),patch.object(m,'transport',side_effect=fake):
            with self.assertRaises(m.FailClosed):m.run()
        self.assertEqual(calls,['POST'])

    def test_success_412_one_conditional_put_and_authenticated_get(self):
        calls=[]
        page={'id':'987654321987654321','blog':{'id':m.BLOG},'title':m.TITLE,
              'url':'https://blog-teste-tema-worpress.blogspot.com/p/v31-sacrificial.html',
              'content':m.HTML,'etag':'"valid-strong-etag"','updated':'2026-11-04T20:00:00-03:00','status':'LIVE'}
        def fake(url,method,*,token=None,obj=None,headers=None):
            calls.append((method,headers))
            if method=='POST':return 201,{'id':page['id']}
            if method=='GET':return 200,page.copy()
            if method=='PUT':
                self.assertEqual(headers['If-Match'],'"V31-SACRIFICIAL-STALE-20261104-DO-NOT-ACCEPT"')
                return 412,{}
            raise AssertionError(method)
        with patch.object(m,'oauth_access_token',return_value='token'),patch.object(m,'list_pages',side_effect=[[{'id':i} for i in m.EXPECTED_LIVE],[]]),patch.object(m,'transport',side_effect=fake):
            m.run()
        self.assertEqual([x[0] for x in calls],['POST','GET','PUT','GET'])

    def test_response_200_blocks_even_if_same_html(self):
        page={'id':'987654321987654321','blog':{'id':m.BLOG},'title':m.TITLE,
              'url':'https://blog-teste-tema-worpress.blogspot.com/p/v31-sacrificial.html',
              'content':m.HTML,'etag':'"valid-strong-etag"','updated':'2026-11-04T20:00:00-03:00','status':'LIVE'}
        verbs=[]
        def fake(url,method,*,token=None,obj=None,headers=None):
            verbs.append(method)
            return (201,{'id':page['id']}) if method=='POST' else (200,page.copy() if method=='GET' else {})
        with patch.object(m,'oauth_access_token',return_value='token'),patch.object(m,'list_pages',side_effect=[[{'id':i} for i in m.EXPECTED_LIVE],[]]),patch.object(m,'transport',side_effect=fake):
            with self.assertRaises(m.FailClosed):m.run()
        self.assertEqual(verbs,['POST','GET','PUT','GET'])

if __name__=='__main__':unittest.main()
