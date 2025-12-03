import os
import tempfile
from flask import Flask, request, render_template, send_file, flash, redirect, url_for
try:
    import yt_dlp
except Exception as e:
    raise RuntimeError(
        "yt_dlp is not installed. Install it into the project's venv:\n"
        "C:/Users/virat/Downloads/global_link_downloader/.venv/Scripts/python.exe -m pip install yt-dlp"
    ) from e
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "change_this_for_prod")

DOWNLOAD_DIR = os.path.join(tempfile.gettempdir(), "gld_downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

YTDLP_OPTS_BASE = {
    "outtmpl": os.path.join(DOWNLOAD_DIR, "%(title).200s.%(ext)s"),
    "noplaylist": True,
    "quiet": True,
}

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        url = request.form.get("url", "").strip()
        if not url:
            flash("Please enter a video URL.", "error")
            return redirect(url_for("index"))

        audio_only = request.form.get("audio_only") == "on"

        tmp_dir = tempfile.mkdtemp(prefix="gld_")
        opts = dict(YTDLP_OPTS_BASE)
        opts["outtmpl"] = os.path.join(tmp_dir, "%(title).200s.%(ext)s")

        if audio_only:
            opts.update({
                "format": "bestaudio/best",
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],
            })

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)

                if "requested_downloads" in info and info["requested_downloads"]:
                    path = info["requested_downloads"][0].get("filepath")
                else:
                    ext = info.get("ext") or "mp4"
                    title = info.get("title") or "video"
                    fname = secure_filename(f"{title}.{ext}")[:255]
                    path = os.path.join(tmp_dir, fname)

                if not path or not os.path.exists(path):
                    files = os.listdir(tmp_dir)
                    if files:
                        path = os.path.join(tmp_dir, files[0])
                    else:
                        raise RuntimeError("Downloaded file not found.")

            return send_file(path, as_attachment=True)

        except Exception as e:
            flash(f"An error occurred: {e}", "error")
            return redirect(url_for("index"))

    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
