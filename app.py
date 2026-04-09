import streamlit as st
import os
from urllib.parse import urlparse, parse_qs
import re
import traceback
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
GEMINI_MODEL_NAME = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')

# --- YOUR YOUTUBEPROCESSOR CLASS (No changes needed here) ---

class YouTubeProcessor:
    def __init__(self):
        self.educational_keywords = [
            'tutorial', 'learn', 'education', 'course', 'lecture',
            'lesson', 'training', 'guide', 'how to', 'explained',
            'introduction to', 'basics of', 'educational', 'study',
            'learning', 'academy', 'university', 'college', 'school',
            'teaching', 'instructor', 'professor', 'classroom',
            'compiler', 'compiler design', 'algorithm', 'data structure',
            'computer science', 'programming', 'coding', 'software engineering',
            'mathematics', 'engineering', 'exam', 'gate', 'gatehub',
            'three address code', 'triples', 'indirect triples', 'representation'
        ]
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        # Initialize Gemini with the API key
        genai.configure(api_key=GEMINI_API_KEY)
        self.gemini_model_names = [
            GEMINI_MODEL_NAME,
            'gemini-2.5-flash',
            'gemini-2.0-flash',
            'gemini-flash-latest',
        ]

    def extract_video_id(self, url):
        """Extract video ID from various YouTube URL formats."""
        youtube_regex = r'(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})'
        match = re.search(youtube_regex, url)
        
        if match:
            return match.group(1)
            
        parsed_url = urlparse(url)
        if parsed_url.netloc == 'youtu.be':
            return parsed_url.path[1:]
        elif parsed_url.netloc in ('www.youtube.com', 'youtube.com'):
            if parsed_url.path == '/watch':
                return parse_qs(parsed_url.query)['v'][0]
            elif parsed_url.path[:7] == '/embed/':
                return parsed_url.path.split('/')[2]
            elif parsed_url.path[:3] == '/v/':
                return parsed_url.path.split('/')[2]
        
        return None

    def is_valid_youtube_url(self, url):
        """Validate if the URL is a valid YouTube URL."""
        try:
            video_id = self.extract_video_id(url)
            return video_id is not None
        except Exception:
            return False

    def get_video_info(self, video_id):
        """Get video information using web scraping."""
        try:
            url = f'https://www.youtube.com/watch?v={video_id}'
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            title = soup.find('meta', property='og:title')['content']
            description = soup.find('meta', property='og:description')['content']
            channel_tag = soup.find('link', itemprop='name')
            channel = channel_tag['content'] if channel_tag and channel_tag.has_attr('content') else "Unknown Channel"
            
            return {
                'title': title,
                'description': description,
                'channel': channel,
                'url': url
            }
        except Exception as e:
            # We'll let Streamlit handle printing errors
            print(f"Error getting video info: {str(e)}")
            return None

    def is_educational_content(self, video_info):
        """Check if the video content is educational."""
        if not video_info:
            return False

        try:
            title = str(video_info.get('title') or '').lower()
            description = str(video_info.get('description') or '').lower()
            channel = str(video_info.get('channel') or '').lower()
            
            # Print statements will show in your terminal, not in Streamlit
            print("\nAnalyzing video metadata:")
            print(f"Title: {video_info.get('title', 'N/A')}")
            print(f"Channel: {video_info.get('channel', 'N/A')}")
            
            for keyword in self.educational_keywords:
                if keyword in title or keyword in description or keyword in channel:
                    print(f"\nFound educational keyword '{keyword}'")
                    return True

            print("\nNo clear educational indicators found")
            return False

        except Exception as e:
            print(f"\nError checking educational content: {str(e)}")
            return False

    def generate_notes_and_flashcards(self, video_info):
        """Generate study notes and flashcards using Gemini."""
        try:
            prompt = f"""
            Based on this YouTube video information, please:
            1. Generate concise study notes highlighting key concepts
            2. Create 5-10 flashcards in Q&A format
            
            Video Information:
            Title: {video_info['title']}
            Channel: {video_info['channel']}
            Description: {video_info['description']}
            
            Format the output as:
            NOTES:
            - Key point 1
            - Key point 2
            ...
            
            FLASHCARDS:
            Q1: [Question]
            A1: [Answer]
            ...
            """

            last_error = None
            for model_name in self.gemini_model_names:
                try:
                    model = genai.GenerativeModel(model_name)
                    response = model.generate_content(
                        prompt,
                        generation_config={
                            "temperature": 0.7,
                            "max_output_tokens": 2048,
                        },
                    )
                    if getattr(response, 'text', None):
                        return response.text
                    last_error = "Gemini returned an empty response."
                except Exception as model_error:
                    last_error = f"{model_name}: {model_error}"

            raise RuntimeError(f"Unable to generate content with Gemini. Last error: {last_error}")

        except Exception as e:
            # This error will be returned to the Streamlit UI
            print(f"Error details in generate_notes: {traceback.format_exc()}")
            return f"Error generating notes and flashcards: {str(e)}"

    def process_youtube_url(self, url):
        """Main function to process YouTube URL and generate educational content."""
        try:
            if not self.is_valid_youtube_url(url):
                return {"error": "Invalid YouTube URL"}

            video_id = self.extract_video_id(url)
            if not video_id:
                return {"error": "Could not extract video ID"}
            
            print(f"\nProcessing video ID: {video_id}")
            
            video_info = self.get_video_info(video_id)
            if not video_info:
                return {"error": "Could not fetch video information"}

            # Treat the educational check as advisory only so non-lesson videos
            # can still be summarized into notes and flashcards.
            educational = self.is_educational_content(video_info)
            
            content = self.generate_notes_and_flashcards(video_info)
            
            # Check if content itself is an error message
            if "Error generating notes" in content:
                 return {"error": content}
            
            return {
                "success": True,
                "video_id": video_id,
                "title": video_info['title'],
                "educational": educational,
                "content": content
            }

        except Exception as e:
            print("Error details:", traceback.format_exc())
            return {"error": str(e)}

# --- NEW STREAMLIT APP CODE ---

# Set the page title and layout
st.set_page_config(page_title="YT Note Generator", layout="wide")
st.title("YouTube Video Note & Flashcard Generator 📼🧠")

# Check if the API key is available
if not GEMINI_API_KEY:
    st.error("GEMINI_API_KEY not found! Please add it to your .env file.")
else:
    st.caption(f"Using Gemini model: {GEMINI_MODEL_NAME}")
    # Use st.cache_resource to initialize the processor only once
    @st.cache_resource
    def init_processor():
        return YouTubeProcessor()
        
    processor = init_processor()

    # --- Sidebar for Inputs ---
    st.sidebar.header("Controls")
    url = st.sidebar.text_input("Enter YouTube URL:", placeholder="https.youtu.be/...")

    if st.sidebar.button("Generate Notes", type="primary"):
        if not url:
            st.sidebar.warning("Please enter a URL first.")
        else:
            # --- Main Content Area for Output ---
            with st.spinner("Processing video... This might take a moment. ⏳"):
                try:
                    # Run the processing
                    result = processor.process_youtube_url(url)
                    
                    if "error" in result:
                        st.error(f"Error: {result['error']}")
                    else:
                        st.subheader(f"Video Title: {result['title']}")
                        if not result.get("educational", True):
                            st.warning("This video did not match the educational keyword filter, but notes were generated anyway.")
                        # Embed the YouTube video
                        st.video(url) 
                        
                        st.markdown("---")
                        st.header("Generated Content 🚀")
                        # Use markdown to render the notes and flashcards
                        st.markdown(result['content']) 
                        
                except Exception as e:
                    st.error("An unexpected error occurred:")
                    st.exception(e) # Display the full exception