from flask import Flask, render_template, request, g, send_file, url_for
import sqlite3
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle

app = Flask(__name__, template_folder="templates")
DATABASE = "prediction_db.db"

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def extract_sequences(fasta_input):
    """ Extracts sequences from FASTA input, ensuring uppercase and removing extra spaces/newlines. """
    sequences = []
    current_seq = ""

    lines = fasta_input.strip().split("\n")

    for line in lines:
        line = line.strip()
        if line.startswith(">"):  # Header line, start new sequence
            if current_seq:
                sequences.append(current_seq.replace(" ", "").upper())  # Store previous sequence
            current_seq = ""  # Reset for the next sequence
        else:
            current_seq += line.replace(" ", "").strip().upper()  # Remove spaces

    if current_seq:
        sequences.append(current_seq.replace(" ", "").upper())  # Store last sequence

    return sequences

@app.route("/", methods=["GET", "POST"])
def index():
    results = []  # Initialize an empty list to hold the results

    if request.method == "POST":
        input_text = request.form["sequence"].strip()
        sequences = extract_sequences(input_text)  # Extract sequences properly

        db = get_db()
        cursor = db.cursor()

        for seq in sequences:
            seq = seq.strip().upper()  # Ensure trimming and uppercase

            cursor.execute("SELECT Sequence, Prediction_Score, Class FROM seq_prediction WHERE Sequence = ?", (seq,))
            row = cursor.fetchone()

            if row:
                results.append({
                    "sequence": row["Sequence"],
                    "prediction_score": row["Prediction_Score"],
                    "classification": row["Class"]
                })
            else:
                results.append({"sequence": seq, "error": "Sequence not found in database."})

        # After processing the POST request, render 'results.html' with the results
        return render_template("results.html", results=results)

    # Handle the GET request, render the index.html form
    return render_template("index.html")



@app.route("/researcher")
def researcher():
    return render_template("researcher.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/dataset")
def dataset():
    return render_template("dataset.html")

@app.route("/algorithm")
def algorithm():
    return render_template("algorithm.html")

@app.route("/index")
def Home():
    return render_template("index.html")


@app.route("/download_pdf", methods=["POST"])
def download_pdf():
    """ Generate and return a PDF of the results. """
    results = request.form.getlist("results[]")

    buffer = BytesIO()

    # Create a PDF document
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []

    # Prepare the data for the table
    table_data = [
        ["Sequence", "Prediction Score", "Classification"]  # Header row
    ]

    for result in results:
        sequence, prediction_score, classification = result.split("|")
        table_data.append([sequence, prediction_score, classification])

    # Create the table with the data
    table = Table(table_data)

    # Apply a TableStyle to add borders and formatting
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),  # Header background color
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),  # Header text color
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),  # Align text to center
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),  # Use Helvetica font
        ('FONTSIZE', (0, 0), (-1, -1), 10),  # Set font size
        ('GRID', (0, 0), (-1, -1), 1, colors.black),  # Add borders to all cells
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),  # Add padding to header row
        ('TOPPADDING', (0, 0), (-1, -1), 8),  # Padding for the other rows
        ('LEFTPADDING', (0, 0), (-1, -1), 8),  # Padding for the other rows
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),  # Padding for the other rows
    ]))

    # Add the table to the PDF elements
    elements.append(table)

    # Build the PDF
    doc.build(elements)

    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name="prediction_results.pdf", mimetype="application/pdf")



if __name__ == "__main__":
    app.run(debug=True)
