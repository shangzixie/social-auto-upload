import unittest

from myUtils.publish_payload import (
    normalize_content_type,
    validate_xiaohongshu_publish_payload,
)


class PublishPayloadTests(unittest.TestCase):
    def test_normalize_content_type_defaults_to_video(self):
        self.assertEqual(normalize_content_type(None), "video")
        self.assertEqual(normalize_content_type(""), "video")

    def test_normalize_content_type_accepts_image(self):
        self.assertEqual(normalize_content_type("image"), "image")
        self.assertEqual(normalize_content_type("IMAGE"), "image")

    def test_validate_xiaohongshu_image_rejects_non_image(self):
        with self.assertRaises(ValueError):
            validate_xiaohongshu_publish_payload(
                content_type="image",
                file_list=["demo.mp4"],
            )

    def test_validate_xiaohongshu_image_limit(self):
        files = [f"img_{i}.jpg" for i in range(10)]
        with self.assertRaises(ValueError):
            validate_xiaohongshu_publish_payload(
                content_type="image",
                file_list=files,
            )

    def test_validate_xiaohongshu_image_accepts_png(self):
        validate_xiaohongshu_publish_payload(
            content_type="image",
            file_list=["a.png", "b.jpeg", "c.webp"],
        )


if __name__ == "__main__":
    unittest.main()
