# YouTube playlist Organizer

A Python project to help organize YouTube playlists by automatically adding new videos
to private playlists using the YouTube Data API.

## Important Notes

1. To use this repository, you must generate a YouTube Data API key and create a file named `API_KEY.py`.
2. The YouTube API is free to use but has a daily quota limit of 10,000 units. See the [Quota Calculator](https://developers.google.com/youtube/v3/determine_quota_cost).
3. This project is still a work in progress, and more features will be added over time.

## Motivation

- This project creates private playlists and adds new videos automatically, helping you keep your YouTube content organized.
- It was created to reduce manual playlist management and make better use of the YouTube API.

## Project Structure

- To save daily quota usage, the project stores some information in `.txt` and `.csv` files.
- The main logic is implemented in Python scripts that interact with the YouTube API.

## Usage

1. Install dependencies
2. Configure your API key
3. Run the main script to add new videos to the playlists


## Future Work

- Still working on:
  - Uploading files to generate a DataFrame containing information for each channel







