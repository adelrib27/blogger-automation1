import os,sys,unittest
from pathlib import Path
from unittest.mock import patch
from urllib import error
import io
import json
sys.path.insert(0,str(Path(__file__).resolve().parents[1] / 'src'))
from v31_lab_second_authorized_publish_once import OneBloggerService, Stop,APPROVAL,validate_launch_env, BLOG,PAGE

class TestAuthorizedTransport(unittest.TestCase):
    def setUp(self):
        self.s=OneBloggerService('t'*35)
    def test_different_page_put_blocked(self):
        with self.assertRaises(Stop):self.s.update(blogId=BLOG,pageId='12345',body={'title':'LOJA','content':'x'})
    def test_different_blog_put_blocked(self):
        with self.assertRaises(Stop):self.s.update(blogId='12345',pageId=PAGE,body={'title':'LOJA','content':'x'})
    def test_unapproved_html_put_blocked(self):
        with self.assertRaises(Stop):self.s.update(blogId=BLOG,pageId=PAGE,body={'title':'LOJA','content':'bad'})
    def test_second_attempt_forbidden(self):
        self.s.put_count=1
        with self.assertRaises(Stop):self.s.update(blogId=BLOG,pageId=PAGE,body={'title':'LOJA','content':'bad'})
    def test_get_must_target_lab(self):
        with self.assertRaises(Stop):self.s.get(blogId=BLOG,pageId='1')
    def test_missing_if_match_blocks_before_network(self):
        q=self.s.get(blogId=BLOG,pageId=PAGE)
        q.method='PUT'
        with self.assertRaises(Stop):q.execute()
        self.assertEqual(self.s.put_count,1)
    def test_conditional_put_http_payload_once(self):
        # Pure HTTP transport mock; no Blogger or Git changes.
        q=self.s.get(blogId=BLOG,pageId=PAGE)
        q.method='PUT'
        q.data={'kind':'blogger#page','id':PAGE,'blog':{'id':BLOG},
                'title':'LOJA','content':'mock-test-only'}
        q.headers['If-Match']='"strong-1"'
        class Response:
            status=200
            def __enter__(self):return self
            def __exit__(self,*args):return False
            def read(self,n):return b'{"id":"'+PAGE.encode()+b'"}'
        def mocked(r,timeout):
            self.assertEqual(r.full_url,'https://www.googleapis.com/blogger/v3/blogs/'+BLOG+'/pages/'+PAGE)
            self.assertEqual(r.get_method(),'PUT')
            self.assertEqual(r.get_header('If-match'),'"strong-1"')
            obj=json.loads(r.data)
            self.assertEqual(obj['id'],PAGE)
            self.assertEqual(obj['blog']['id'],BLOG)
            return Response()
        with patch('v31_lab_second_authorized_publish_once.request.urlopen',side_effect=mocked) as u:
            self.assertEqual(q.execute()['id'],PAGE)
        self.assertEqual(self.s.put_count,1)
        with self.assertRaises(Stop):q.execute()
        self.assertEqual(u.call_count,1)
    def test_http_412_is_terminal(self):
        q=self.s.get(blogId=BLOG,pageId=PAGE)
        q.method='PUT';q.data={'kind':'blogger#page'};q.headers['If-Match']='"stale"'
        with patch('v31_lab_second_authorized_publish_once.request.urlopen',
                    side_effect=error.HTTPError('https://www.googleapis.com/',412,'Precondition Failed',{},None)) as u:
            with self.assertRaises(Stop):q.execute()
            with self.assertRaises(Stop):q.execute()
            self.assertEqual(u.call_count,1)
        self.assertEqual(self.s.put_count,1)
    def test_timeout_is_terminal(self):
        q=self.s.get(blogId=BLOG,pageId=PAGE)
        q.method='PUT';q.data={'kind':'blogger#page'};q.headers['If-Match']='"strong"'
        with patch('v31_lab_second_authorized_publish_once.request.urlopen',side_effect=TimeoutError()) as u:
            with self.assertRaises(Stop):q.execute()
            with self.assertRaises(Stop):q.execute()
            self.assertEqual(u.call_count,1)
    def test_rerun_not_authorized(self):
        with patch.dict(os.environ, {'GITHUB_REPOSITORY':'adelrib27/blogger-automation1',
              'GITHUB_REF':'refs/heads/lab/v31r1-shopee-safe-20261103',
              'GITHUB_EVENT_NAME':'push','GITHUB_RUN_ATTEMPT':'2',
              'V31_LAB_ONCE_APPROVAL':APPROVAL},clear=True):
            with self.assertRaises(Stop):validate_launch_env()
    def test_approval_flag_missing_blocks(self):
        with patch.dict(os.environ, {'GITHUB_REPOSITORY':'adelrib27/blogger-automation1',
              'GITHUB_REF':'refs/heads/lab/v31r1-shopee-safe-20261103',
              'GITHUB_EVENT_NAME':'push','GITHUB_RUN_ATTEMPT':'1'},clear=True):
            with self.assertRaises(Stop):validate_launch_env()
if __name__=='__main__':unittest.main()
