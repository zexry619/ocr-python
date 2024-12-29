from flask import Flask, request, render_template
from paddleocr import PaddleOCR
import os
import spacy

# Inisialisasi Flask app
app = Flask(__name__)

# Konfigurasi folder upload
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Inisialisasi PaddleOCR dan spaCy NLP
ocr = PaddleOCR(use_angle_cls=True, lang='en')
nlp = spacy.load("en_core_web_sm")  # Model spaCy bahasa Inggris

# Fungsi untuk membersihkan teks hasil OCR
def clean_text(text):
    text = text.replace("…", "...")
    text = text.replace("ﬁ", "fi")
    return text

# Fungsi untuk memproses gambar dan mengstrukturkan hasil OCR
@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # Cek jika ada file yang diunggah
        if 'file' not in request.files:
            return render_template('upload.html', error="Tidak ada file yang diunggah")
        file = request.files['file']
        if file.filename == '':
            return render_template('upload.html', error="Nama file kosong")
        if file:
            # Simpan file ke folder upload
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)

            # Proses gambar dengan PaddleOCR
            result = ocr.ocr(file_path, cls=True)

            # Gabungkan teks hasil OCR
            raw_text = "\n".join([line[1][0] for line in result[0]])

            # Gunakan spaCy untuk memproses teks
            doc = nlp(raw_text)

            # Strukturkan teks menjadi paragraf berdasarkan entitas
            structured_text = []
            current_paragraph = []
            for sentence in doc.sents:
                current_paragraph.append(sentence.text)
                # Tambahkan pemisah paragraf jika bertemu entitas tertentu
                if any(ent.label_ in ["DATE", "MONEY", "ORG"] for ent in sentence.ents) or len(current_paragraph) > 3:
                    structured_text.append(clean_text(" ".join(current_paragraph)))
                    current_paragraph = []

            if current_paragraph:
                structured_text.append(clean_text(" ".join(current_paragraph)))

            # Hapus file setelah diproses
            os.remove(file_path)

            # Tampilkan hasil OCR dan NLP
            return render_template('result.html', result=structured_text)

    return render_template('upload.html')

if __name__ == '__main__':
    app.run(debug=True)
