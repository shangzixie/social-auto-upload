import sys
import types
import unittest


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

from uploader.xiaohongshu_uploader.main import XiaoHongShuImage


class XhsImageNoteContentTests(unittest.TestCase):
    def test_build_note_content_includes_body_and_tags(self):
        text = XiaoHongShuImage.build_note_content("正文第一行", ["旅行", "摄影"])
        self.assertEqual(text, "正文第一行\n#旅行 #摄影")


if __name__ == "__main__":
    unittest.main()
