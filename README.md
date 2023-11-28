# About

Takes the backup from the [Daylio](https://daylio.net/) journal in the `.daylio` format (described below)
and converts to Markdown files. This script doesn't support the CSV format as an intentional choice,
since that format doesn't support exporting the images/audio added to your notes.

Intended to be used once or multiple times. For example for regularly syncing your Daylio journal
into your Obsidian (or otherwise) Markdown vault.

Will export the notes into defined folder path, and images into another defined folder path.

# Status

Fully functioning for my use-case.

Plenty more could be done for yours. PRs welcome!

I have not tested with an iOS Daylio export. I don't know what might be different.
I assume the "AndroidMetadata" block isn't present in the iOS export and is replaced by something
iOS relevant.

# Enhancements / TODOs

Things that  I'm either interested in doing for my own needs or I could see other people benefitting from:

- Insert Daylio notes into existing notes (e.g. add a Daylio heading in your daily Obsidian note)
  rather than overwriting existing notes.
- Condense multiple notes from the same day/week/month into a single markdown file.
- Export all moods into a single chronological file. To better support individual files for text content
  and media, but still exporting all of the moods without creating thousands of files.
  - This might be ideal for incorporating with
    [Obsidian Dataview](https://github.com/blacksmithgu/obsidian-dataview).
- Custom filename template (possibly in-line with combining multiple entries into one file).
- CVS Daylio export support - would be easy to add, but I'm not interested due to lack of image support.
- Support for other data-points in the `.daylio` backup.

# Installation

I recommend [pipx](https://github.com/pypa/pipx):

```
pipx install git+https://github.com/mbafford/daylio-markdown-export.git
```

# Usage

```
daylio2markdown --backup data/backup_2023_11_27.daylio --markdown ~/notes/daylio/ --images ~/notes/daylio/images/ --template template.md --skip-empty
```

Use `--help` for more information / options.

# Templates

The template format is powered by [Jinja2](https://github.com/pallets/jinja).
There's an example that outputs most of the data available in template.md.

Information about how to write Jinja2 templates is outside the scope of this README.

# Related Projects

- [Obsidian Daylio Parser](https://github.com/DeutscheGabanna/Obsidian-Daylio-Parser)
  - Reads the CSV export format, so doesn't include images.
- [Daylio to Obsidian Daily Notes](https://github.com/fsaresh/Dayio-to-Obsidian-Daily-Notes)
  - Another CSV to Markdown exporter.
- [Daylio Web](https://github.com/jaxparrow07/daylio-web)
  - Loads the `.daylio` backup file and allows you to browse the journal, with a nice UI and charts.  

# Data Format

The `daylio` backup format is actually a ZIP file of multiple files:

```
backup_2023_11_23.daylio (ZIP compressed archive)
=================================================
assets/
    photos/
        2023/              - Year 
            9/             - Month, not 0 padded
                <assetid>  - Image file (always JPEG in my backup, maybe others?). No extension.
backup.daylio              - Base64 encoded JSON data
```

While the `<assetid>` is identified as "checksum" in the file, it is NOT the md5sum of the image
file itself. Not sure what the checksum value actually represents, but it's probably not important
for the purposes of this tool.

## backup.daylio

Embedded in the ZIP file. Contains a JSON object base64 encoded.

Reference below of the data-points I care about for this exporter.

Concepts ignored by this exporter:
- achievements
- goals
- goal successes
- metadata
- milestones
- icons
- pin (yes, the pin locking your journal is in plaintext once you unzip/base64 decode your archive)
- preferences
- reminders
- tag groups
- tag icons
- writing templates

After base64 decoding the JSON stored in `backup.daylio` inside the main `backup_<date>.daylio`
zip archive, you fill find a structure something like this:

```json
{
  "version": 15,
  "pin": 12345,
  "achievements": [],
  "goalEntries": [],
  "goalSuccessWeeks": [],
  "goals": [],
  "milestones": [],
  "prefs": [],
  "reminders": [],
  "tag_groups": [],
  "writingTemplates": [],
  "assets": [
    {
      "android_metadata": "{\"Name\":\"Screenshot_20220825-113609.png\",\"LastModified\":1661442023000,\"Orientation\":0}",
      "checksum": "f64aecf702fbe90faa086148e57638fa",
      "createdAt": 1661442023327,
      "createdAtOffset": -14400000,
      "id": 12,
      "type": 1
    },
    {
      "android_metadata": "{\"Name\":\"PXL_20220903_150112805.MP.jpg\",\"LastModified\":1662318849000,\"Orientation\":0}",
      "checksum": "6ad9fd0faa3332b93920b681f9203328",
      "createdAt": 1662318849866,
      "createdAtOffset": -14400000,
      "id": 13,
      "type": 1
    }
  ],
  "customMoods": [
    {
      "createdAt": 0,
      "custom_name": "",
      "icon_id": 304,
      "id": 1,
      "mood_group_id": 1,
      "mood_group_order": 0,
      "predefined_name_id": 1,
      "state": 0
    },
    {
      "createdAt": 0,
      "custom_name": "",
      "icon_id": 301,
      "id": 2,
      "mood_group_id": 2,
      "mood_group_order": 0,
      "predefined_name_id": 2,
      "state": 0
    },
    {
      "createdAt": 0,
      "custom_name": "meh+",
      "icon_id": 321,
      "id": 6,
      "mood_group_id": 2,
      "mood_group_order": 1,
      "predefined_name_id": -1,
      "state": 0
    }
  ],
  "dayEntries": [
    {
      "assets": [
        12, 13
      ],
      "datetime": 1700408759432,
      "day": 19,
      "hour": 10,
      "id": 15024,
      "minute": 45,
      "month": 10,
      "mood": 1,
      "note": "Working on a Daylio to Markdown converter",
      "note_title": "",
      "tags": [
        179
      ],
      "timeZoneOffset": -18000000,
      "year": 2023
    },
    {
      "assets": [],
      "datetime": 1575750093255,
      "day": 7,
      "hour": 15,
      "id": 13466,
      "minute": 21,
      "month": 11,
      "mood": 1,
      "note": "Multiple tags on the same note",
      "note_title": "",
      "tags": [
        177,
        167
      ],
      "timeZoneOffset": -18000000,
      "year": 2019
    }
  ],
  "tags": [
    {
      "createdAt": 1546392776714,
      "icon": 6,
      "id": 184,
      "id_tag_group": 1,
      "name": "programming",
      "order": 1,
      "state": 0
    },
    {
      "createdAt": 1546391637835,
      "icon": 271,
      "id": 183,
      "id_tag_group": 1,
      "name": "exercising",
      "order": 2,
      "state": 0
    }
  ]
}
```

## Moods

```json
{
    "createdAt": 0,
    "custom_name": "",
    "icon_id": 304,
    "id": 1,
    "mood_group_id": 1,
    "mood_group_order": 0,
    "predefined_name_id": 1,
    "state": 0
},
```

The moods JSON allows for custom and predefined moods. The `predefined_name_id` values aren't defined
in the JSON, so I had to guess at their values based on looking at similar records in the CSV export.

| predefined_name_id | text name                   |
| ------------------ | --------------------------- |
| -1                 | use the `custom_name` value |
| 1                  | rad                         |
| 2                  | good                        |
| 3                  | meh                         |
| 4                  | bad                         |
| 5                  | awful                       |


# Obtaining the backup

Go into `Daylio -> More (settings) -> Backup & Restore -> Advanced Options -> Export` to obtain the
backup file this tool needs. Then send to your computer and run this script against that file.

# Automation

Currently there is no supported way to automate the export. I think Daylio's automated backups
write these zipped `.daylio` files into your Google Drive account, so if you can gain access to the
app data for Daylio in your Google Drive account (not supported, but there are ways), then I assume
this would work on those files and could be automated.