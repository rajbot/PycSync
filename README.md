PycSync: 2-way Synchronize local photos with flickr
==================================================

This python script is an attempt to improve my poor workflow for digital 
photos. I have been using iPhoto for the last 10 years, and it is terrible
software. I was working at Apple when it was first released, and was a 
very early user. I have no idea why I have been using it for so long.
iPhoto is less buggy, crashy, and slow than it used to be, but it is
still incredibly bad.

I no longer try to crop or edit photos, so I really don't need photo editing
software anymore. My new Canon T1i with came with several Canon utilities
which I installed. The only one that seems useful is Canon ImageBrowser,
which launches automatically when I put a memory card into the card reader.
It automatically copies the images to a dated directory in my  Pictures folder.

Workflow
--------
- Insert memory card in card reader
- Canon utility automatically launches instead of iPhoto
- Import photos into a directory
- Use the ImageBrowser or OSX Finder in Cover Flow mode to review the photos
- Delete blurry photos
- Add PycSync.yml to directory with name of album and privacy settings
- Run pycsync.py, which creates a flickr set and uploads photos
- Edit metadata on flickr (optional)
- Add new photos to directory (optional)
- Run pycsync.py again to upload new photos and download metadata locally

Todo
----
- Check for duplicates using md5s of previous imports
- Create posterous post of flickr favorites
- Create twitter post of public flickr favorites
- Sync tags, descriptions, and notes
- Add flickr machine tags with hashes: http://longair.net/blog/2009/12/19/hashing-flickr-photos/

Usage
-----
Put your flickr api keys in ~/.pycsync
 flickr_api: [api_key, secret]

Then, create a directory of photos. Place a PycSync.yml file in that dir.
PycSync.yml should look like this:

    album: Title of Flickr Set
    is_public: 0
    is_family: 1
    is_friend: 1

Run pycsync.py in the directory you wish to sync to flickr.

Upload status will be saved in PycSync_meta.yml. Don't edit PycSync_meta.yml
manually; edit metadata only on Flickr, and run pycsync.py to copy the
metadata from flickr into meta.yml.

Python depencencies
-------------------
- flickrapi
- pyyaml
