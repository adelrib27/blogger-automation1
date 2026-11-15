"""Offline simulation of Blogger listbox state. No browser, network, or Blogger writes."""
from __future__ import annotations
import unittest
import browser_provision as bp

class FakeOption:
    def __init__(self, page, label):
        self.page=page
        self.label=label
    def is_visible(self):
        return self.page.expanded and self.page.hydration_ticks<=0
    def inner_text(self):
        return self.label
    def evaluate(self, script):
        self.page.new_blog_activated=True

class FakeOptions:
    def __init__(self, page):self.page=page
    def count(self):return len(self.page.labels)
    def nth(self,i):return FakeOption(self.page,self.page.labels[i])

class FakeListbox:
    def __init__(self, page):self.page=page
    def count(self):return 1
    @property
    def first(self):return self
    def is_visible(self):return True
    def click(self,timeout=0):
        self.page.clicks+=1
        self.page.expanded=not self.page.expanded
        if self.page.fail_click_after_effect:raise RuntimeError('timeout after dispatch')
    def get_attribute(self,key):
        if key!='aria-expanded':return None
        if self.page.unreadable:raise RuntimeError('unreadable expanded state')
        if self.page.no_aria:return None
        return 'true' if self.page.expanded else 'false'

class FakeKeyboard:
    def __init__(self,page):self.page=page
    def press(self,key):
        if key=='Escape':self.page.expanded=False

class FakePage:
    def __init__(self,expanded=False,hydration_ticks=0,labels=None):
        self.expanded=expanded
        self.hydration_ticks=hydration_ticks
        self.labels=['Novo blog...', 'Blog Antigo'] if labels is None else labels
        self.clicks=0
        self.new_blog_activated=False
        self.fail_click_after_effect=False
        self.unreadable=False
        self.no_aria=False
        self.keyboard=FakeKeyboard(self)
        self.ticks=0
    def get_by_role(self,role,**kwargs):
        if role=='option':return FakeOptions(self)
        if role=='listbox':return FakeListbox(self)
        raise AssertionError('unexpected role '+role)
    def wait_for_timeout(self,ms):
        self.ticks+=1
        if self.hydration_ticks>0:self.hydration_ticks-=1

class SelectorGuardTests(unittest.TestCase):
    def test_already_open_never_toggles_menu(self):
        p=FakePage(expanded=True)
        bp.open_blog_switcher(p)
        self.assertTrue(p.expanded)
        self.assertEqual(p.clicks,0)
    def test_collapsed_opens_once(self):
        p=FakePage(expanded=False)
        bp.open_blog_switcher(p)
        self.assertTrue(p.expanded)
        self.assertEqual(p.clicks,1)
    def test_expanded_hydrating_waits_without_toggle(self):
        p=FakePage(expanded=True,hydration_ticks=5)
        bp.open_blog_switcher(p)
        self.assertEqual(p.clicks,0)
        self.assertTrue(p.expanded)
        self.assertGreaterEqual(p.ticks,5)
    def test_expanded_without_target_fails_without_toggle(self):
        p=FakePage(expanded=True,labels=['Outro blog'])
        with self.assertRaises(bp.SafeAutomationError):bp.open_blog_switcher(p)
        self.assertEqual(p.clicks,0)
        self.assertFalse(p.new_blog_activated)
    def test_collapsed_without_target_fails_after_one_click(self):
        p=FakePage(expanded=False,labels=['Outro blog'])
        with self.assertRaises(bp.SafeAutomationError):bp.open_blog_switcher(p)
        self.assertEqual(p.clicks,1)
        self.assertFalse(p.new_blog_activated)
    def test_ambiguous_click_exception_never_triggers_second_click(self):
        p=FakePage(expanded=False,labels=['Outro blog'])
        p.fail_click_after_effect=True
        with self.assertRaises(bp.SafeAutomationError):bp.open_blog_switcher(p)
        self.assertEqual(p.clicks,1)
    def test_click_exception_after_menu_visible_is_accepted(self):
        p=FakePage(expanded=False)
        p.fail_click_after_effect=True
        bp.open_blog_switcher(p)
        self.assertEqual(p.clicks,1)
        self.assertTrue(p.expanded)
    def test_readonly_preflight_closes_menu_after_confirm(self):
        p=FakePage(expanded=True)
        self.assertTrue(bp.ensure_new_blog_available(p))
        self.assertFalse(p.expanded)
        self.assertEqual(p.clicks,0)
        self.assertFalse(p.new_blog_activated)
    def test_unreadable_expansion_blocks_before_click(self):
        p=FakePage(expanded=False,labels=['Outro blog'])
        p.unreadable=True
        with self.assertRaises(bp.SafeAutomationError):bp.open_blog_switcher(p)
        self.assertEqual(p.clicks,0)
    def test_no_aria_attribute_keeps_safe_single_click(self):
        p=FakePage(expanded=False)
        p.no_aria=True
        bp.open_blog_switcher(p)
        self.assertEqual(p.clicks,1)

if __name__=='__main__':unittest.main()
