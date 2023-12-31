import base64
import datetime
import json
import mimetypes
import os
import sys
import zipfile
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Generator, List, Optional, Set

import click
import html2text
import magic
import tqdm
from jinja2 import Environment, FileSystemLoader, Template

# the version of my export as of 2023-11-27 Android app version 1.54.4
# no idea what this might be from an iPhone export of the Daylio journal
SUPPORTED_VERSION = 15

PREDEFINED_MOODS = {
    1: "rad",
    2: "good",
    3: "meh",
    4: "bad",
    5: "awful",
}


@dataclass(frozen=True)
class DaylioAssetFile():
    checksum: str
    data: bytes

    @property
    def mimetype(self) -> str:
        mime = magic.Magic(mime=True)
        return mime.from_buffer(self.data)

    @property
    def filename(self) -> str:
        return self.checksum + mimetypes.guess_extension(self.mimetype)

    def __str__(self) -> str:
        return f"{self.checksum} ({self.mimetype}) {len(self.data)} bytes"


@dataclass(frozen=True)
class DaylioMood():
    id: int
    custom_name: str
    mood_group_id: int
    predefined_name_id: int

    @property
    def mood_name(self) -> str:
        if self.predefined_name_id in PREDEFINED_MOODS:
            return PREDEFINED_MOODS[self.predefined_name_id]
        return self.custom_name

    def __str__(self) -> str:
        return self.mood_name

@dataclass(frozen=True)
class DaylioTag():
    id: int
    name: str

    @property
    def hashtag(self) -> str:
        """
        Return the tag with spaces replaced with dashes, with a # at the front.
        """
        return f"#{self.name.replace(' ', '-')}"

    @property
    def tag(self) -> str:
        """
        Return the tag with spaces replaced with dashes, but without a # at the front.
        """
        return self.name.replace(' ', '-')


@dataclass(frozen=True)
class AndroidMetadata():
    name: str
    last_modified: int
    orientation: int
    duration: int


class DaylioAssetType(Enum):
    PHOTO = 1
    AUDIO = 2


@dataclass#(frozen=True)
class DaylioAsset():
    id: int
    type: DaylioAssetType
    checksum: str
    created_at: int
    created_at_offset: int
    android_metadata: AndroidMetadata
    file: DaylioAssetFile


@dataclass(frozen=True)
class DaylioDayEntry:
    id: int
    timestamp: datetime.datetime
    mood: DaylioMood
    note_html: str
    note_title: str
    tags: List[DaylioTag]
    assets: List[DaylioAsset]

    @property
    def note_text(self) -> str:
        return html2text.html2text(self.note_html)

    @property
    def date(self) -> datetime.date:
        return self.timestamp.date()


@dataclass
class DaylioJournal():
    version: int
    custom_moods: Dict[int, DaylioMood]
    day_entries: List[DaylioDayEntry]
    tags: Dict[int, DaylioTag]
    assets: Dict[int, DaylioAsset]

    def __init__(self, asset: DaylioAssetFile):
        self.custom_moods = {}
        self.tags = {}
        self.day_entries = []
        self.assets = {}

        data = json.loads(base64.b64decode(asset.data))

        self.version = data['version']
        for tag in data['tags']:
            self.tags[tag['id']] = DaylioTag(id=tag['id'], name=tag['name'])

        for mood in data['customMoods']:
            self.custom_moods[mood['id']] = DaylioMood(
                id=mood['id'],
                custom_name=mood['custom_name'],
                mood_group_id=mood['mood_group_id'],
                predefined_name_id=mood['predefined_name_id']
            )

        for asset in data['assets']:
            android_metadata = json.loads(asset['android_metadata'])

            type: DaylioAssetType
            if asset['type'] == DaylioAssetType.AUDIO.value:
                type = DaylioAssetType.AUDIO
            elif asset['type'] == DaylioAssetType.PHOTO.value:
                type = DaylioAssetType.PHOTO
            else:
                raise Exception(f"Unknown asset type in journal: {asset['type']}")

            self.assets[asset['id']] = DaylioAsset(
                id=asset['id'],
                type=type,
                checksum=asset['checksum'],
                created_at=asset['createdAt'],
                created_at_offset=asset['createdAtOffset'],
                android_metadata=AndroidMetadata(
                    name=android_metadata['Name'],
                    last_modified=android_metadata['LastModified'],
                    orientation=android_metadata.get('Orientation'),
                    duration=android_metadata.get('Duration'),
                ),
                file=None
            )

        # in my journal two entries have the exact same timestamp - probably from
        # manually setting a time for a past event - keep track of those and increment
        # timestamps by a millisecond to avoid duplicate keys in the dict
        seen_entry_timestamps: Set[int] = set()

        for day_entry in data['dayEntries']:
            epochtime = day_entry['datetime']
            while epochtime in seen_entry_timestamps:
                # print(f"Incrementing timestamp on entry due to duplicates - from {epochtime} to {epochtime + 1}")
                epochtime += 1

            seen_entry_timestamps.add(epochtime)

            # Convert milliseconds to seconds for the timestamp
            timestamp = datetime.datetime.fromtimestamp(
                epochtime / 1000,
                datetime.timezone(datetime.timedelta(seconds=day_entry['timeZoneOffset'] / 1000))
            )

            self.day_entries.append(DaylioDayEntry(
                id=day_entry['id'],
                timestamp=timestamp,
                mood=self.custom_moods[day_entry['mood']],
                note_html=day_entry['note'],
                note_title=day_entry['note_title'],
                tags=[self.tags[tag_id] for tag_id in day_entry['tags']],
                assets=[self.assets[asset_id] for asset_id in day_entry['assets']],
            ))


class DaylioJournalBackup():
    def __init__(self, zipfile: str):
        self.zipfile = zipfile
        self.zip: Optional[zipfile.ZipFile] = None

    def __enter__(self) -> 'DaylioJournalBackup':
        self.zip = zipfile.ZipFile(self.zipfile, 'r')
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.zip.close()
        pass

    @property
    def files(self) -> Generator[str, None, None]:
        for file_name in self.zip.namelist():
            yield file_name

    def load_asset(self, checksum: str) -> DaylioAssetFile:
        filename = next(filter(lambda x: x.endswith(checksum), self.files))
        with self.zip.open(filename) as file:
            return DaylioAssetFile(checksum, file.read())

    def load_journal(self) -> DaylioJournal:
        return DaylioJournal(self.load_asset('backup.daylio'))


def write_file_if_unchanged(path: str, bytes: bytes) -> bool:
    """
    Write a file to disk, but only if the contents are different from the existing file.
    """
    if os.path.exists(path):
        with open(path, 'rb') as f:
            if f.read() == bytes:
                return False

    with open(path, 'wb') as f:
        f.write(bytes)

    return True


@click.command()
@click.option('--backup',
              type=click.Path(exists=True, dir_okay=False, file_okay=True, readable=True),
              required=True)
@click.option('--markdown',
              type=click.Path(exists=True, file_okay=False, writable=True),
              required=True)
@click.option('--images',
              type=click.Path(exists=True, file_okay=False, writable=True),
              required=True)
@click.option('--template',
              type=click.Path(exists=True, dir_okay=False, file_okay=True, readable=True),
              required=True)
@click.option('--overwrite',
              is_flag=True,
              help="Overwrite existing files. Defaults to skipping already existing files.")
@click.option('--ignore-version',
              is_flag=True,
              help="Ignore Daylio version specified in file. "
              "Use to *attempt* to parse versions not explicitly supported.")
@click.option('--skip-empty',
              is_flag=True,
              help="Skip entries with no note and no assets (photos, audio).)")
@click.option('--verbose',
              is_flag=True,
              help="Print verbose output.")
def main(backup, markdown, images, template, overwrite, ignore_version, skip_empty, verbose):
    """Converts Daylio export files to Markdown format."""

    with DaylioJournalBackup(backup) as daylio:
        journal = daylio.load_journal()

        if journal.version != SUPPORTED_VERSION:
            if ignore_version:
                click.echo(
                    f"Unsupported Daylio version: [{journal.version}]. "
                    f"Only [{SUPPORTED_VERSION}] is supported."
                    f"Continuing anyway, due to --ignore-version flag.",
                    file=sys.stderr
                )
            else:
                raise click.ClickException(
                    f"Unsupported Daylio version: [{journal.version}]. "
                    f"Only [{SUPPORTED_VERSION}] is supported. Aborting. "
                    f"If you want to proceed anyway, use --ignore-version flag."
                )

        template: Template
        jinja = Environment(
            loader=FileSystemLoader(os.path.dirname(template)),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        template = jinja.get_template(os.path.basename(template))

        skipped_existing_asset = 0
        skipped_existing_note = 0
        skipped_empty = 0
        exported_note = 0
        exported_asset = 0

        with tqdm.tqdm(journal.day_entries, desc='Exporting Daylio entries', disable=not sys.stdout.isatty()) as t:
            for daily_entry in t:
                t.set_postfix_str(f"skipped: {skipped_empty} empty / "
                                  f"{skipped_existing_note} existing notes / "
                                  f"{skipped_existing_asset} existing assets")

                filename = f"{daily_entry.timestamp.strftime('%Y-%m-%d')} - Daylio - {daily_entry.timestamp.timestamp()}.md"
                path = os.path.join(markdown, filename)
                if os.path.exists(path) and not overwrite:
                    skipped_existing_note += 1
                    if verbose:
                        t.write(f"Skipping {filename} as it already exists.")
                    continue

                if skip_empty:
                    if not daily_entry.note_html and not daily_entry.note_title and not daily_entry.assets:
                        skipped_empty += 1
                        if verbose:
                            t.write(f"Skipping {filename} as it has no note and no assets.")
                        continue

                for asset in daily_entry.assets:
                    asset.file = daylio.load_asset(asset.checksum)

                    asset_path = os.path.join(images, asset.file.filename)
                    if os.path.exists(asset_path) and not overwrite:
                        skipped_existing_asset += 1
                        if verbose:
                            t.write(f"Skipping {asset.file.filename} as it already exists.")
                        continue

                    written = write_file_if_unchanged(asset_path, asset.file.data)
                    if written:
                        if verbose:
                            t.write(f"Exported {filename}")
                        exported_asset += 1
                    else:
                        if verbose:
                            t.write(f"Skipping {asset.file.filename} as it already exists with identical content.")
                        skipped_existing_asset += 1

                md = template.render(
                    entry=daily_entry
                )

                written = write_file_if_unchanged(path, md.encode('utf-8'))
                if written:
                    if verbose:
                        t.write(f"Exported {filename}")
                    exported_note += 1
                else:
                    if verbose:
                        t.write(f"Skipping {filename} as it already exists with identical content.")
                    skipped_existing_note += 1

                # unload the asset bytes from memory once the note is processed
                for asset in daily_entry.assets:
                    asset.file = None

        if skip_empty:
            print(f"Skipped {skipped_empty} empty (no note, and no assets) entries.")
        print(f"Skipped {skipped_existing_note} existing notes and {skipped_existing_asset} existing assets.")
        print(f"Exported {exported_note} notes and {exported_asset} assets.")

if __name__ == '__main__':
    main()