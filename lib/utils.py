import os

def print_red(text: str) -> None:
    print(f"\033[31m{text}\033[0m")

# Get the file name without the extension
def get_file_name(filename: str) -> str:
    return os.path.splitext(filename)[0]

# generate a random name for the srt file
def get_subtitle_file() -> str:
    return "subtitle-" + str(os.urandom(6).hex()) + ".srt"

# manage the -r flag
def delete_mkv(filename: str) -> None:
    print(f"    ⌛️ Deleting: \033[33m" + filename + "\033[0m ...")
    try:
        # delete the file if it's a valid mkv file
        if os.path.isfile(filename) and (filename.endswith(".mkv") or filename.endswith(".MKV")):
            os.remove(filename)
            print(f"    🗑️ \033[33m" + filename + "\033[0m has been deleted!")
    except Exception as e:
        print_red("❌ Failed to delete file: " + filename)
        print_red("❌ Error: " + str(e))
        exit(1)