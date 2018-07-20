#!/bin/sh
cd /
echo "compressing /data"
tar -zcf tmp/$HOSTNAME-`date "+%Y-%m-%d_%H-%M-%S"`.tar.gz data/data
echo "compressing /logs"
tar -zcf tmp/$HOSTNAME-`date "+%Y-%m-%d_%H-%M-%S"`.tar.gz data/logs
echo "uploading tarballs"
/usr/local/bin/aws s3 cp /tmp/*.tar.gz $AWS_S3_BUCKET_URL
echo "cleaning up"
rm /tmp/*.tar.gz
