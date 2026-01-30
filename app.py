from flask import Flask, request, jsonify, send_file, render_template_string
import yt_dlp
import os
import time

app = Flask(__name__)

# ==========================================
# 🎨 واجهة التطبيق
# ==========================================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pro Video Hunter</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        :root { --primary: #FF0000; --dark: #181818; --gray: #202020; --text: #ffffff; }
        body { font-family: sans-serif; background-color: #121212; color: var(--text); margin: 0; padding: 20px; text-align: center; }
        .container { max-width: 800px; margin: 0 auto; }
        h1 i { color: var(--primary); }
        .search-box { position: relative; max-width: 600px; margin: 0 auto 40px auto; }
        input[type="text"] { width: 100%; padding: 15px 20px; border-radius: 25px; border: none; background-color: var(--dark); color: white; font-size: 18px; direction: auto; }
        .search-btn { position: absolute; right: 10px; top: 50%; transform: translateY(-50%); background: none; border: none; color: gray; font-size: 20px; cursor: pointer; }
        #results-area { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; }
        .video-card { background-color: var(--gray); border-radius: 10px; overflow: hidden; text-align: left; }
        .thumbnail { width: 100%; height: 160px; object-fit: cover; }
        .info { padding: 10px; }
        .title { font-size: 14px; font-weight: bold; margin-bottom: 10px; height: 34px; overflow: hidden; }
        .download-btn { width: 100%; background-color: #333; color: white; border: none; padding: 8px; border-radius: 5px; cursor: pointer; }
        .download-btn:hover { background-color: var(--primary); }
        .loader { display: none; margin: 20px auto; border: 4px solid #333; border-top: 4px solid var(--primary); border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
</head>
<body>
<div class="container">
    <h1><i class="fab fa-youtube"></i> Video Hunter</h1>
    <div class="search-box">
        <input type="text" id="searchInput" placeholder="Search matches...">
        <button class="search-btn" onclick="searchVideos()"><i class="fas fa-search"></i></button>
    </div>
    <div id="loader" class="loader"></div>
    <div id="status-msg"></div>
    <div id="results-area"></div>
</div>
<script>
    async function searchVideos() {
        const query = document.getElementById('searchInput').value;
        if (!query) return;
        document.getElementById('results-area').innerHTML = '';
        document.getElementById('loader').style.display = 'block';
        document.getElementById('status-msg').innerText = 'Searching...';
        
        try {
            const response = await fetch('/api/search', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({query: query})
            });
            const data = await response.json();
            document.getElementById('loader').style.display = 'none';
            document.getElementById('status-msg').innerText = '';
            
            data.forEach(video => {
                document.getElementById('results-area').innerHTML += `
                    <div class="video-card">
                        <img src="${video.thumbnail}" class="thumbnail">
                        <div class="info">
                            <div class="title">${video.title}</div>
                            <button class="download-btn" onclick="downloadVideo('${video.url}')">Download</button>
                        </div>
                    </div>`;
            });
        } catch (err) { document.getElementById('status-msg').innerText = 'Error'; }
    }

    function downloadVideo(url) {
        document.getElementById('status-msg').innerText = 'Downloading... Please wait';
        window.location.href = `/download?url=${encodeURIComponent(url)}`;
    }
</script>
</body>
</html>
"""

# ==========================================
# 🐍 منطق السيرفر
# ==========================================
@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/search', methods=['POST'])
def api_search():
    data = request.get_json()
    ydl_opts = {'default_search': 'ytsearch6', 'quiet': True, 'extract_flat': True, 'no_warnings': True}
    results = []
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(data.get('query', ''), download=False)
            if 'entries' in info:
                for v in info['entries']:
                    results.append({
                        'title': v.get('title'),
                        'url': v.get('url'),
                        'thumbnail': v.get('thumbnails')[-1]['url'] if v.get('thumbnails') else ''
                    })
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/download')
def download_route():
    video_url = request.args.get('url')
    # استخدام مجلد مؤقت آمن في Render
    download_dir = '/tmp'
    filename = f"video_{int(time.time())}.mp4"
    save_path = os.path.join(download_dir, filename)
    
    ydl_opts = {'format': 'mp4/best[height<=480]', 'outtmpl': save_path, 'quiet': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        return send_file(save_path, as_attachment=True, download_name="Highlight.mp4")
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
