<p align="center">
  <img src="https://upload.wikimedia.org/wikipedia/commons/e/ef/Youtube_logo.png" width="200">
</p>


# YouTube Playlist Organizer

A Python project to help organize YouTube playlists by automatically adding new videos
to private playlists using the YouTube Data API.

- [Important Notes](#important-notes)
- [Motivation](#motivation)
- [Project Structure](#project-structure)
- [Usage](#usage)



## Important Notes

1. To use this repository, you must generate a YouTube Data API key and create a file named `API_KEY.py`. Is also necessary to manually create the file `credentials.json` and stored in  `Tokens/`. [Learn More](https://developers.google.com/youtube/registering_an_application)
2. The YouTube API is free to use but has a daily quota limit of 10,000 units. See the [Quota Calculator](https://developers.google.com/youtube/v3/determine_quota_cost).
3. This project is still a work in progress, and more features will be added over time.

## Motivation

- This project creates private playlists and automatically adds new videos, helping you keep your YouTube content organized.
- It was created to reduce manual playlist management and make better use of the YouTube API.

## Project Structure

To reduce daily quota usage, the project stores cached information in `.txt` and `.csv` files and creates the following folders:

- `Content Creators/`: each YouTube channel (handle) has its own file storing video IDs already added.
- `Exceptions/`: handles that should not be added to any playlist (e.g. shorts-only channels).
- `Playlists/`: each `.txt` file represents a playlist and contains associated handles.
- `Restrictions/`: videos blocked in your region are stored here and skipped.
- `Stats/`: files tracking daily quota usage and a DataFrame with channel information.
- `Tokens/`: authentication files used to interact with the YouTube API.

## Usage

1. Install dependencies:
   ```bash
   pip install -r requirements.txt







