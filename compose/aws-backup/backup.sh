#!/bin/sh
cd /
echo "compressing /data"
tar -zcf tmp/$HOSTNAME-`date "+%Y%m%d%H%M%S"`_data.tar.gz /data
echo "compressing /logs"
tar -zcf tmp/$HOSTNAME-`date "+%Y%m%d%H%M%S"`_logs.tar.gz /logs
echo "uploading tarballs"
/usr/local/bin/aws s3 cp /tmp $AWS_S3_BUCKET_URL --recursive --exclude "*" --include "*.tar.gz"
echo "cleaning up"
rm /tmp/*.tar.gz

