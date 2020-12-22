#! /bin/bash    

_LOGFILE=$0.log
_URL="http://?.?.?.?:9702/scs2redis"
_NOW=$(date +"%Y-%m-%d %H:%M:%S.%6N")
_EPOCH=$(date +"%s")

# parse SCS cmd line args
while [ 0 -lt "$#" ]; do
case "$1" in
"-msgid") shift; MSGID="$1" ;;
"-msgtext") shift; MSGTEXT="$1" ;;
"-condid") shift; CONDID="$1" ;;
"-condname") shift; CONDNAME="$1" ;;
"-conddesc") shift; CONDDESC="$1" ;;
"-appid") shift; APPID="$1" ;;
"-appname")shift; APPNAME="$1" ;;
"-hostname")shift; HOSTNAME="$1" ;;
esac
shift
done

_SCS_DATA="$(printf '{"timestamp": "%s", "epoch": "%s", "msgid": "%s", "msgtext": "%s", "condid": "%s", "condname": "%s", "conddesc": "%s", "appid": "%s", "appname": "%s", "hostname": "%s"}' "${_NOW}" "${_EPOCH}" "${MSGID}" "${MSGTEXT}" "${CONDID}" "${CONDNAME}" "${CONDDESC}" "${APPID}" "${APPNAME}" "${HOSTNAME}")"

# debug
echo -e "$(printf '{"timestamp":"%s", "epoch":"%s", "message":%s}' "${_NOW}" "${_EPOCH}" "${_SCS_DATA}")" >> ${_LOGFILE} 2>&1

# send json alarm data to API endpoint
_API_RESULT=$(curl --write-out %{http_code} --silent --output /dev/null -X POST -H 'Content-type: application/json' --data "${_SCS_DATA}" ${_URL})

# store API Endpoint result
_CURL_RC="$(printf '{"curl_result_code":"%s"}' ${_API_RESULT})"

# debug
echo -e "$(printf '{"timestamp":"%s", "epoch":"%s", "message":%s}' "${_NOW}" "${_EPOCH}" "${_CURL_RC}")" >> ${_LOGFILE} 2>&1
