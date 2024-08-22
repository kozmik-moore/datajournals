function setTime(obj_id){
    document.getElementById(obj_id).value = getLocalTime();
}

function setDate(obj_id){
    document.getElementById(obj_id).value = getLocalDate();
}

function setDatetime(obj_id){
    document.getElementById(obj_id).value = getLocalDatetime();
}

function getLocalTime(date) {
    if (date === undefined || date === null){
        var date = new Date();
    }
    date.setMilliseconds(0);
    date.setSeconds(0);
    var date_str = String(date.getHours()).padStart(2, '0') + ":" + String(date.getMinutes()).padStart(2, '0');
    return date_str;
}

function getLocalDate(date) {
    if (date === undefined || date === null){
        var date = new Date();
    }
    date.setMilliseconds(0);
    date.setSeconds(0);
    var datestring = date.getFullYear() + "-" + 
        String(date.getMonth() + 1).padStart(2, '0') + "-" + 
        String(date.getDate()).padStart(2, '0');
    return datestring;
}

function getLocalDatetime(){
    var date = new Date();
    return getLocalDate(date) + 'T' + getLocalTime(date);
}

function resetDatetime(obj_id){
    document.getElementById(obj_id).value = null
}