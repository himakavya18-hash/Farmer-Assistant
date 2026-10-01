import os
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.utils import secure_filename
from crop_recommendation import recommend_crops
from weather import get_weather

try:
    from groq import Groq
except ImportError:
    Groq = None


load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "change-this-secret-key")
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB
app.config["UPLOAD_FOLDER"] = Path(app.static_folder) / "uploads"
ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}


def add_history(sender, message):
    history = session.get("history", [])
    history.append({"sender": sender, "message": message})
    session["history"] = history[-20:]


def ask_advisor(question, image_name=None):
    """Return agricultural advice, with a useful local fallback when AI is unavailable."""
    api_key = os.getenv("GROQ_API_KEY")
    if Groq and api_key:
        try:
            context = f" An image named '{image_name}' was uploaded, but you cannot inspect its contents." if image_name else ""
            response = Groq(api_key=api_key).chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an agricultural advisor. Give concise, practical, safety-conscious advice in bullet points. Do not claim to diagnose an image you cannot see.",
                    },
                    {"role": "user", "content": f"Farmer question: {question}.{context}"},
                ],
                temperature=0.4,
                max_tokens=500,
            )
            return response.choices[0].message.content
        except Exception:
            pass

    return (
        "AI advice is not configured yet. Add a valid GROQ_API_KEY to .env and restart the server. "
        "Until then, record the crop, growth stage, symptoms, irrigation schedule, and recent fertilizer or pesticide use before consulting a local agriculture officer."
    )


@app.route("/")
def home():
    return render_template(
        "index.html",
        history=session.get("history", []),
        uploaded_image=session.get("uploaded_image"),
        weather=session.get("weather"),
        recommendations=session.get("recommendations"),
    )


@app.post("/recommend-crops")
def recommend_crops_route():
    season = request.form.get("season", "")
    soil_type = request.form.get("soil_type", "")
    water_level = request.form.get("water_level", "")
    try:
        session["recommendations"] = {
            "season": season.title(),
            "soil_type": soil_type.title(),
            "water_level": water_level.title(),
            "crops": recommend_crops(season, soil_type, water_level),
        }
    except ValueError as error:
        flash(str(error), "warning")
    return redirect(url_for("home") + "#recommend-crops")


@app.post("/weather")
def weather():
    try:
        session["weather"] = get_weather(request.form.get("location", ""))
    except ValueError as error:
        flash(str(error), "warning")
    return redirect(url_for("home") + "#weather")


@app.post("/ask")
def ask_question():
    question = request.form.get("question", "").strip()
    if not question:
        flash("Please enter a question before asking the advisor.", "warning")
        return redirect(url_for("home") + "#ask")

    add_history("user", question)
    add_history("advisor", ask_advisor(question, session.get("uploaded_image")))
    return redirect(url_for("home") + "#history")


@app.post("/upload")
def upload_image():
    image = request.files.get("image")
    if not image or not image.filename:
        flash("Choose an image file before uploading.", "warning")
        return redirect(url_for("home") + "#upload")

    extension = image.filename.rsplit(".", 1)[-1].lower() if "." in image.filename else ""
    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        flash("Please upload a PNG, JPG, JPEG, or WEBP image.", "warning")
        return redirect(url_for("home") + "#upload")

    upload_folder = Path(app.config["UPLOAD_FOLDER"])
    upload_folder.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid4().hex}_{secure_filename(image.filename)}"
    image.save(upload_folder / filename)
    session["uploaded_image"] = filename
    add_history("user", f"Uploaded image: {secure_filename(image.filename)}")
    flash("Image uploaded. Now describe the crop and symptoms in your question.", "success")
    return redirect(url_for("home") + "#ask")


@app.post("/history/clear")
def clear_history():
    session.pop("history", None)
    session.pop("uploaded_image", None)
    flash("Chat history cleared.", "success")
    return redirect(url_for("home") + "#history")


@app.errorhandler(413)
def file_too_large(_error):
    flash("Image is too large. The maximum upload size is 5 MB.", "warning")
    return redirect(url_for("home") + "#upload")


if __name__ == "__main__":
    app.run(debug=True)
