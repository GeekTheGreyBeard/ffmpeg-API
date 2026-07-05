#!/usr/bin/env bash
set -euo pipefail

IMAGE="${IMAGE:-ffmpeg-api:1.3.0}"
CONTAINER_NAME="${CONTAINER_NAME:-ffmpeg-api-smoke}"
PORT="${PORT:-18000}"
TMP_DIR="$(mktemp -d)"
PYTHON_BIN="${PYTHON_BIN:-$(command -v python3 || command -v python)}"

cleanup() {
  docker rm -f "${CONTAINER_NAME}" >/dev/null 2>&1 || true
  rm -rf "${TMP_DIR}"
}
trap cleanup EXIT

docker build -t "${IMAGE}" .
docker rm -f "${CONTAINER_NAME}" >/dev/null 2>&1 || true
docker run -d --name "${CONTAINER_NAME}" -p "${PORT}:8000" "${IMAGE}" >/dev/null

for _ in {1..30}; do
  if curl -fsS "http://127.0.0.1:${PORT}/health" >/dev/null; then
    break
  fi
  sleep 1
done

curl -fsS "http://127.0.0.1:${PORT}/health" | grep -q '"status":"ok"'
curl -fsS "http://127.0.0.1:${PORT}/endpoints" | grep -q 'convert_to_mp3'

ffmpeg -hide_banner -loglevel error -f lavfi -i sine=frequency=1000:duration=1 -q:a 9 "${TMP_DIR}/tone.mp3"
ffmpeg -hide_banner -loglevel error -f lavfi -i sine=frequency=800:duration=1 "${TMP_DIR}/tone.wav"
ffmpeg -hide_banner -loglevel error -f lavfi -i testsrc=size=160x120:rate=10:duration=1 -f lavfi -i sine=frequency=440:duration=1 -shortest -pix_fmt yuv420p "${TMP_DIR}/sample.mp4"
ffmpeg -hide_banner -loglevel error -f lavfi -i testsrc=size=64x64:duration=1 -frames:v 1 "${TMP_DIR}/sample.png"

post_file() {
  local endpoint="$1"
  local file="$2"
  curl -fsS -X POST -F "file=@${file}" "http://127.0.0.1:${PORT}${endpoint}"
}

download_from_file_id() {
  local json="$1"
  local file_id
  file_id="$(printf '%s' "${json}" | "${PYTHON_BIN}" -c 'import json,sys; print(json.load(sys.stdin)["file_id"])')"
  curl -fsS "http://127.0.0.1:${PORT}/download/${file_id}" -o "${TMP_DIR}/download-${file_id}"
  test -s "${TMP_DIR}/download-${file_id}"
}

download_from_file_id "$(post_file /convert_to_mp3 "${TMP_DIR}/tone.wav")"
download_from_file_id "$(curl -fsS -X POST -F "file=@${TMP_DIR}/tone.wav" -F "format=mp3" -F "audio_codec=libmp3lame" -F "audio_bitrate=96k" "http://127.0.0.1:${PORT}/convert")"
download_from_file_id "$(post_file /convert_to_wav "${TMP_DIR}/tone.mp3")"
download_from_file_id "$(post_file /convert_to_mp4 "${TMP_DIR}/sample.mp4")"
download_from_file_id "$(post_file /convert_image_to_jpg "${TMP_DIR}/sample.png")"
download_from_file_id "$(post_file /extract_audio "${TMP_DIR}/sample.mp4")"
download_from_file_id "$(post_file /extract_images "${TMP_DIR}/sample.mp4")"
post_file /probe "${TMP_DIR}/sample.mp4" | grep -q '"format"'
download_from_file_id "$(post_file /extract_audio_to_mp3 "${TMP_DIR}/sample.mp4")"
post_file /split_mp3 "${TMP_DIR}/tone.mp3" | grep -q 'chunk_file_ids'
download_from_file_id "$(post_file /scrubber "${TMP_DIR}/tone.mp3")"
artifact_id="$(post_file /convert_to_mp3 "${TMP_DIR}/tone.wav" | "${PYTHON_BIN}" -c 'import json,sys; print(json.load(sys.stdin)["file_id"])')"
curl -fsS "http://127.0.0.1:${PORT}/artifacts/${artifact_id}" | grep -q '"operation"'
curl -fsS -X DELETE "http://127.0.0.1:${PORT}/artifacts/${artifact_id}" | grep -q '"deleted":true'
curl -sS "http://127.0.0.1:${PORT}/download/not-a-real-id" -o /dev/null -w '%{http_code}' | grep -q '404'

echo "container smoke tests passed"
