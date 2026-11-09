# Project Overview

## Purpose

TKKGDownloader is a Python command line tool for preparing TKKG audio drama episodes as individual MP3 files for offline listening.

## Core workflow

The intended workflow is to accept an episode number or range, resolve official episode metadata from TKKGTracker, find the matching Spotify release using episode number and title, download its Spotify tracks with spotDL, and merge them into one MP3 per episode with FFmpeg.

## Source of episode metadata

- Repository: https://github.com/OliverZsuffa/TKKGtracker
- Dataset: https://raw.githubusercontent.com/OliverZsuffa/TKKGtracker/main/data/episodes.json

The episode number and official title are relevant metadata. The dataset's `tracks` array describes chapter information and must not be assumed to match Spotify's track divisions.

## Intended environment

- Windows
- PowerShell
- Python
- spotDL
- FFmpeg

These are project requirements and intended dependencies. Exact supported versions remain to be validated during implementation.
