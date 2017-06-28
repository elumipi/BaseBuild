#!/bin/bash

DEFAULT_MODULES=( en-ebooks en-hesperian_health en-iicba en-math_expression \
                  en-medline_plus en-musictheory en-olpc en-powertyping en-practical_action en-scratch \
        	  en-understanding_algebra en-wikipedia_for_schools en-rpi_guide en-windows_apps en-asst_medical )

DEST_PATH=/var/www/modules
RSYNC_SOURCE=rsync://dev.worldpossible.org/rachelmods/
FILE_OWNER="www-data"
RSYNC_OPT=()
MODULES=()

CMDNAME=$0
Usage () {
    echo "$CMDNAME [options]"
    echo "  Options:"
    echo "    --module       Load specified module"
    echo "    --module-file  Read modules to load from provided file"
    echo "    --dest         Path to store downloaded RACHEL content (default '$DEST_PATH')"
    echo "    --rsh          Set rsync shell command"
    echo "    --source       RACHEL content server. (default '$RSYNC_SOURCE')"
    echo "    --own          Keep ownership of copied files"
    echo "    --owner        Set owner of copied files"
    echo "    --help         Display help message"
    echo ""
}

while [ true ]; do
    case $1 in 
        -h | --help | -\?)
            Usage
            exit 0
            ;;
	--module)
	    MODULES+=("$2")
	    shift 2
	    ;;
	--module-file)
	    IFS=$'\n' read -d '' -r -a NEW_MODULES < "$2"
	    MODULES=( "${MODULES[@]}" "${NEW_MODULES[@]}" )
	    shift 2
	    ;;
        --source) 
            RSYNC_SOURCE="$2"
            shift 2
            ;;
	--dest)
	    DEST_PATH="$2"
	    shift 2
	    ;;
        --own) 
	    FILE_OWNER=""
            shift 1
            ;;
        --owner) 
	    FILE_OWNER="$2"
            shift 2
            ;;
	--rsh)
	    RSYNC_OPT=("-e" "$2")
	    shift 2
	    ;;
	--*)
	    echo "$CMDNAME: invalid option '$1'"
	    exit 1
	    ;;
        *) 
            break
            ;;
    esac
done

function copy_file () {
    local MODULE="$1"
    local DESTDIR="$2"
    ${CHOWN_CMD}rsync -rlptvz "${RSYNC_OPT[@]}" "${RSYNC_SOURCE}${MODULE}" "$DEST_PATH/$DESTDIR"
    if [ $? -ne 0 ]; then
	sleep 1
	echo "Copying of $module failed or was aborted.  Exiting."
	exit
    fi
}

function copy_module () {
    local MODULE="$1"
    local DESTDIR="$2"
    ${CHOWN_CMD}rsync -rlptvz "${RSYNC_OPT[@]}" "${RSYNC_SOURCE}${MODULE}/" "$DEST_PATH/$DESTDIR"
    if [ $? -ne 0 ]; then
	sleep 1
	echo "Copying of $module failed or was aborted.  Exiting."
	exit
    fi
}

if [ $# -gt 0 ]; then
    echo "$CMDNAME: too many arguments"
    exit 1
fi

if [ `id -u` != "0" ] && [ ! -z "$FILE_OWNER" ]; then
    echo "$CMDNAME: This script must be run as root"
    exit
fi

if [ ${#MODULES[@]} -eq 0 ]; then
   MODULES="${DEFAULT_MODULES[@]}"
fi

if [ "${RSYNC_SOURCE: -1}" != ":" ] && [ "${RSYNC_SOURCE: -1}" != "/" ]; then
    RSYNC_SOURCE="${RSYNC_SOURCE}/"
fi

if [ -z "$FILE_OWNER" ]; then
    CHOWN_CMD=""
else
    CHOWN_CMD="sudo -u $FILE_OWNER SSHPASS=$SSHPASS "
fi

${CHOWN_CMD}mkdir -p "$DEST_PATH"

for MODULE in ${MODULES[@]}; do
    echo
    echo "Syncing $MODULE ..."
    DESTDIR="$MODULE"
    if [ "$DESTDIR" == "en-khan_health" ]; then
	${CHOWN_CMD}mkdir -p "$DEST_PATH/en-kaos/science/health-and-medicine"
	copy_module "en-kaos/science/health-and-medicine" "en-kaos/science/health-and-medicine"
	copy_file "en-kaos/style.css" "en-kaos"
	copy_file "en-kaos/about.html" "en-kaos"
	DESTDIR="en-kaos"
    fi
    copy_module "${MODULE}" "$DESTDIR"
done
