import sys
import types
import unittest


# Test environment may not have loguru installed.
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


# Test environment may not have playwright installed.
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


CHECKBOX_SELECTOR = ".d-modal .d-checkbox input[type='checkbox']"
DECLARE_SELECTOR = ".d-modal button:has-text('声明原创')"


class FakeLocator:
    def __init__(self, page, selector):
        self.page = page
        self.selector = selector

    @property
    def first(self):
        return self

    async def count(self):
        if self.selector == ".d-modal-mask":
            return 1 if self.page.mask_visible and self.page.modal_visible else 0
        if self.selector == ".d-modal":
            return 1 if self.page.modal_visible else 0
        if self.selector in self.page.present_selectors and self.page.modal_visible:
            return 1
        return 0

    async def click(self, timeout=None, force=False):
        self.page.clicks.append(self.selector)
        if self.selector == CHECKBOX_SELECTOR:
            if self.page.fail_input_checkbox_click:
                raise RuntimeError("input checkbox click failed")
            self.page.checkbox_checked = True
            return
        if self.selector == ".d-modal .d-checkbox .d-checkbox-simulator":
            self.page.checkbox_checked = True
            return
        if self.selector == DECLARE_SELECTOR:
            if not self.page.checkbox_checked:
                raise RuntimeError("声明原创按钮仍为禁用态")
            self.page.modal_visible = False

    async def wait_for(self, state=None, timeout=None):
        if self.selector == ".d-modal-mask" and state == "hidden" and self.page.modal_visible:
            raise RuntimeError("modal still visible")

    async def is_checked(self):
        return self.page.checkbox_checked


class FakePage:
    def __init__(self, present_selectors, mask_visible=True, fail_input_checkbox_click=False):
        self.present_selectors = set(present_selectors)
        self.modal_visible = True
        self.mask_visible = mask_visible
        self.fail_input_checkbox_click = fail_input_checkbox_click
        self.checkbox_checked = False
        self.clicks = []

    def locator(self, selector):
        return FakeLocator(self, selector)


class XhsOriginalModalTests(unittest.IsolatedAsyncioTestCase):
    async def test_dismiss_modal_checks_agreement_before_declaring_original(self):
        uploader = XiaoHongShuImage(
            title="title",
            file_paths=["a.jpg"],
            tags=[],
            publish_date=0,
            account_file="cookies/xhs.json",
            original_declare=True,
            visibility="public",
        )
        page = FakePage({CHECKBOX_SELECTOR, DECLARE_SELECTOR})

        await uploader.dismiss_intercept_modal(page)

        self.assertIn(CHECKBOX_SELECTOR, page.clicks)
        self.assertIn(DECLARE_SELECTOR, page.clicks)
        self.assertLess(page.clicks.index(CHECKBOX_SELECTOR), page.clicks.index(DECLARE_SELECTOR))

    async def test_dismiss_modal_without_mask_still_handles_original_modal(self):
        uploader = XiaoHongShuImage(
            title="title",
            file_paths=["a.jpg"],
            tags=[],
            publish_date=0,
            account_file="cookies/xhs.json",
            original_declare=True,
            visibility="public",
        )
        page = FakePage({".d-modal", CHECKBOX_SELECTOR, DECLARE_SELECTOR}, mask_visible=False)

        await uploader.dismiss_intercept_modal(page)

        self.assertFalse(page.modal_visible)
        self.assertIn(CHECKBOX_SELECTOR, page.clicks)
        self.assertIn(DECLARE_SELECTOR, page.clicks)

    async def test_dismiss_modal_falls_back_to_checkbox_simulator(self):
        uploader = XiaoHongShuImage(
            title="title",
            file_paths=["a.jpg"],
            tags=[],
            publish_date=0,
            account_file="cookies/xhs.json",
            original_declare=True,
            visibility="public",
        )
        page = FakePage(
            {".d-modal", CHECKBOX_SELECTOR, ".d-modal .d-checkbox .d-checkbox-simulator", DECLARE_SELECTOR},
            mask_visible=False,
            fail_input_checkbox_click=True,
        )

        await uploader.dismiss_intercept_modal(page)

        self.assertFalse(page.modal_visible)
        self.assertIn(".d-modal .d-checkbox .d-checkbox-simulator", page.clicks)


if __name__ == "__main__":
    unittest.main()
