# YouTube Video Note & Flashcard Generator

Streamlit app that takes a YouTube URL, checks the video metadata, and generates study notes and flashcards with Gemini.

## Features

- Paste a YouTube URL in the sidebar
- Scrapes the video title, description, and channel metadata
- Generates notes and flashcards with Gemini
- Shows the embedded video and generated content in Streamlit

## Requirements

- Python 3.12+
- A Gemini API key
- Windows PowerShell, if you want to use the commands below exactly as written

## Setup

Open a terminal in the project folder:

```powershell
cd "c:\Users\BIT\OneDrive\Desktop\shoro ai\youtube_transcripts"
```

Create and activate the virtual environment:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.venv\Scripts\Activate.ps1
```

If `.venv` does not exist yet, create it first:

```powershell
python -m venv .venv
```

Install the dependencies:

```powershell
pip install -r requirements.txt
```

## Configure Gemini

Create a `.env` file in the project root with your API key:

```env
GEMINI_API_KEY=your_api_key_here
```

Optional: set a specific model if you want to override the default.

```env
GEMINI_MODEL=gemini-2.5-flash
```

## Run the app

Start Streamlit:

```powershell
streamlit run app.py
```

Then open the local URL shown in the terminal, usually:

```text
http://localhost:8501
```

## Notes

- The app uses Gemini to generate content.
- The educational keyword filter is advisory, not blocking.
- If you see an API error, confirm your `.env` file is present and the key is valid.

## Troubleshooting

If PowerShell refuses to activate the virtual environment, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```

If Streamlit cannot find packages, make sure the virtual environment is active before running `streamlit run app.py`.