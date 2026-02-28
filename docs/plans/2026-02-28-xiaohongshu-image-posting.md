# XiaoHongShu Image Posting Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add first-version XiaoHongShu multi-image publishing (`视频/图文` mode) with scheduling support, local upload + material library selection, and image-only validations.

**Architecture:** Keep the existing `/postVideo` contract and add `contentType` (`video` or `image`). Frontend `PublishCenter` controls upload/type validation and sends unified payload. Backend routes XiaoHongShu image mode to a dedicated uploader flow that uploads 1-9 images as one post and reuses current publish/schedule logic.

**Tech Stack:** Vue 3 + Element Plus, Flask, Playwright, Python unittest.

---

### Task 1: Add request validation helpers with tests

**Files:**
- Create: `myUtils/publish_payload.py`
- Create: `tests/test_publish_payload.py`

**Step 1: Write failing tests for content type and file type rules**
- Assert `contentType` defaults to `video`.
- Assert XiaoHongShu image mode rejects non-image files.
- Assert XiaoHongShu image mode enforces max 9 files.

**Step 2: Run tests to verify failures**
- Run: `python3 -m unittest tests/test_publish_payload.py`

**Step 3: Implement minimal helper functions**
- Add content type normalizer.
- Add extension-based image/video checks.
- Add XiaoHongShu image mode validator.

**Step 4: Run tests to verify pass**
- Run: `python3 -m unittest tests/test_publish_payload.py`

### Task 2: Wire backend `/postVideo` for image mode

**Files:**
- Modify: `sau_backend.py`
- Modify: `myUtils/postVideo.py`

**Step 1: Add failing test for backend helper integration (if feasible)**
- Keep validation-first behavior in helper unit tests if endpoint integration test is heavy.

**Step 2: Implement backend wiring**
- Parse `contentType` from request JSON.
- Validate payload for XiaoHongShu image mode.
- Pass `contentType` into `post_video_xhs`.

**Step 3: Verify behavior**
- Run helper tests.
- Smoke-check existing video branch remains unchanged.

### Task 3: Add XiaoHongShu image uploader flow

**Files:**
- Modify: `uploader/xiaohongshu_uploader/main.py`

**Step 1: Add minimal uploader class for image posts**
- Navigate to XiaoHongShu image publish page.
- Upload multiple images in one post.
- Fill title/tags.
- Support schedule publish.

**Step 2: Integrate with `post_video_xhs`**
- In image mode, create one post per account from selected images.
- In video mode, keep existing one-video-per-file behavior.

**Step 3: Smoke verify**
- Run syntax checks and backend startup sanity (`python -m py_compile` targeted files).

### Task 4: Add publish type and image flow in frontend

**Files:**
- Modify: `sau_frontend/src/views/PublishCenter.vue`

**Step 1: Add publish type UI**
- `视频/图文` radio in each tab.
- Default `视频`.

**Step 2: Add upload + material filtering rules**
- In `图文` mode accept image formats only.
- In `视频` mode accept video formats only.
- Material library list filters by current mode.
- Image mode max 9 files; prevent mixed types.

**Step 3: Update publish payload and validations**
- Add `contentType` in payload.
- Require XiaoHongShu platform in image mode for v1.
- Keep schedule payload reusable.

**Step 4: Verify frontend build**
- Run: `cd sau_frontend && npm run build`

### Task 5: End-to-end verification and notes

**Files:**
- Modify: `README.md` (optional short note, if needed)

**Step 1: Verify backend/unit tests + frontend build**
- `python3 -m unittest tests/test_publish_payload.py`
- `cd sau_frontend && npm run build`

**Step 2: Docker smoke**
- Rebuild and run container if needed.
- Confirm no regression for existing video publish request shape.
