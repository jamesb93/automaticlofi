setinletassist(0,  '(String) Control In')
setoutletassist(0, 'Info Out')

function getcwd(){
    f = new File(this.patcher.filepath);
    outlet(0, f.foldername);
    return f.foldername;
}

function getfilename(){
    f = new File(this.patcher.filepath);
    outlet(0, f.filename);
    return f.filename;
}

function getrelative(list){
    // The first argument must be the queried path, then either '-' to move up, or a folder/file name.

    pathArray = arguments[0].split('/');

    for(i=1;i<arguments.length;i++){
        if(arguments[i] == '-')
            pathArray.pop();
        else
            pathArray.push(arguments[i]);
    }

    path = '';
    for(i=0;i<pathArray.length;i++){
        path = path + pathArray[i];
        if(i != pathArray.length-1)
            path = path + '/'
    }

    outlet(0, path);
    return path;
}

function getrelativefromcwd(list){
    // Either '-' to move up, or a folder/file name.

    f = new File(this.patcher.filepath);
    pathArray = f.foldername.split('/');

    for(i=0;i<arguments.length;i++){
        if(arguments[i] == '-')
            pathArray.pop();
        else
            pathArray.push(arguments[i]);
    }

    path = '';
    for(i=0;i<pathArray.length;i++){
        path = path + pathArray[i];
        if(i != pathArray.length-1)
            path = path + '/'
    }

    outlet(0, path);
    return path;
}

function getrelativefromcwd_withoutroot(list){
    // Either '-' to move up, or a folder/file name.

    f = new File(this.patcher.filepath);
    pathArray = f.foldername.split('/');

    for(i=0;i<arguments.length;i++){
        if(arguments[i] == '-')
            pathArray.pop();
        else
            pathArray.push(arguments[i]);
    }

    path = '/';
    for(i=1;i<pathArray.length;i++){
        path = path + pathArray[i];
        if(i != pathArray.length-1)
            path = path + '/'
    }

    outlet(0, path);
    return path;
}