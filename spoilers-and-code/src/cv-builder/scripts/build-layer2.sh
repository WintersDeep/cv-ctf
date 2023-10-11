# stop on error
set -e

# location things we are going to need
SCRIPT_DIRECTORY=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

PATCHER_PROJECT_DIRECTORY=$(cd ${SCRIPT_DIRECTORY}/.. && pwd)
PATCHER_BUILD_DIRECTORY="${PATCHER_PROJECT_DIRECTORY}/build"
PATCHER_BUILD_TEST_DATA_DIRECTORY="${PATCHER_PROJECT_DIRECTORY}/test-data"
PATCHER_OUTPUT_NAME="layer2-composited.pdf"
PATCHER_OUTPUT_PATH="${PATCHER_BUILD_DIRECTORY}/${PATCHER_OUTPUT_NAME}"

FLAG2="Troubled Tortoise"
LAYER2_BASE="${PATCHER_BUILD_TEST_DATA_DIRECTORY}/flag-layer-unprocessed.pdf"
LAYER2_EMBEDDED_DATA="${PATCHER_BUILD_TEST_DATA_DIRECTORY}/flag3.zip"
LAYER2_EMBED_IMAGE="${PATCHER_BUILD_TEST_DATA_DIRECTORY}/image.png"
LAYER2_QR_MESSAGE=$(echo "Flag #2: ${FLAG2}" $'\nI buried the next flag in my treasure, be careful though it has a habit of disappearing when being taken.')

LAYER2_QRCODE_RECT=(44 233 182 372)
LAYER2_IMAGE_RECT=(667 233 805 372)


PYTHON="${PATCHER_PROJECT_DIRECTORY}/venv/bin/python"

# make sure patch build directory exists
mkdir -p "${PATCHER_BUILD_DIRECTORY}"

"${PYTHON}" -m pdfp insert-image-with-data "${LAYER2_BASE}" ${LAYER2_IMAGE_RECT[@]} "${LAYER2_EMBED_IMAGE}" "${LAYER2_EMBEDDED_DATA}" "${PATCHER_OUTPUT_PATH}.0"
"${PYTHON}" -m pdfp insert-qr-code "${PATCHER_OUTPUT_PATH}.0" ${LAYER2_QRCODE_RECT[@]} "${LAYER2_QR_MESSAGE}" "${PATCHER_OUTPUT_PATH}"
