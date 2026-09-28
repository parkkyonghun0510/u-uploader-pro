#!/usr/bin/env python3
"""YouTube Uploader Pro - Enhanced CLI entry point."""
import argparse
import json
import sys
import os
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(
        prog='yt-upload',
        description='Upload videos to YouTube via Selenium - Pro Edition',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''Examples:
  yt-upload --login                      # Interactive YouTube sign-in (default profile)
  yt-upload --login --profile channel_1  # Interactive sign-in for specific channel profile
  yt-upload --video video.mp4
  yt-upload --video video.mp4 --meta metadata.json --thumbnail thumb.png
  yt-upload --video video.mp4 --profile my_profile
  yt-upload --web                        # Start web dashboard
  yt-upload --web --port 8080            # Start web dashboard on port 8080
  yt-upload --status                     # Show queue status
  yt-upload --queue                      # Manage upload queue
        '''
    )
    parser.add_argument("--login", action='store_true', help='Launch interactive Firefox session to log in to YouTube and save profile cookies')
    parser.add_argument("--video", help='Path to the video file')
    parser.add_argument("-t", "--thumbnail", help='Path to the thumbnail image')
    parser.add_argument("--meta", help='Path to the JSON file with metadata')
    parser.add_argument("--profile", help='Path or name of the Firefox profile (e.g. channel_1 or ./profiles/channel_1)')
    parser.add_argument("--web", action='store_true', help='Start the web dashboard')
    parser.add_argument("--port", type=int, default=8080, help='Port for web dashboard (default: 8080)')
    parser.add_argument("--status", action='store_true', help='Show queue status')

    args = parser.parse_args()

    def resolve_profile_path(profile_name):
        if not profile_name:
            return os.path.abspath(os.path.join(os.getcwd(), "profile"))
        if os.path.isabs(profile_name):
            return profile_name
        # Check ./profiles/<profile_name>
        candidate = os.path.abspath(os.path.join(os.getcwd(), "profiles", profile_name))
        return candidate

    if args.login:
        from youtube_uploader_selenium import YouTubeUploader
        target_profile = resolve_profile_path(args.profile)
        print(f"🚀 Initializing YouTube interactive login session")
        print(f"📁 Profile location: {target_profile}")
        uploader = YouTubeUploader(profile_path=target_profile)
        try:
            success = uploader.login()
            if success:
                print(f"✅ Login complete! Session cookies saved to: {target_profile}")
                print(f"👉 You can now run automated uploads with --profile {args.profile or 'default'}")
            else:
                print("❌ Login could not be completed.")
        except Exception as e:
            print(f"❌ Error during login: {e}")
            sys.exit(1)
        return

    if args.web:
        from app import start_web_app
        print(f"🚀 YouTube Uploader Pro Dashboard")
        print(f"📡 Opening http://localhost:{args.port}")
        print(f"📋 API docs available at http://localhost:{args.port}/api/jobs")
        start_web_app(port=args.port)
        return

    if args.status:
        from youtube_uploader_selenium.queue import UploadQueue
        queue = UploadQueue()
        print(json.dumps(queue.get_queue_stats(), indent=2))
        return

    if not args.video:
        parser.error("--video is required (or use --login / --web)")

    from youtube_uploader_selenium import YouTubeUploader, UploadJob, UploadStatus

    resolved_profile = resolve_profile_path(args.profile) if args.profile else None

    job = UploadJob(
        video_path=args.video,
        metadata_path=args.meta,
        thumbnail_path=args.thumbnail,
        profile_path=resolved_profile
    )

    uploader = YouTubeUploader(args.video, args.meta, args.thumbnail, resolved_profile)
    print(f"📤 Uploading: {args.video}")
    if args.meta:
        print(f"📄 Metadata: {args.meta}")
    if args.thumbnail:
        print(f"🖼️  Thumbnail: {args.thumbnail}")
    print(f"📝 Job ID: {job.job_id}")

    try:
        was_uploaded, video_id = uploader.upload()
        if was_uploaded:
            print(f"✅ Upload successful! Video ID: {video_id}")
        else:
            print("❌ Upload failed")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
