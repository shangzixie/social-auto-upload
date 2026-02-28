# -*- coding: utf-8 -*-
from datetime import datetime
from pathlib import Path

from playwright.async_api import Playwright, async_playwright, Page
import os
import asyncio

from conf import LOCAL_CHROME_PATH, LOCAL_CHROME_HEADLESS
from utils.base_social_media import set_init_script
from utils.log import douyin_logger


async def cookie_auth(account_file):
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=LOCAL_CHROME_HEADLESS)
        context = await browser.new_context(storage_state=account_file)
        context = await set_init_script(context)
        # 创建一个新的页面
        page = await context.new_page()
        # 访问指定的 URL
        await page.goto("https://creator.douyin.com/creator-micro/content/upload")
        try:
            await page.wait_for_url("https://creator.douyin.com/creator-micro/content/upload", timeout=5000)
        except:
            print("[+] 等待5秒 cookie 失效")
            await context.close()
            await browser.close()
            return False
        # 2024.06.17 抖音创作者中心改版
        if await page.get_by_text('手机号登录').count() or await page.get_by_text('扫码登录').count():
            print("[+] 等待5秒 cookie 失效")
            return False
        else:
            print("[+] cookie 有效")
            return True


async def douyin_setup(account_file, handle=False):
    if not os.path.exists(account_file) or not await cookie_auth(account_file):
        if not handle:
            # Todo alert message
            return False
        douyin_logger.info('[+] cookie文件不存在或已失效，即将自动打开浏览器，请扫码登录，登陆后会自动生成cookie文件')
        await douyin_cookie_gen(account_file)
    return True


async def douyin_cookie_gen(account_file):
    async with async_playwright() as playwright:
        options = {
            'headless': LOCAL_CHROME_HEADLESS
        }
        # Make sure to run headed.
        browser = await playwright.chromium.launch(**options)
        # Setup context however you like.
        context = await browser.new_context()  # Pass any options
        context = await set_init_script(context)
        # Pause the page, and start recording manually.
        page = await context.new_page()
        await page.goto("https://creator.douyin.com/")
        await page.pause()
        # 点击调试器的继续，保存cookie
        await context.storage_state(path=account_file)


class DouYinVideo(object):
    def __init__(self, title, file_path, tags, publish_date: datetime, account_file, thumbnail_path=None, productLink='', productTitle=''):
        self.title = title  # 视频标题
        self.file_path = file_path
        self.tags = tags
        self.publish_date = publish_date
        self.account_file = account_file
        self.date_format = '%Y年%m月%d日 %H:%M'
        self.local_executable_path = LOCAL_CHROME_PATH
        self.headless = LOCAL_CHROME_HEADLESS
        self.thumbnail_path = thumbnail_path
        self.productLink = productLink
        self.productTitle = productTitle

    async def set_schedule_time_douyin(self, page, publish_date):
        # 选择包含特定文本内容的 label 元素
        label_element = page.locator("[class^='radio']:has-text('定时发布')")
        # 在选中的 label 元素下点击 checkbox
        await label_element.click()
        await asyncio.sleep(1)
        publish_date_hour = publish_date.strftime("%Y-%m-%d %H:%M")

        await asyncio.sleep(1)
        await page.locator('.semi-input[placeholder="日期和时间"]').click()
        await page.keyboard.press("Control+KeyA")
        await page.keyboard.type(str(publish_date_hour))
        await page.keyboard.press("Enter")

        await asyncio.sleep(1)

    async def handle_upload_error(self, page):
        douyin_logger.info('视频出错了，重新上传中')
        await page.locator('div.progress-div [class^="upload-btn-input"]').set_input_files(self.file_path)

    async def upload(self, playwright: Playwright) -> None:
        # 使用 Chromium 浏览器启动一个浏览器实例
        if self.local_executable_path:
            browser = await playwright.chromium.launch(headless=self.headless, executable_path=self.local_executable_path)
        else:
            browser = await playwright.chromium.launch(headless=self.headless)
        # 创建一个浏览器上下文，使用指定的 cookie 文件
        context = await browser.new_context(storage_state=f"{self.account_file}")
        context = await set_init_script(context)

        # 创建一个新的页面
        page = await context.new_page()
        # 访问指定的 URL
        await page.goto("https://creator.douyin.com/creator-micro/content/upload")
        douyin_logger.info(f'[+]正在上传-------{self.title}.mp4')
        # 等待页面跳转到指定的 URL，没进入，则自动等待到超时
        douyin_logger.info(f'[-] 正在打开主页...')
        await page.wait_for_url("https://creator.douyin.com/creator-micro/content/upload")
        # 点击 "上传视频" 按钮
        await page.locator("div[class^='container'] input").set_input_files(self.file_path)

        # 等待页面跳转到指定的 URL 2025.01.08修改在原有基础上兼容两种页面
        while True:
            try:
                # 尝试等待第一个 URL
                await page.wait_for_url(
                    "https://creator.douyin.com/creator-micro/content/publish?enter_from=publish_page", timeout=3000)
                douyin_logger.info("[+] 成功进入version_1发布页面!")
                break  # 成功进入页面后跳出循环
            except Exception:
                try:
                    # 如果第一个 URL 超时，再尝试等待第二个 URL
                    await page.wait_for_url(
                        "https://creator.douyin.com/creator-micro/content/post/video?enter_from=publish_page",
                        timeout=3000)
                    douyin_logger.info("[+] 成功进入version_2发布页面!")

                    break  # 成功进入页面后跳出循环
                except:
                    print("  [-] 超时未进入视频发布页面，重新尝试...")
                    await asyncio.sleep(0.5)  # 等待 0.5 秒后重新尝试
        # 填充标题和话题
        # 检查是否存在包含输入框的元素
        # 这里为了避免页面变化，故使用相对位置定位：作品标题父级右侧第一个元素的input子元素
        await asyncio.sleep(1)
        douyin_logger.info(f'  [-] 正在填充标题和话题...')
        title_container = page.get_by_text('作品标题').locator("..").locator("xpath=following-sibling::div[1]").locator("input")
        if await title_container.count():
            await title_container.fill(self.title[:30])
        else:
            titlecontainer = page.locator(".notranslate")
            await titlecontainer.click()
            await page.keyboard.press("Backspace")
            await page.keyboard.press("Control+KeyA")
            await page.keyboard.press("Delete")
            await page.keyboard.type(self.title)
            await page.keyboard.press("Enter")
        css_selector = ".zone-container"
        for index, tag in enumerate(self.tags, start=1):
            await page.type(css_selector, "#" + tag)
            await page.press(css_selector, "Space")
        douyin_logger.info(f'总共添加{len(self.tags)}个话题')
        while True:
            # 判断重新上传按钮是否存在，如果不存在，代表视频正在上传，则等待
            try:
                #  新版：定位重新上传
                number = await page.locator('[class^="long-card"] div:has-text("重新上传")').count()
                if number > 0:
                    douyin_logger.success("  [-]视频上传完毕")
                    break
                else:
                    douyin_logger.info("  [-] 正在上传视频中...")
                    await asyncio.sleep(2)

                    if await page.locator('div.progress-div > div:has-text("上传失败")').count():
                        douyin_logger.error("  [-] 发现上传出错了... 准备重试")
                        await self.handle_upload_error(page)
            except:
                douyin_logger.info("  [-] 正在上传视频中...")
                await asyncio.sleep(2)

        if self.productLink and self.productTitle:
            douyin_logger.info(f'  [-] 正在设置商品链接...')
            await self.set_product_link(page, self.productLink, self.productTitle)
            douyin_logger.info(f'  [+] 完成设置商品链接...')
        
        #上传视频封面
        await self.set_thumbnail(page, self.thumbnail_path)

        # 更换可见元素
        await self.set_location(page, "")


        # 頭條/西瓜
        third_part_element = '[class^="info"] > [class^="first-part"] div div.semi-switch'
        # 定位是否有第三方平台
        if await page.locator(third_part_element).count():
            # 检测是否是已选中状态
            if 'semi-switch-checked' not in await page.eval_on_selector(third_part_element, 'div => div.className'):
                await page.locator(third_part_element).locator('input.semi-switch-native-control').click()

        if self.publish_date != 0:
            await self.set_schedule_time_douyin(page, self.publish_date)

        # 判断视频是否发布成功
        while True:
            # 判断视频是否发布成功
            try:
                publish_button = page.get_by_role('button', name="发布", exact=True)
                if await publish_button.count():
                    await publish_button.click()
                await page.wait_for_url("https://creator.douyin.com/creator-micro/content/manage**",
                                        timeout=3000)  # 如果自动跳转到作品页面，则代表发布成功
                douyin_logger.success("  [-]视频发布成功")
                break
            except:
                # 尝试处理封面问题
                await self.handle_auto_video_cover(page)
                douyin_logger.info("  [-] 视频正在发布中...")
                await page.screenshot(full_page=True)
                await asyncio.sleep(0.5)

        await context.storage_state(path=self.account_file)  # 保存cookie
        douyin_logger.success('  [-]cookie更新完毕！')
        await asyncio.sleep(2)  # 这里延迟是为了方便眼睛直观的观看
        # 关闭浏览器上下文和浏览器实例
        await context.close()
        await browser.close()

    async def handle_auto_video_cover(self, page):
        """
        处理必须设置封面的情况，点击推荐封面的第一个
        """
        # 1. 判断是否出现 "请设置封面后再发布" 的提示
        # 必须确保提示是可见的 (is_visible)，因为 DOM 中可能存在隐藏的历史提示
        if await page.get_by_text("请设置封面后再发布").first.is_visible():
            print("  [-] 检测到需要设置封面提示...")

            # 2. 定位“智能推荐封面”区域下的第一个封面
            # 使用 class^= 前缀匹配，避免 hash 变化导致失效
            recommend_cover = page.locator('[class^="recommendCover-"]').first

            if await recommend_cover.count():
                print("  [-] 正在选择第一个推荐封面...")
                try:
                    await recommend_cover.click()
                    await asyncio.sleep(1)  # 等待选中生效

                    # 3. 处理可能的确认弹窗 "是否确认应用此封面？"
                    # 并不一定每次都会出现，健壮性判断：如果出现弹窗，则点击确定
                    confirm_text = "是否确认应用此封面？"
                    if await page.get_by_text(confirm_text).first.is_visible():
                        print(f"  [-] 检测到确认弹窗: {confirm_text}")
                        # 直接点击“确定”按钮，不依赖脆弱的 CSS 类名
                        await page.get_by_role("button", name="确定").click()
                        print("  [-] 已点击确认应用封面")
                        await asyncio.sleep(1)

                    print("  [-] 已完成封面选择流程")
                    return True
                except Exception as e:
                    print(f"  [-] 选择封面失败: {e}")

        return False

    async def set_thumbnail(self, page: Page, thumbnail_path: str):
        if thumbnail_path:
            douyin_logger.info('  [-] 正在设置视频封面...')
            await page.click('text="选择封面"')
            await page.wait_for_selector("div.dy-creator-content-modal")
            await page.click('text="设置竖封面"')
            await page.wait_for_timeout(2000)  # 等待2秒
            # 定位到上传区域并点击
            await page.locator("div[class^='semi-upload upload'] >> input.semi-upload-hidden-input").set_input_files(thumbnail_path)
            await page.wait_for_timeout(2000)  # 等待2秒
            await page.locator("div#tooltip-container button:visible:has-text('完成')").click()
            # finish_confirm_element = page.locator("div[class^='confirmBtn'] >> div:has-text('完成')")
            # if await finish_confirm_element.count():
            #     await finish_confirm_element.click()
            # await page.locator("div[class^='footer'] button:has-text('完成')").click()
            douyin_logger.info('  [+] 视频封面设置完成！')
            # 等待封面设置对话框关闭
            await page.wait_for_selector("div.extractFooter", state='detached')
            

    async def set_location(self, page: Page, location: str = ""):
        if not location:
            return
        # todo supoort location later
        # await page.get_by_text('添加标签').locator("..").locator("..").locator("xpath=following-sibling::div").locator(
        #     "div.semi-select-single").nth(0).click()
        await page.locator('div.semi-select span:has-text("输入地理位置")').click()
        await page.keyboard.press("Backspace")
        await page.wait_for_timeout(2000)
        await page.keyboard.type(location)
        await page.wait_for_selector('div[role="listbox"] [role="option"]', timeout=5000)
        await page.locator('div[role="listbox"] [role="option"]').first.click()

    async def handle_product_dialog(self, page: Page, product_title: str):
        """处理商品编辑弹窗"""

        await page.wait_for_timeout(2000)
        await page.wait_for_selector('input[placeholder="请输入商品短标题"]', timeout=10000)
        short_title_input = page.locator('input[placeholder="请输入商品短标题"]')
        if not await short_title_input.count():
            douyin_logger.error("[-] 未找到商品短标题输入框")
            return False
        product_title = product_title[:10]
        await short_title_input.fill(product_title)
        # 等待一下让界面响应
        await page.wait_for_timeout(1000)

        finish_button = page.locator('button:has-text("完成编辑")')
        if 'disabled' not in await finish_button.get_attribute('class'):
            await finish_button.click()
            douyin_logger.debug("[+] 成功点击'完成编辑'按钮")
            
            # 等待对话框关闭
            await page.wait_for_selector('.semi-modal-content', state='hidden', timeout=5000)
            return True
        else:
            douyin_logger.error("[-] '完成编辑'按钮处于禁用状态，尝试直接关闭对话框")
            # 如果按钮禁用，尝试点击取消或关闭按钮
            cancel_button = page.locator('button:has-text("取消")')
            if await cancel_button.count():
                await cancel_button.click()
            else:
                # 点击右上角的关闭按钮
                close_button = page.locator('.semi-modal-close')
                await close_button.click()
            
            await page.wait_for_selector('.semi-modal-content', state='hidden', timeout=5000)
            return False
        
    async def set_product_link(self, page: Page, product_link: str, product_title: str):
        """设置商品链接功能"""
        await page.wait_for_timeout(2000)  # 等待2秒
        try:
            # 定位"添加标签"文本，然后向上导航到容器，再找到下拉框
            await page.wait_for_selector('text=添加标签', timeout=10000)
            dropdown = page.get_by_text('添加标签').locator("..").locator("..").locator("..").locator(".semi-select").first
            if not await dropdown.count():
                douyin_logger.error("[-] 未找到标签下拉框")
                return False
            douyin_logger.debug("[-] 找到标签下拉框，准备选择'购物车'")
            await dropdown.click()
            ## 等待下拉选项出现
            await page.wait_for_selector('[role="listbox"]', timeout=5000)
            ## 选择"购物车"选项
            await page.locator('[role="option"]:has-text("购物车")').click()
            douyin_logger.debug("[+] 成功选择'购物车'")
            
            # 输入商品链接
            ## 等待商品链接输入框出现
            await page.wait_for_selector('input[placeholder="粘贴商品链接"]', timeout=5000)
            # 输入
            input_field = page.locator('input[placeholder="粘贴商品链接"]')
            await input_field.fill(product_link)
            douyin_logger.debug(f"[+] 已输入商品链接: {product_link}")
            
            # 点击"添加链接"按钮
            add_button = page.locator('span:has-text("添加链接")')
            ## 检查按钮是否可用（没有disable类）
            button_class = await add_button.get_attribute('class')
            if 'disable' in button_class:
                douyin_logger.error("[-] '添加链接'按钮不可用")
                return False
            await add_button.click()
            douyin_logger.debug("[+] 成功点击'添加链接'按钮")
            ## 如果链接不可用
            await page.wait_for_timeout(2000)
            error_modal = page.locator('text=未搜索到对应商品')
            if await error_modal.count():
                confirm_button = page.locator('button:has-text("确定")')
                await confirm_button.click()
                # await page.wait_for_selector('.semi-modal-content', state='hidden', timeout=5000)
                douyin_logger.error("[-] 商品链接无效")
                return False

            # 填写商品短标题
            if not await self.handle_product_dialog(page, product_title):
                return False
            
            # 等待链接添加完成
            douyin_logger.debug("[+] 成功设置商品链接")
            return True
        except Exception as e:
            douyin_logger.error(f"[-] 设置商品链接时出错: {str(e)}")
            return False

    async def main(self):
        async with async_playwright() as playwright:
            await self.upload(playwright)


class DouYinImage(object):
    def __init__(self, title, file_paths, tags, publish_date: datetime, account_file, body=''):
        self.title = title
        self.file_paths = [str(file_path) for file_path in file_paths]
        self.tags = tags
        self.body = str(body or "").strip()
        self.publish_date = publish_date
        self.account_file = account_file
        self.date_format = '%Y年%m月%d日 %H:%M'
        self.local_executable_path = LOCAL_CHROME_PATH
        self.headless = LOCAL_CHROME_HEADLESS

    @staticmethod
    def build_note_content(body, tags):
        body_text = str(body or "").strip()
        tag_tokens = [f"#{str(tag).strip()}" for tag in tags if str(tag).strip()]
        tags_text = " ".join(tag_tokens)
        if body_text and tags_text:
            return f"{body_text}\n{tags_text}"
        return body_text or tags_text

    async def set_schedule_time_douyin(self, page, publish_date):
        label_element = page.locator("[class^='radio']:has-text('定时发布')")
        await label_element.click()
        await asyncio.sleep(1)
        publish_date_hour = publish_date.strftime("%Y-%m-%d %H:%M")
        await asyncio.sleep(1)
        await page.locator('.semi-input[placeholder="日期和时间"]').click()
        await page.keyboard.press("Control+KeyA")
        await page.keyboard.type(str(publish_date_hour))
        await page.keyboard.press("Enter")
        await asyncio.sleep(1)

    async def switch_to_image_mode(self, page: Page, timeout_ms: int = 8000):
        tab_texts = ["发布图文", "上传图文", "图文"]
        loop = asyncio.get_running_loop()
        start = loop.time()
        while (loop.time() - start) * 1000 < timeout_ms:
            for text in tab_texts:
                button = page.get_by_text(text).first
                try:
                    if await button.count():
                        await button.click(timeout=4000)
                        await asyncio.sleep(0.3)
                        return
                except Exception:
                    continue
            await asyncio.sleep(0.2)

        debug_path = await self.dump_debug_artifacts(page, "switch_to_image_mode_timeout")
        raise RuntimeError(f"未找到抖音“发布图文”入口，请检查页面结构（诊断目录：{debug_path}）")

    async def upload_images(self, page: Page, timeout_ms: int = 8000):
        await self.dismiss_blocking_overlays(page)
        upload_selectors = [
            "div[class^='container'] input[type='file']",
            "input[type='file']",
        ]

        loop = asyncio.get_running_loop()
        start = loop.time()
        found_input = False
        last_exc = None
        while (loop.time() - start) * 1000 < timeout_ms:
            for selector in upload_selectors:
                input_group = page.locator(selector)
                try:
                    count = await input_group.count()
                    if count <= 0:
                        continue
                    ordered_inputs = []
                    fallback_inputs = []
                    input_candidates = []
                    if hasattr(input_group, "nth"):
                        for idx in range(count):
                            input_candidates.append(input_group.nth(idx))
                    elif hasattr(input_group, "first"):
                        input_candidates.append(input_group.first)
                    else:
                        input_candidates.append(input_group)

                    for input_file in input_candidates:
                        is_image_input = False
                        try:
                            accept = (await input_file.get_attribute("accept") or "").lower()
                            is_image_input = "image/" in accept or "image" in accept
                        except Exception:
                            is_image_input = False
                        if is_image_input:
                            ordered_inputs.append(input_file)
                        else:
                            fallback_inputs.append(input_file)

                    for input_file in ordered_inputs + fallback_inputs:
                        try:
                            found_input = True
                            await input_file.set_input_files(self.file_paths)
                            return
                        except Exception as exc:
                            last_exc = exc
                            continue
                except Exception as exc:
                    last_exc = exc
                    continue
            await asyncio.sleep(0.2)

        debug_path = await self.dump_debug_artifacts(page, "upload_images_timeout")
        if found_input and last_exc is not None:
            raise RuntimeError(
                f"抖音图文上传输入框已找到，但设置文件失败：{last_exc}（诊断目录：{debug_path}）"
            )
        raise RuntimeError(f"未找到抖音图文上传输入框，请检查页面结构（诊断目录：{debug_path}）")

    async def dismiss_blocking_overlays(self, page: Page):
        dismiss_texts = ["我知道了", "知道了", "跳过", "稍后再说"]
        if not hasattr(page, "get_by_text"):
            return
        for text in dismiss_texts:
            try:
                button = page.get_by_text(text).first
                if await button.count():
                    await button.click(timeout=1000)
                    await asyncio.sleep(0.2)
                    return
            except Exception:
                continue

    async def dump_debug_artifacts(self, page: Page, reason: str) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_dir = Path("logs") / "douyin_debug" / f"{timestamp}_{reason}"
        out_dir.mkdir(parents=True, exist_ok=True)

        url_text = ""
        try:
            url_text = str(page.url)
        except Exception:
            url_text = ""

        try:
            (out_dir / "meta.txt").write_text(f"reason={reason}\nurl={url_text}\n", encoding="utf-8")
        except Exception:
            pass

        try:
            files_text = "\n".join(
                f"{path}\texists={Path(path).exists()}" for path in self.file_paths
            )
            (out_dir / "files.txt").write_text(files_text + "\n", encoding="utf-8")
        except Exception:
            pass

        try:
            if hasattr(page, "screenshot"):
                await page.screenshot(path=str(out_dir / "page.png"), full_page=True)
        except Exception:
            pass

        try:
            if hasattr(page, "content"):
                html = await page.content()
                (out_dir / "page.html").write_text(html, encoding="utf-8")
        except Exception:
            pass

        return str(out_dir)

    async def wait_for_image_editor_ready(self, page: Page, timeout_ms: int = 30000):
        editor_selectors = [
            "input[placeholder*='作品标题']",
            "input[placeholder*='输入标题']",
            "textarea[placeholder*='标题']",
            "div[contenteditable='true'][role='textbox']",
            "div[contenteditable='true'][data-placeholder*='简介']",
            "div[contenteditable='true'][data-placeholder*='描述']",
        ]
        upload_error_selectors = [
            "text=不支持该格式",
            "text=不支持gif格式",
            "text=上传失败",
            "text=格式不支持",
            "text=图片上传失败",
            "text=文件上传失败",
        ]

        loop = asyncio.get_running_loop()
        start = loop.time()
        while (loop.time() - start) * 1000 < timeout_ms:
            for selector in editor_selectors:
                try:
                    locator = page.locator(selector).first
                    if await locator.count():
                        return
                except Exception:
                    continue

            for selector in upload_error_selectors:
                try:
                    if await self.error_text_visible(page, selector):
                        raise RuntimeError(f"抖音图文素材上传失败：检测到提示“{selector.replace('text=', '')}”")
                except RuntimeError:
                    raise
                except Exception:
                    continue

            await asyncio.sleep(0.5)

        raise RuntimeError("抖音图文素材上传后未进入编辑页，请确认图片格式为 jpg/jpeg/png/webp 且文件可用")

    async def wait_for_image_editor_url(self, page: Page, timeout_ms: int = 45000):
        upload_error_selectors = [
            "text=不支持该格式",
            "text=不支持gif格式",
            "text=上传失败",
            "text=格式不支持",
            "text=图片上传失败",
            "text=文件上传失败",
        ]
        target_path = "/creator-micro/content/post/image"

        loop = asyncio.get_running_loop()
        start = loop.time()
        while (loop.time() - start) * 1000 < timeout_ms:
            if target_path in page.url:
                return

            for selector in upload_error_selectors:
                try:
                    if await self.error_text_visible(page, selector):
                        raise RuntimeError(f"抖音图文素材上传失败：检测到提示“{selector.replace('text=', '')}”")
                except RuntimeError:
                    raise
                except Exception:
                    continue

            await asyncio.sleep(0.5)

        raise RuntimeError(
            f"抖音图文素材上传后未跳转到编辑页({target_path})，当前页面：{page.url}"
        )

    async def error_text_visible(self, page: Page, selector: str) -> bool:
        locator = page.locator(selector).first
        if not await locator.count():
            return False
        try:
            return await locator.is_visible()
        except Exception:
            return False

    async def fill_title_and_desc(self, page: Page):
        douyin_logger.info('  [-] 正在填充图文标题和正文...')
        title_selectors = [
            "input[placeholder*='作品标题']",
            "input[placeholder*='输入标题']",
            "textarea[placeholder*='标题']",
        ]
        title_filled = False
        for selector in title_selectors:
            locator = page.locator(selector).first
            try:
                if await locator.count():
                    await locator.click(timeout=3000)
                    await locator.fill(self.title[:30], timeout=3000)
                    title_filled = True
                    break
            except Exception:
                continue
        if not title_filled:
            fallback_title = page.locator(".notranslate").first
            if await fallback_title.count():
                await fallback_title.click()
                await page.keyboard.press("Control+KeyA")
                await page.keyboard.press("Delete")
                await page.keyboard.type(self.title[:30])

        note_text = self.build_note_content(self.body, self.tags)
        if not note_text:
            return

        desc_selectors = [
            "div[contenteditable='true'][role='textbox']",
            "div[contenteditable='true'][data-placeholder*='简介']",
            "div[contenteditable='true'][data-placeholder*='描述']",
            "div[contenteditable='true']",
            "textarea[placeholder*='作品简介']",
            "textarea[placeholder*='输入作品简介']",
            ".zone-container",
            ".notranslate",
        ]
        for selector in desc_selectors:
            locator = page.locator(selector).first
            try:
                if await locator.count():
                    await locator.click(timeout=3000)
                    if selector.startswith("textarea"):
                        await locator.fill(note_text)
                    else:
                        await page.keyboard.type(note_text)
                    return
            except Exception:
                continue
        raise RuntimeError("未找到抖音图文正文输入框，请检查页面结构")

    async def click_publish_button(self, page: Page):
        # Prefer an exact "发布" action button to avoid clicking unrelated
        # controls such as "高消发布"/"发布视频"/"发布图文" tab items.
        publish_button = page.get_by_role("button", name="发布", exact=True).first
        if await publish_button.count():
            await publish_button.click()
            return

        fallback_selectors = [
            "button:has-text('发布'):not(:has-text('高消发布')):not(:has-text('发布视频')):not(:has-text('发布图文'))",
            "button.semi-button-primary:has-text('发布')",
        ]
        for selector in fallback_selectors:
            locator = page.locator(selector).first
            try:
                if await locator.count():
                    await locator.click()
                    return
            except Exception:
                continue

        raise RuntimeError("未找到抖音图文发布按钮，请检查页面结构")

    async def upload(self, playwright: Playwright) -> None:
        if self.local_executable_path:
            browser = await playwright.chromium.launch(headless=self.headless, executable_path=self.local_executable_path)
        else:
            browser = await playwright.chromium.launch(headless=self.headless)
        context = await browser.new_context(storage_state=f"{self.account_file}")
        context = await set_init_script(context)
        page = await context.new_page()
        await page.goto("https://creator.douyin.com/creator-micro/content/upload")
        await page.wait_for_url("https://creator.douyin.com/creator-micro/content/upload")
        douyin_logger.info(f'[+]正在上传抖音图文，共{len(self.file_paths)}张')

        await self.switch_to_image_mode(page)
        await self.upload_images(page)
        await self.wait_for_image_editor_url(page, timeout_ms=45000)
        await self.wait_for_image_editor_ready(page, timeout_ms=30000)
        await self.fill_title_and_desc(page)

        if self.publish_date != 0:
            await self.set_schedule_time_douyin(page, self.publish_date)

        loop = asyncio.get_running_loop()
        publish_start = loop.time()
        while (loop.time() - publish_start) < 90:
            try:
                if self.publish_date != 0:
                    schedule_button = page.get_by_role("button", name="定时发布", exact=True).first
                    if await schedule_button.count():
                        await schedule_button.click()
                    else:
                        await self.click_publish_button(page)
                else:
                    await self.click_publish_button(page)
                await page.wait_for_url(
                    "https://creator.douyin.com/creator-micro/content/manage**",
                    timeout=3000
                )
                douyin_logger.success("  [-]图文发布成功")
                break
            except Exception:
                douyin_logger.info("  [-] 图文正在发布中...")
                await asyncio.sleep(0.5)
        else:
            debug_path = await self.dump_debug_artifacts(page, "publish_timeout")
            raise RuntimeError(f"抖音图文发布超时，请检查页面状态（诊断目录：{debug_path}）")

        await context.storage_state(path=self.account_file)
        douyin_logger.success('  [-]cookie更新完毕！')
        await asyncio.sleep(2)
        await context.close()
        await browser.close()

    async def main(self):
        async with async_playwright() as playwright:
            await self.upload(playwright)
