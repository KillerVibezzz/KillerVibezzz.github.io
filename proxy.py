from flask import Flask, request, render_template_string
import yt_dlp

app = Flask(__name__)

YOUTUBE_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YouTube Search</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            padding: 0;
            background-color: #f8f9fa;
            text-align: center;
        }
        h3 {
            margin-top: 20px;
        }
        form {
            margin-bottom: 20px;
        }
        input[type="text"] {
            padding: 10px;
            width: 60%;
            border: 2px solid #ddd;
            border-radius: 5px;
            font-size: 16px;
        }
        button {
            padding: 10px 15px;
            font-size: 16px;
            border: none;
            background-color: #007bff;
            color: white;
            border-radius: 5px;
            cursor: pointer;
        }
        button:hover {
            background-color: #0056b3;
        }
        .video-grid {
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 15px;
            padding: 10px;
        }
        .video-item {
            background: white;
            padding: 10px;
            border-radius: 10px;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
            text-align: center;
            width: 250px;
        }
        .video-item img {
            max-width: 100%;
            border-radius: 8px;
        }
        .video-item a {
            text-decoration: none;
            font-weight: bold;
            color: #333;
            display: block;
            margin-top: 8px;
        }
        .video-item a:hover {
            color: #007bff;
        }
        .channel-name {
            font-size: 14px;
            color: #555;
        }
        video {
            margin-top: 20px;
            border-radius: 10px;
        }
    </style>
</head>
<body>

<form action="/search" method="get">
    <input type="text" name="query" placeholder="Search for YouTube videos" required>
    <button type="submit">Search</button>
</form>

{% if recommended_videos %}
    <h3>Recommended Videos:</h3>
    <div class="video-grid">
        {% for video in recommended_videos %}
            <div class="video-item">
                <a href="/watch?url={{ video.url }}" target="_blank">
                    <img src="{{ video.thumbnail }}" alt="Thumbnail">
                </a>
                <a href="/watch?url={{ video.url }}" target="_blank">{{ video.title }}</a>
                <div class="channel-name">{{ video.channel }}</div>
            </div>
        {% endfor %}
    </div>
{% endif %}

{% if videos %}
    <h3>Search Results:</h3>
    <div class="video-grid">
        {% for video in videos %}
            <div class="video-item">
                <a href="/watch?url={{ video.url }}" target="_blank">
                    <img src="{{ video.thumbnail }}" alt="Thumbnail">
                </a>
                <a href="/watch?url={{ video.url }}" target="_blank">{{ video.title }}</a>
                <div class="channel-name">{{ video.channel }}</div>
            </div>
        {% endfor %}
    </div>
{% elif query %}
    <p>No results found for "{{ query }}".</p>
{% endif %}

{% if video_url %}
    <video controls autoplay width="650">
        <source src="{{ video_url }}" type="video/mp4">
        Your browser does not support the video tag.
    </video>
{% endif %}

</body>
</html>
'''

@app.route('/')
def home():
    try:
        # Set default search term for recommendations
        recommendations_query = " "
        
        ydl_opts = {
            "format": "best",
            "quiet": True,
            "extract_flat": True,
            "noplaylist": False,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            search_query = f"ytsearch100:{recommendations_query}"
            result = ydl.extract_info(search_query, download=False)

            recommended_videos = []

            if 'entries' in result:
                for entry in result['entries']:
                    if entry.get('_type') == 'video' or entry.get('url', '').startswith('https://www.youtube.com/watch?v='):
                        recommended_videos.append({
                            "url": entry.get('url'),
                            "title": entry.get('title', 'No Title'),
                            "thumbnail": entry.get('thumbnails', [{}])[-1].get('url', ''),  # Get highest quality thumbnail
                            "channel": entry.get('channel', '')  # Channel name beside the link
                        })
                    if len(recommended_videos) >= 6:  # Show a limited number of recommended videos
                        break

        return render_template_string(YOUTUBE_TEMPLATE, recommended_videos=recommended_videos)

    except Exception as e:
        return f"Error fetching recommended videos: {str(e)}", 500

@app.route('/search')
def search():
    query = request.args.get("query")
    if not query:
        return "No query provided", 400

    try:
        ydl_opts = {
            "format": "best",
            "quiet": True,
            "extract_flat": True,
            "noplaylist": False,
        }

        search_query = f"ytsearch100:{query}"

        print(f"Performing search with query: {search_query}")

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(search_query, download=False)

            videos = []
            
            if 'entries' in result:
                for entry in result['entries']:
                    print(f"Processing entry: {entry}")

                    if entry.get('_type') == 'video' or entry.get('url', '').startswith('https://www.youtube.com/watch?v='):
                        videos.append({
                            "url": entry.get('url'),
                            "title": entry.get('title', 'No Title'),
                            "thumbnail": entry.get('thumbnails', [{}])[-1].get('url', ''),  # Get highest quality thumbnail
                            "channel": entry.get('channel', '')  # Channel name beside the link
                        })

                        if len(videos) >= 100:
                            break

            print(f"Found {len(videos)} valid videos.")

        if not videos:
            return render_template_string(YOUTUBE_TEMPLATE, query=query, videos=None)

        return render_template_string(YOUTUBE_TEMPLATE, videos=videos, query=query)

    except Exception as e:
        return f"Error searching for videos: {str(e)}", 500

@app.route('/watch')
def watch():
    url = request.args.get("url")
    if not url:
        return "No URL provided", 400

    try:
        ydl_opts = {"format": "best"}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            video_url = info["url"]
        
        return render_template_string(YOUTUBE_TEMPLATE, video_url=video_url)
    
    except Exception as e:
        return f"Error fetching video: {str(e)}", 500

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
<VirtualHost *:80>
    ServerName yourvideosnow.com
    ProxyPass / http://127.0.0.1:5000/
    ProxyPassReverse / http://127.0.0.1:5000/
</VirtualHost>

