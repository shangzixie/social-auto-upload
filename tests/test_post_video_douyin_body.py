import sys
import types
import unittest
from unittest.mock import patch


if "loguru" not in sys.modules:
    loguru_mod = types.ModuleType("loguru")

    class _DummyLogger:
        def add(self, *args, **kwargs):
            return 1

        def remove(self, *args, **kwargs):
            return None

        def bind(self, **kwargs):
            return self

        def __getattr__(self, _name):
            def _noop(*args, **kwargs):
                return None

            return _noop

    loguru_mod.logger = _DummyLogger()
    sys.modules["loguru"] = loguru_mod

if "playwright" not in sys.modules:
    sys.modules["playwright"] = types.ModuleType("playwright")
if "playwright.async_api" not in sys.modules:
    async_api = types.ModuleType("playwright.async_api")
    async_api.Playwright = object
    async_api.Page = object

    async def _async_playwright_stub():
        raise RuntimeError("playwright is not available in test environment")

    async_api.async_playwright = _async_playwright_stub
    sys.modules["playwright.async_api"] = async_api

from myUtils import postVideo


class PostVideoDouyinBodyTests(unittest.TestCase):
    def test_post_video_douyin_passes_body_to_image_uploader(self):
        captured = {}

        class FakeDouyinImage:
            def __init__(self, title, file_paths, tags, publish_date, account_file, body="", visibility="public", music_mode="none", music_keyword=""):
                captured["body"] = body
                captured["visibility"] = visibility

            async def main(self):
                return None

        with patch.object(postVideo, "DouYinImage", FakeDouyinImage), patch.object(postVideo.asyncio, "run", lambda coro, debug=False: coro.close()):
            postVideo.post_video_DouYin(
                title="标题",
                files=["1.jpg"],
                tags=["旅行"],
                account_file=["douyin.json"],
                content_type="image",
                body="这里是抖音图文正文",
                visibility="private",
            )

        self.assertEqual(captured.get("body"), "这里是抖音图文正文")
        self.assertEqual(captured.get("visibility"), "private")

    def test_post_video_douyin_passes_friends_visibility(self):
        captured = {}

        class FakeDouyinImage:
            def __init__(self, title, file_paths, tags, publish_date, account_file, body="", visibility="public", music_mode="none", music_keyword=""):
                captured["visibility"] = visibility

            async def main(self):
                return None

        with patch.object(postVideo, "DouYinImage", FakeDouyinImage), patch.object(postVideo.asyncio, "run", lambda coro, debug=False: coro.close()):
            postVideo.post_video_DouYin(
                title="标题",
                files=["1.jpg"],
                tags=["旅行"],
                account_file=["douyin.json"],
                content_type="image",
                visibility="friends",
            )

        self.assertEqual(captured.get("visibility"), "friends")

    def test_post_video_douyin_passes_music_options_for_image(self):
        captured = {}

        class FakeDouyinImage:
            def __init__(
                self,
                title,
                file_paths,
                tags,
                publish_date,
                account_file,
                body="",
                visibility="public",
                music_mode="none",
                music_keyword="",
            ):
                captured["music_mode"] = music_mode
                captured["music_keyword"] = music_keyword

            async def main(self):
                return None

        with patch.object(postVideo, "DouYinImage", FakeDouyinImage), patch.object(postVideo.asyncio, "run", lambda coro, debug=False: coro.close()):
            postVideo.post_video_DouYin(
                title="标题",
                files=["1.jpg"],
                tags=["旅行"],
                account_file=["douyin.json"],
                content_type="image",
                music_mode="keyword",
                music_keyword="山河故人",
            )

        self.assertEqual(captured.get("music_mode"), "keyword")
        self.assertEqual(captured.get("music_keyword"), "山河故人")


if __name__ == "__main__":
    unittest.main()
