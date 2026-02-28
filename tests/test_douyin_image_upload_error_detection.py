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

from uploader.douyin_uploader.main import DouYinImage


class FakeLocator:
    def __init__(self, selector, visibility_map):
        self.selector = selector
        self.visibility_map = visibility_map

    @property
    def first(self):
        return self

    async def count(self):
        return 1 if self.selector in self.visibility_map else 0

    async def is_visible(self):
        return self.visibility_map.get(self.selector, False)


class FakePage:
    def __init__(self, visibility_map, url):
        self.visibility_map = visibility_map
        self.url = url

    def locator(self, selector):
        return FakeLocator(selector, self.visibility_map)


class DelayedUploadLocator:
    def __init__(self, page, selector):
        self.page = page
        self.selector = selector

    @property
    def first(self):
        return self

    async def count(self):
        return 1 if self.page.upload_ready and self.selector == "input[type='file']" else 0

    async def set_input_files(self, file_paths):
        self.page.uploaded = list(file_paths)


class DelayedUploadPage:
    def __init__(self):
        self.upload_ready = False
        self.uploaded = None

    def locator(self, selector):
        return DelayedUploadLocator(self, selector)


class HiddenInputLocator:
    def __init__(self, page, selector):
        self.page = page
        self.selector = selector

    @property
    def first(self):
        return self

    async def count(self):
        return 1 if self.selector == "input[type='file']" else 0

    async def is_visible(self):
        return False

    async def set_input_files(self, file_paths):
        self.page.uploaded = list(file_paths)


class HiddenInputPage:
    def __init__(self):
        self.uploaded = None

    def locator(self, selector):
        return HiddenInputLocator(self, selector)


class FailingUploadLocator:
    def __init__(self, selector):
        self.selector = selector

    @property
    def first(self):
        return self

    async def count(self):
        return 1 if self.selector == "input[type='file']" else 0

    async def set_input_files(self, file_paths):
        raise RuntimeError("No file to upload")


class FailingUploadPage:
    def locator(self, selector):
        return FailingUploadLocator(selector)


class MixedInputLocator:
    def __init__(self, kind, page):
        self.kind = kind
        self.page = page

    @property
    def first(self):
        return self

    async def count(self):
        return 1

    async def get_attribute(self, name):
        if name != "accept":
            return None
        if self.kind == "video":
            return "video/x-flv,video/mp4,.mp4"
        return "image/png,image/jpeg,image/jpg,image/bmp,image/webp,image/tif"

    async def set_input_files(self, file_paths):
        if self.kind == "video":
            raise RuntimeError("Non-multiple file input can only accept single file")
        self.page.uploaded = list(file_paths)


class MixedInputGroup:
    def __init__(self, page, selector):
        self.page = page
        self.selector = selector
        self.first = MixedInputLocator("video", page)

    async def count(self):
        if self.selector == "input[type='file']":
            return 2
        return 0

    def nth(self, index):
        if index == 0:
            return MixedInputLocator("video", self.page)
        return MixedInputLocator("image", self.page)


class MixedInputPage:
    def __init__(self):
        self.uploaded = None

    def locator(self, selector):
        return MixedInputGroup(self, selector)


class SwitchTabLocator:
    def __init__(self, page, text):
        self.page = page
        self.text = text

    @property
    def first(self):
        return self

    async def count(self):
        return 1 if self.page.tab_ready and self.text == "发布图文" else 0

    async def click(self, timeout=None):
        if self.text == "发布图文":
            self.page.clicked_publish_image = True


class SwitchTabPage:
    def __init__(self):
        self.tab_ready = False
        self.clicked_publish_image = False

    def get_by_text(self, text):
        return SwitchTabLocator(self, text)


class PublishRoleLocator:
    def __init__(self, exists, page):
        self._exists = exists
        self.page = page

    @property
    def first(self):
        return self

    async def count(self):
        return 1 if self._exists else 0

    async def click(self, timeout=None):
        self.page.publish_clicked = True


class PublishCssLocator:
    def __init__(self, exists, page):
        self._exists = exists
        self.page = page

    @property
    def first(self):
        return self

    async def count(self):
        return 1 if self._exists else 0

    async def click(self, timeout=None):
        self.page.publish_clicked = True


class PublishButtonPage:
    def __init__(self, role_exact_exists=False, css_exists=False):
        self.role_exact_exists = role_exact_exists
        self.css_exists = css_exists
        self.publish_clicked = False

    def get_by_role(self, role, name=None, exact=False):
        if role == "button" and name == "发布" and exact and self.role_exact_exists:
            return PublishRoleLocator(True, self)
        return PublishRoleLocator(False, self)

    def locator(self, selector):
        if selector.startswith("button") and self.css_exists:
            return PublishCssLocator(True, self)
        return PublishCssLocator(False, self)


class DouyinImageUploadErrorDetectionTests(unittest.IsolatedAsyncioTestCase):
    async def test_wait_for_image_editor_url_ignores_hidden_error_text(self):
        uploader = DouYinImage(
            title="标题",
            file_paths=["a.png"],
            tags=[],
            publish_date=0,
            account_file="cookies/douyin.json",
            body="",
        )
        page = FakePage(
            visibility_map={"text=不支持gif格式": False},
            url="https://creator.douyin.com/creator-micro/content/upload",
        )

        async def _fast_sleep(_seconds):
            page.url = "https://creator.douyin.com/creator-micro/content/post/image"
            return None

        with patch("uploader.douyin_uploader.main.asyncio.sleep", side_effect=_fast_sleep):
            await uploader.wait_for_image_editor_url(page, timeout_ms=2000)

    async def test_wait_for_image_editor_url_raises_on_visible_error_text(self):
        uploader = DouYinImage(
            title="标题",
            file_paths=["a.png"],
            tags=[],
            publish_date=0,
            account_file="cookies/douyin.json",
            body="",
        )
        page = FakePage(
            visibility_map={"text=不支持gif格式": True},
            url="https://creator.douyin.com/creator-micro/content/upload",
        )

        with self.assertRaisesRegex(RuntimeError, "不支持gif格式"):
            await uploader.wait_for_image_editor_url(page, timeout_ms=1000)

    async def test_upload_images_waits_for_delayed_file_input(self):
        uploader = DouYinImage(
            title="标题",
            file_paths=["a.png"],
            tags=[],
            publish_date=0,
            account_file="cookies/douyin.json",
            body="",
        )
        page = DelayedUploadPage()

        async def _make_ready(_seconds):
            page.upload_ready = True
            return None

        with patch("uploader.douyin_uploader.main.asyncio.sleep", side_effect=_make_ready):
            await uploader.upload_images(page)

        self.assertEqual(page.uploaded, ["a.png"])

    async def test_upload_images_accepts_hidden_file_input(self):
        uploader = DouYinImage(
            title="标题",
            file_paths=["a.png"],
            tags=[],
            publish_date=0,
            account_file="cookies/douyin.json",
            body="",
        )
        page = HiddenInputPage()

        await uploader.upload_images(page, timeout_ms=500)

        self.assertEqual(page.uploaded, ["a.png"])

    async def test_switch_to_image_mode_waits_for_publish_image_tab(self):
        uploader = DouYinImage(
            title="标题",
            file_paths=["a.png"],
            tags=[],
            publish_date=0,
            account_file="cookies/douyin.json",
            body="",
        )
        page = SwitchTabPage()

        async def _make_tab_ready(_seconds):
            page.tab_ready = True
            return None

        with patch("uploader.douyin_uploader.main.asyncio.sleep", side_effect=_make_tab_ready):
            await uploader.switch_to_image_mode(page)

        self.assertTrue(page.clicked_publish_image)

    async def test_upload_images_surfaces_set_input_files_error(self):
        uploader = DouYinImage(
            title="标题",
            file_paths=["/path/not-found.png"],
            tags=[],
            publish_date=0,
            account_file="cookies/douyin.json",
            body="",
        )
        page = FailingUploadPage()

        with self.assertRaisesRegex(RuntimeError, "上传输入框已找到，但设置文件失败"):
            await uploader.upload_images(page, timeout_ms=300)

    async def test_upload_images_prefers_image_input_when_video_input_exists(self):
        uploader = DouYinImage(
            title="标题",
            file_paths=["1.png", "2.png"],
            tags=[],
            publish_date=0,
            account_file="cookies/douyin.json",
            body="",
        )
        page = MixedInputPage()

        await uploader.upload_images(page, timeout_ms=500)

        self.assertEqual(page.uploaded, ["1.png", "2.png"])

    async def test_click_publish_button_uses_exact_role_match(self):
        uploader = DouYinImage(
            title="标题",
            file_paths=["1.png"],
            tags=[],
            publish_date=0,
            account_file="cookies/douyin.json",
            body="",
        )
        page = PublishButtonPage(role_exact_exists=True, css_exists=False)

        await uploader.click_publish_button(page)

        self.assertTrue(page.publish_clicked)


if __name__ == "__main__":
    unittest.main()
