# Recapify
Recapify is a summarization chatbot for group chats, using OpenAI’s API and various NLP tools to analyze and summarize conversations. This project aims to facilitate chat summaries with performance evaluation and user-defined preferences.

## Features
- **Text Summarization**: Generates summaries of text-based chat content.
- **Multi-Modal Analysis**: Includes support for analyzing multimedia messages.
- **Customizable**: Allows users to set language preferences and configure summary length.

## Requirements

Ensure that your environment meets the following dependencies. You can set up the environment by installing the packages listed in `requirements.txt`.

### Major Dependencies:
- **Python 3.x**: Ensure Python 3.7 or higher is installed.
- **spaCy**: For keyword extraction.
- **OpenAI API**: Used for summarization.
- **ROUGE** and **BERTScore**: For evaluating summarization quality.
- **psutil** and **tracemalloc**: For monitoring performance.
- **Quart**: For managing the server.

### Additional Files:
Your project includes several Python scripts:
- `main.py`: Entry point for starting the application.
- `webhook.py`: Manages the connection with Telegram and routes incoming messages.
- `database.py`: Manages database operations.
- `session_manager.py` and `user_session.py`: Handle user sessions.
- `nlp.py`: Conducts natural language processing tasks.

## Installation

1. **Clone the repository**:
    ```bash
    git clone git@github.com:SeanCampailla/Recapify.git
    cd Recapify
    ```

2. **Install Dependencies**:
    Ensure all required packages are installed.
    ```bash
    pip install -r requirements.txt
    ```

3. **Set Up Environment Variables**:
    Configure necessary environment variables by creating a `.env` file in the root directory or by adding them directly in `config.py`. 

    Required keys include:
    - `API_ID`: Your unique Telegram API ID
    - `API_HASH`: Your unique Telegram API hash
    - `BOT_TOKEN`: Token generated for your Telegram bot
    - `OPENAI_API_KEY`: API key for OpenAI to access GPT models
    - `NGROK_URL`: URL provided by Ngrok for local development (optional)

    Example `.env` file:
    ```plaintext
    API_ID=your_telegram_api_id
    API_HASH=your_telegram_api_hash
    BOT_TOKEN=your_telegram_bot_token
    OPENAI_API_KEY=your_openai_api_key
    NGROK_URL=your_ngrok_url  # Optional for local testing
    ```

4. **Download spaCy Model**:
    ```bash
    python -m spacy download it_core_news_sm
    ```

## Running the Project

To start the chatbot server, execute:
```bash
python main.py

