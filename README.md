![Three files](img/make_3_files.png)

# Experimental

Use at your own risk!

# Privacy

The app talks with OpenAI, meaning if you for example `cat secret.txt` and the continue talking with the AI, OpenAI will get the contents of `secret.txt`

# Project Setup Instructions

## Prerequisites
Before you begin, ensure you have met the following requirements:

- You have installed [Python](https://www.python.org/downloads/) (version compatible with the project).
- You have [Git](https://git-scm.com/downloads) installed on your machine.

## Cloning the Repository
To clone the repository, run:

```bash
git clone <repository-url>
cd <repository-directory>
```

## Setting Up a Virtual Environment
It is highly recommended to use a virtual environment to manage dependencies:

1. Create a virtual environment:
   ```bash
   python -m venv venv
   ```
2. Activate the virtual environment:
   - On Windows:
     ```bash
     .\venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

## Installing Dependencies
Once the virtual environment is activated, install the required dependencies:

```bash
pip install -r requirements.txt
```

## Configuring the API key

Make a copy of `.env_sample` into `.env` and fill in your OpenAI API key in the `.env` file

## Running the Application
You can now run the application using:

```bash
python app.py
```

## Known issues

- It doesn't strip away markdown always
- Sometimes it creates a new python function (under `./gen`) instead of carrying out the command

## Additional Notes
- Make sure to configure any necessary settings in `config.ini` before running the application.
- You can also ask the app to change some of the settings, like
  - `set the history size to 10`
  - `use the bash shell`

## Example

```
E:\repos-own\aitoy: summarize the file length of all files in this folder and any subfolders, in megabytes.
> Get-ChildItem -Recurse | Measure-Object -Property Length -Sum | ForEach-Object { [math]::round($_.Sum / 1MB, 2) }
36
```