class _PostPages:
    def __init__(self, posts):
        self.posts = posts
    def get(self, *, blogId, pageId):
        return self.posts.get(blogId=blogId, postId=pageId)
    def update(self, *, blogId, pageId, body):
        return self.posts.update(blogId=blogId, postId=pageId, body=body)

class BloggerPostTargetProxy:
    def __init__(self, service):
        self.service = service
    def pages(self):
        return _PostPages(self.service.posts())
    def posts(self):
        return self.service.posts()
