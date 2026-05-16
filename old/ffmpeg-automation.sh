#!/bin/bash

# Script to use FFmpeg API for media file processing
# Usage: ./script.sh <filename> <command> [additional_args]

# Constants
SFTP_LOCATION="gtgb@10.0.255.244:./working"
LOCAL_WORK_DIR="/tmp/ffmpeg_work"
API_BASE_URL="http://10.100.101.203:3000"

# Check if required arguments are provided
if [ "$#" -lt 2 ]; then
    echo "Usage: $0 <filename> <command> [additional_args]"
    echo "Commands:"
    echo "  convert_to_mp3 - Convert audio to MP3 format"
    echo "  convert_to_wav - Convert audio to WAV format"
    echo "  convert_to_mp4 - Convert video to MP4 format"
    echo "  convert_image_to_jpg - Convert image to JPG format"
    echo "  extract_audio - Extract audio as WAV from video"
    echo "  extract_images - Extract images from video as a ZIP file"
    echo "  probe - Get metadata of the media file"
    echo "  extract_audio_to_mp3 - Extract audio as MP3 from video"
    echo "  extract_images_and_download - Extract images from video and download locally"
    echo "  dryrun - Simulate the command without making actual changes"
    exit 1
fi

# Arguments
FILE_NAME="$1"
COMMAND="$2"
ADDITIONAL_ARGS="$3"

# Prepare working directory
mkdir -p "$LOCAL_WORK_DIR"

# Fetch file from SFTP
scp "$SFTP_LOCATION/$FILE_NAME" "$LOCAL_WORK_DIR" || {
    echo "Error: Failed to download file from SFTP."
    exit 1
}

LOCAL_FILE_PATH="$LOCAL_WORK_DIR/$FILE_NAME"

# Determine file base name and extension
BASE_NAME="$(basename "$FILE_NAME" | cut -d. -f1)"
EXTENSION="${FILE_NAME##*.}"

# Define function for API call
api_call() {
    local url="$1"
    local input_file="$2"
    local output_file="$3"

    if [ "$COMMAND" == "dryrun" ]; then
        echo "[DRYRUN] Would call: curl -F 'file=@$input_file' '$url' > '$output_file'"
    else
        curl -F "file=@$input_file" "$url" > "$output_file" || {
            echo "Error: API call failed for URL: $url"
            exit 1
        }
    fi
}

# Process commands
case "$COMMAND" in
    convert_to_mp3)
        OUTPUT_FILE="$LOCAL_WORK_DIR/${BASE_NAME}-audio.mp3"
        api_call "$API_BASE_URL/convert/audio/to/mp3" "$LOCAL_FILE_PATH" "$OUTPUT_FILE"
        ;;
    convert_to_wav)
        OUTPUT_FILE="$LOCAL_WORK_DIR/${BASE_NAME}.wav"
        api_call "$API_BASE_URL/convert/audio/to/wav" "$LOCAL_FILE_PATH" "$OUTPUT_FILE"
        ;;
    convert_to_mp4)
        OUTPUT_FILE="$LOCAL_WORK_DIR/${BASE_NAME}.mp4"
        api_call "$API_BASE_URL/convert/video/to/mp4" "$LOCAL_FILE_PATH" "$OUTPUT_FILE"
        ;;
    convert_image_to_jpg)
        OUTPUT_FILE="$LOCAL_WORK_DIR/${BASE_NAME}.jpg"
        api_call "$API_BASE_URL/convert/image/to/jpg" "$LOCAL_FILE_PATH" "$OUTPUT_FILE"
        ;;
    extract_audio)
        OUTPUT_FILE="$LOCAL_WORK_DIR/${BASE_NAME}-audio.wav"
        api_call "$API_BASE_URL/video/extract/audio" "$LOCAL_FILE_PATH" "$OUTPUT_FILE"
        ;;
    extract_images)
        OUTPUT_FILE="$LOCAL_WORK_DIR/${BASE_NAME}-images.zip"
        api_call "$API_BASE_URL/video/extract/images?compress=zip" "$LOCAL_FILE_PATH" "$OUTPUT_FILE"
        ;;
    probe)
        OUTPUT_FILE="$LOCAL_WORK_DIR/${BASE_NAME}-metadata.json"
        api_call "$API_BASE_URL/probe" "$LOCAL_FILE_PATH" "$OUTPUT_FILE"
        ;;
    extract_audio_to_mp3)
        TEMP_AUDIO_FILE="$LOCAL_WORK_DIR/${BASE_NAME}-audio.wav"
        OUTPUT_FILE="${BASE_NAME}-audio.mp3"

        if [ "$COMMAND" == "dryrun" ]; then
            echo "[DRYRUN] Would extract audio as WAV: $API_BASE_URL/video/extract/audio"
            echo "[DRYRUN] Would convert WAV to MP3: $API_BASE_URL/convert/audio/to/mp3"
        else
            api_call "$API_BASE_URL/video/extract/audio" "$LOCAL_FILE_PATH" "$TEMP_AUDIO_FILE"
            api_call "$API_BASE_URL/convert/audio/to/mp3" "$TEMP_AUDIO_FILE" "$LOCAL_WORK_DIR/$OUTPUT_FILE"
            rm "$TEMP_AUDIO_FILE"
        fi
        ;;
    extract_images_and_download)
        TEMP_IMAGES_FILE="$LOCAL_WORK_DIR/${BASE_NAME}-images.zip"
        UNZIP_DIR="$LOCAL_WORK_DIR/${BASE_NAME}_images"

        if [ "$COMMAND" == "dryrun" ]; then
            echo "[DRYRUN] Would extract images as ZIP: $API_BASE_URL/video/extract/images?compress=zip"
            echo "[DRYRUN] Would unzip images to: $UNZIP_DIR"
        else
            api_call "$API_BASE_URL/video/extract/images?compress=zip" "$LOCAL_FILE_PATH" "$TEMP_IMAGES_FILE"
            mkdir -p "$UNZIP_DIR"
            unzip "$TEMP_IMAGES_FILE" -d "$UNZIP_DIR"
            mv "$UNZIP_DIR" .
            rm "$TEMP_IMAGES_FILE"
        fi
        ;;
    dryrun)
        echo "[DRYRUN] Simulating command for file: $FILE_NAME"
        ;; 
    *)
        echo "Error: Unknown command '$COMMAND'"
        exit 1
        ;;
esac

# Move the output to the current working directory
if [ "$COMMAND" != "extract_images_and_download" ] && [ "$COMMAND" != "dryrun" ]; then
    mv "$LOCAL_WORK_DIR/$OUTPUT_FILE" . || {
        echo "Error: Failed to move output file to the current directory."
        exit 1
    }
fi

# Clean up
if [ "$COMMAND" != "dryrun" ]; then
    rm -rf "$LOCAL_WORK_DIR"
fi

echo "Processing complete. Output saved to: $(pwd)/$OUTPUT_FILE"
