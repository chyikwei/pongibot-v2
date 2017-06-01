#!/bin/bash

ACT=$1

CURRENT_FOLDER=$(pwd)
ARN="arn:aws:iam::637827702214:role/pongibot-dev"
S3_BUCKET="pongibot"
FUNC_HANDLER="lambda_handler.handler"


if [ "$ACT" == "create" ]; then
    echo "going to create lambda function"
elif [ "$ACT" == "update" ]; then
    echo "going to update lambda function"
else
    echo "invalid action argument ${ACT}"
    return
fi

ZIP_FOLDER="deploy"
ZIP_FILE_NAME="lambda_pongitbot_0.2.zip"
ZIP_PATH="${CURRENT_FOLDER}/${ZIP_FOLDER}/${ZIP_FILE_NAME}"

LAMBDA_FUNC_NAME="pongibot_async_process"
VENV_NAME="venv_lambda"
VENV_PKG_FOLDER="${VENV_NAME}/lib/python2.7/site-packages/"
PIP_PATH="${VENV_NAME}/bin/pip"
REQ_PATH="requirements.txt"

TIMEOUT=60
MEMORY=128

S3_FOLDER="lambda_upload"
S3_KEY="${S3_FOLDER}/${ZIP_FILE_NAME}"


if [ ! -d "$VENV_PATH" ]; then
    echo "create venv ${VENV_NAME}"
    virtualenv ${VENV_NAME}
fi

echo "update requirement"
${PIP_PATH} install -r ${REQ_PATH}

echo "add python scripts"
zip -j9 ${ZIP_PATH} *.py

echo "add packages"
cd ${VENV_PKG_FOLDER}
zip -r9 ${ZIP_PATH} *

cd "$CURRENT_FOLDER"
echo "upload ${ZIP_PATH} to s3"
aws s3 cp ${ZIP_PATH} s3://${S3_BUCKET}/${S3_FOLDER}/


if [ "$ACT" == "create" ]; then
    echo "creating lambda function..."
    aws lambda create-function --function-name ${LAMBDA_FUNC_NAME} \
    --runtime python2.7 --role ${ARN} --handler ${FUNC_HANDLER} \
    --code S3Bucket=${S3_BUCKET},S3Key=${S3_KEY} --timeout ${TIMEOUT} \
    --memory-size ${MEMORY}
else
    echo "updating lambda fuction..."
    aws lambda update-function-code --function-name ${LAMBDA_FUNC_NAME} \
    --s3-bucket ${S3_BUCKET}  --s3-key ${S3_KEY}
fi
