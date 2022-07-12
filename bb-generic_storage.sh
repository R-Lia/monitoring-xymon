#!/bin/sh

#### Meta information
# OS : Linux (Debian-like), FreeBSD
# Author : Michel Gravey (sys.vision)

TEST='storage'

ZFS_TOTAL_SIZE_BYTES=0
ZFS_ALLOC_SIZE_BYTES=0
ZFS_FREE_SIZE_BYTES=0
if [ -e "/dev/zfs" ]; then
	while read total_size alloc_size free_size
	do
		ZFS_TOTAL_SIZE_BYTES=$(( ZFS_TOTAL_SIZE_BYTES + total_size ))
		ZFS_ALLOC_SIZE_BYTES=$(( ZFS_ALLOC_SIZE_BYTES + alloc_size ))
		ZFS_FREE_SIZE_BYTES=$(( ZFS_FREE_SIZE_BYTES + free_size ))
	done <<EOF
	$(zpool list -Hp | awk '{ print $2" "$3" "$4 }')
EOF
fi

SYSTEM=$(uname -s)
OTHERFS_STRING_SIZE_BYTES=""
OTHERFS_TOTAL_SIZE_BYTES=0
OTHERFS_ALLOC_SIZE_BYTES=0
OTHERFS_FREE_SIZE_BYTES=0

case "$SYSTEM" in
	FreeBSD)
		OTHERFS_STRING_SIZE_BYTES=$(df -t ufs,nfs -k -c | $TAIL -n 1 | $AWK '{ print $2" "$3" "$4 }')
		OTHERFS_TOTAL_SIZE_BYTES=$(( `echo $OTHERFS_STRING_SIZE_BYTES | $AWK '{ print $1 }'` / 1024 ))
		OTHERFS_ALLOC_SIZE_BYTES=$(( `echo $OTHERFS_STRING_SIZE_BYTES | $AWK '{ print $2 }'` / 1024 ))
		OTHERFS_FREE_SIZE_BYTES=$(( `echo $OTHERFS_STRING_SIZE_BYTES | $AWK '{ print $3 }'` / 1024 ))
		;;
	Linux)
		OTHERFS_STRING_SIZE_BYTES=$(df -t ext3 -t ext4 -t btrfs -t nfs --block-size=1 --total | $TAIL -n 1 | $AWK '{ print $2" "$3" "$4 }')
		OTHERFS_TOTAL_SIZE_BYTES=$(echo $OTHERFS_STRING_SIZE_BYTES | $AWK '{ print $1 }')
		OTHERFS_ALLOC_SIZE_BYTES=$(echo $OTHERFS_STRING_SIZE_BYTES | $AWK '{ print $2 }')
		OTHERFS_FREE_SIZE_BYTES=$(echo $OTHERFS_STRING_SIZE_BYTES | $AWK '{ print $3 }')
		;;
esac

TOTAL_SIZE_BYTES=0
TOTAL_SIZE_BYTES=$(( OTHERFS_TOTAL_SIZE_BYTES + ZFS_TOTAL_SIZE_BYTES ))
ALLOC_SIZE_BYTES=0
ALLOC_SIZE_BYTES=$(( OTHERFS_ALLOC_SIZE_BYTES + ZFS_ALLOC_SIZE_BYTES ))
FREE_SIZE_BYTES=0
FREE_SIZE_BYTES=$(( OTHERFS_FREE_SIZE_BYTES + ZFS_FREE_SIZE_BYTES ))

#DEBUG
#echo "TOTAL : $TOTAL_SIZE_BYTES"
#echo "ALLOC : $ALLOC_SIZE_BYTES"
#echo "FREE : $FREE_SIZE_BYTES"

$BB $BBDISP "data $MACHINE.$TEST $(echo; echo -e "$TEST : $TOTAL_SIZE_BYTES\n${TEST}_alloc : $ALLOC_SIZE_BYTES\n${TEST}_free : $FREE_SIZE_BYTES\n\n")"
