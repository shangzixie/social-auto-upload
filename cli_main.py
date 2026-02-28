import argparse
import asyncio
from datetime import datetime
from os.path import exists
from pathlib import Path

from conf import BASE_DIR
from uploader.douyin_uploader.main import douyin_setup, DouYinVideo, DouYinImage
from uploader.ks_uploader.main import ks_setup, KSVideo
from uploader.tencent_uploader.main import weixin_setup, TencentVideo
from uploader.tk_uploader.main_chrome import tiktok_setup, TiktokVideo
from uploader.xiaohongshu_uploader.main import xiaohongshu_setup, XiaoHongShuImage
from utils.base_social_media import get_supported_social_media, get_cli_action, SOCIAL_MEDIA_DOUYIN, \
    SOCIAL_MEDIA_TENCENT, SOCIAL_MEDIA_TIKTOK, SOCIAL_MEDIA_KUAISHOU, SOCIAL_MEDIA_XIAOHONGSHU
from utils.constant import TencentZoneTypes
from utils.files_times import get_title_and_hashtags


def parse_schedule(schedule_raw):
    if schedule_raw:
        schedule = datetime.strptime(schedule_raw, '%Y-%m-%d %H:%M')
    else:
        schedule = None
    return schedule


async def main():
    # 主解析器
    parser = argparse.ArgumentParser(description="Upload video to multiple social-media.")
    parser.add_argument("platform", metavar='platform', choices=get_supported_social_media(), help="Choose social-media platform: douyin tencent tiktok kuaishou")

    parser.add_argument("account_name", type=str, help="Account name for the platform: xiaoA")
    subparsers = parser.add_subparsers(dest="action", metavar='action', help="Choose action", required=True)

    actions = list(get_cli_action())
    if "xhs-image-upload" not in actions:
        actions.append("xhs-image-upload")
    if "douyin-image-upload" not in actions:
        actions.append("douyin-image-upload")
    for action in actions:
        action_parser = subparsers.add_parser(action, help=f'{action} operation')
        if action == 'login':
            # Login 不需要额外参数
            continue
        elif action == 'upload':
            action_parser.add_argument("video_file", help="Path to the Video file")
            action_parser.add_argument("-pt", "--publish_type", type=int, choices=[0, 1],
                                       help="0 for immediate, 1 for scheduled", default=0)
            action_parser.add_argument('-t', '--schedule', help='Schedule UTC time in %Y-%m-%d %H:%M format')
        elif action == 'xhs-image-upload':
            action_parser.add_argument("image_files", nargs="+", help="Paths to image files (max 9)")
            action_parser.add_argument("--title", required=True, help="Post title")
            action_parser.add_argument("--tags", default="", help="Comma-separated tags, e.g. 美食,探店")
            action_parser.add_argument("-pt", "--publish_type", type=int, choices=[0, 1],
                                       help="0 for immediate, 1 for scheduled", default=0)
            action_parser.add_argument('-t', '--schedule', help='Schedule UTC time in %Y-%m-%d %H:%M format')
            action_parser.add_argument("--original-declare", action="store_true", help="Enable original declaration")
            action_parser.add_argument("--visibility", choices=["public", "private"], default="public",
                                       help="Visibility scope: public or private")
        elif action == 'douyin-image-upload':
            action_parser.add_argument("image_files", nargs="+", help="Paths to image files (max 9)")
            action_parser.add_argument("--title", required=True, help="Post title")
            action_parser.add_argument("--body", default="", help="Post body text")
            action_parser.add_argument("--tags", default="", help="Comma-separated tags, e.g. 美食,探店")
            action_parser.add_argument("-pt", "--publish_type", type=int, choices=[0, 1],
                                       help="0 for immediate, 1 for scheduled", default=0)
            action_parser.add_argument('-t', '--schedule', help='Schedule UTC time in %Y-%m-%d %H:%M format')

    # 解析命令行参数
    args = parser.parse_args()
    # 参数校验
    if args.action == 'upload':
        if not exists(args.video_file):
            raise FileNotFoundError(f'Could not find the video file at {args.video_file}')
        if args.publish_type == 1 and not args.schedule:
            parser.error("The schedule must must be specified for scheduled publishing.")
    if args.action == 'xhs-image-upload':
        if args.platform != SOCIAL_MEDIA_XIAOHONGSHU:
            parser.error("xhs-image-upload only supports platform 'xiaohongshu'.")
        if len(args.image_files) == 0:
            parser.error("At least one image file is required.")
        if len(args.image_files) > 9:
            parser.error("xhs-image-upload supports at most 9 images.")
        for image_file in args.image_files:
            if not exists(image_file):
                raise FileNotFoundError(f'Could not find image file at {image_file}')
            suffix = Path(image_file).suffix.lower()
            if suffix not in {".jpg", ".jpeg", ".png", ".webp"}:
                parser.error(f"Unsupported image format: {image_file}")
        if args.publish_type == 1 and not args.schedule:
            parser.error("The schedule must must be specified for scheduled publishing.")
    if args.action == 'douyin-image-upload':
        if args.platform != SOCIAL_MEDIA_DOUYIN:
            parser.error("douyin-image-upload only supports platform 'douyin'.")
        if len(args.image_files) == 0:
            parser.error("At least one image file is required.")
        if len(args.image_files) > 9:
            parser.error("douyin-image-upload supports at most 9 images.")
        for image_file in args.image_files:
            if not exists(image_file):
                raise FileNotFoundError(f'Could not find image file at {image_file}')
            suffix = Path(image_file).suffix.lower()
            if suffix not in {".jpg", ".jpeg", ".png", ".webp"}:
                parser.error(f"Unsupported image format: {image_file}")
        if args.publish_type == 1 and not args.schedule:
            parser.error("The schedule must must be specified for scheduled publishing.")

    account_file = Path(BASE_DIR / "cookies" / f"{args.platform}_{args.account_name}.json")
    account_file.parent.mkdir(exist_ok=True)

    # 根据 action 处理不同的逻辑
    if args.action == 'login':
        print(f"Logging in with account {args.account_name} on platform {args.platform}")
        if args.platform == SOCIAL_MEDIA_DOUYIN:
            await douyin_setup(str(account_file), handle=True)
        elif args.platform == SOCIAL_MEDIA_TIKTOK:
            await tiktok_setup(str(account_file), handle=True)
        elif args.platform == SOCIAL_MEDIA_TENCENT:
            await weixin_setup(str(account_file), handle=True)
        elif args.platform == SOCIAL_MEDIA_KUAISHOU:
            await ks_setup(str(account_file), handle=True)
        elif args.platform == SOCIAL_MEDIA_XIAOHONGSHU:
            await xiaohongshu_setup(str(account_file), handle=True)
    elif args.action == 'upload':
        title, tags = get_title_and_hashtags(args.video_file)
        video_file = args.video_file

        if args.publish_type == 0:
            print("Uploading immediately...")
            publish_date = 0
        else:
            print("Scheduling videos...")
            publish_date = parse_schedule(args.schedule)

        if args.platform == SOCIAL_MEDIA_DOUYIN:
            await douyin_setup(account_file, handle=False)
            app = DouYinVideo(title, video_file, tags, publish_date, account_file)
        elif args.platform == SOCIAL_MEDIA_TIKTOK:
            await tiktok_setup(account_file, handle=True)
            app = TiktokVideo(title, video_file, tags, publish_date, account_file)
        elif args.platform == SOCIAL_MEDIA_TENCENT:
            await weixin_setup(account_file, handle=True)
            category = TencentZoneTypes.LIFESTYLE.value  # 标记原创需要否则不需要传
            app = TencentVideo(title, video_file, tags, publish_date, account_file, category)
        elif args.platform == SOCIAL_MEDIA_KUAISHOU:
            await ks_setup(account_file, handle=True)
            app = KSVideo(title, video_file, tags, publish_date, account_file)
        else:
            print("Wrong platform, please check your input")
            exit()

        await app.main()
    elif args.action == 'xhs-image-upload':
        if args.publish_type == 0:
            print("Uploading images immediately...")
            publish_date = 0
        else:
            print("Scheduling image post...")
            publish_date = parse_schedule(args.schedule)

        tags = [tag.strip() for tag in args.tags.split(",") if tag.strip()]
        await xiaohongshu_setup(account_file, handle=False)
        app = XiaoHongShuImage(
            args.title,
            args.image_files,
            tags,
            publish_date,
            account_file,
            args.original_declare,
            args.visibility,
        )
        await app.main()
    elif args.action == 'douyin-image-upload':
        if args.publish_type == 0:
            print("Uploading images immediately...")
            publish_date = 0
        else:
            print("Scheduling image post...")
            publish_date = parse_schedule(args.schedule)

        tags = [tag.strip() for tag in args.tags.split(",") if tag.strip()]
        await douyin_setup(account_file, handle=False)
        app = DouYinImage(
            args.title,
            args.image_files,
            tags,
            publish_date,
            account_file,
            args.body,
        )
        await app.main()


if __name__ == "__main__":
    asyncio.run(main())
