#!/usr/bin/env python3
from __future__ import annotations


class PostsAsPages:
    """Adapta o recurso posts da Blogger API para scripts já validados contra pages."""

    def __init__(self, posts_resource):
        self._posts = posts_resource

    def get(self, *, blogId, pageId):
        return self._posts.get(blogId=blogId, postId=pageId)

    def update(self, *, blogId, pageId, body):
        return self._posts.update(blogId=blogId, postId=pageId, body=body)


class BloggerPostTargetProxy:
    def __init__(self, service):
        self._service = service

    def pages(self):
        return PostsAsPages(self._service.posts())

    def __getattr__(self, name):
        return getattr(self._service, name)
