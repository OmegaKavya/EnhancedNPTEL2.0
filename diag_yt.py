import youtube_transcript_api
from youtube_transcript_api import YouTubeTranscriptApi
import inspect

print(f"Module attributes: {dir(youtube_transcript_api)}")
print(f"Class attributes: {dir(YouTubeTranscriptApi)}")

try:
    target = "list_transcripts"
    if hasattr(YouTubeTranscriptApi, target):
        print(f"Found {target}")
    else:
        print(f"{target} NOT found")
except Exception as e:
    print(f"Error checking: {e}")
