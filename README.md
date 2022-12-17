# mk4

![preview](https://pbs.twimg.com/media/FkISQIGWYAYLWpC?format=jpg&name=large)

## _I want it to be mp4_

mk4 is a Python 3 script to convert mkv videos into mp4, and burning subtitles into the mp4 output. You can choose the font and the size of the subtitles in the config file.

## Usage
### _Configuration_
To configure the mk4 script, you need to edit the config variables in `config.ini`. You will be able to change the font name, the size, and the crf. Keeping the defaults values is enough to have a good experience.

### _Launch script_
```sh
mk4.py <file.mkv | directory> [<file.mkv | directory> ...]
```

OR

```sh
mk4.py --help
```

## Prerequisites
You only need to have ffmpeg installed in your system.

## To-Do

- Deal with multiples audio/subtitles tracks
- Improve the stdout to make it more dynamic
- The `--help` flag

Please enjoy !!
