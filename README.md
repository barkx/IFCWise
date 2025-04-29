# IFCWISE – Interactive IFC Assistant

**IFCWISE** is a Streamlit-based app that allows you to upload, explore, filter, and modify IFC (Industry Foundation Classes) models using natural language through LLMs like ChatGPT, Gemini, or Claude.

---

## 🛠️ Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/IFCWISE.git
cd IFCWISE
```

### 2. Create and Activate a Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate on Windows
venv\Scripts\activate

# Activate on macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies

Make sure you have Python 3.8 or higher installed:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Launch the App

```bash
streamlit run Home.py
```

---

## 📁 Project Structure

```
.
├── Home.py               # Main app entry point
├── sidebar.py            # Shared sidebar navigation
├── icon.png              # App icon
├── requirements.txt      # Python dependencies
├── pages/                # Multi-step Streamlit pages
├── demo_ifc/             # Sample IFC files
├── demo_images/          # Preview images for demo projects
```

---

## 🌐 LLM Integration

- Supports ChatGPT (OpenAI), Claude (Anthropic), Gemini (Google), and others.
- Model data is chunked and streamed into the LLM thread for processing.
- You must provide your own API key for your selected LLM provider.

---

## 📌 Notes

- IFC models are parsed using `ifcopenshell`.
- The full IFC model is analyzed and filtered client-side before being sent to the assistant.

---

## 📷 Demo Projects Included

- Three sample IFC files (`Small`, `Medium`, `Large`) with images are available under `demo_ifc/` and `demo_images/`.

---

## 🧾 License

MIT License – feel free to use and extend.

